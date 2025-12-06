# creation.py
# --- ОБНОВЛЕН: 2025-12-06 (фиксы разметки Markdown/HTML, безопасные подписи) ---

import asyncio
import logging
import html

from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message, URLInputFile
from aiogram.exceptions import TelegramBadRequest

# Импортируем свои модули
from database.db import db
from keyboards.inline import (
    get_room_keyboard,
    get_style_keyboard,
    get_payment_keyboard,
    get_post_generation_keyboard,
    get_profile_keyboard,
    get_main_menu_keyboard,
    get_clear_space_confirm_keyboard,
    get_upload_photo_keyboard
)

from services.replicate_api import generate_image_auto, clear_space_image
from states.fsm import CreationStates
from utils.texts import (
    CHOOSE_STYLE_TEXT,
    PHOTO_SAVED_TEXT,
    NO_BALANCE_TEXT,
    TOO_MANY_PHOTOS_TEXT,
    UPLOAD_PHOTO_TEXT,
    PROFILE_TEXT,
    MAIN_MENU_TEXT
)
from utils.helpers import add_balance_to_text

logger = logging.getLogger(__name__)
router = Router()


async def show_single_menu(
    sender,
    state: FSMContext,
    text: str,
    keyboard,
    parse_mode: str = "Markdown",
    show_balance: bool = True
):
    """
    Отображает единое меню с автоматическим добавлением баланса.
    """
    # Добавляем баланс к тексту если нужно
    if show_balance and hasattr(sender, 'from_user'):
        user_id = sender.from_user.id
        text = await add_balance_to_text(text, user_id)

    data = await state.get_data()
    old_menu_id = data.get('menu_message_id')
    if old_menu_id:
        try:
            await sender.bot.edit_message_text(
                chat_id=sender.chat.id,
                message_id=old_menu_id,
                text=text,
                reply_markup=keyboard,
                parse_mode=parse_mode
            )
            await state.update_data(menu_message_id=old_menu_id)
            return old_menu_id
        except Exception:
            pass

    menu = await sender.answer(text, reply_markup=keyboard, parse_mode=parse_mode)
    await state.update_data(menu_message_id=menu.message_id)
    if old_menu_id and old_menu_id != menu.message_id:
        try:
            await sender.bot.delete_message(chat_id=sender.chat.id, message_id=old_menu_id)
        except Exception:
            pass
    return menu.message_id


# ===== ГЛАВНЫЙ МЕНЮ И СТАРТ =====
@router.callback_query(F.data == "main_menu")
async def go_to_main_menu(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    await db.log_activity(user_id, 'main_menu')

    await state.clear()
    await show_single_menu(callback.message, state, MAIN_MENU_TEXT, get_main_menu_keyboard())
    await callback.answer()


@router.callback_query(F.data == "create_design")
async def choose_new_photo(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    await db.log_activity(user_id, 'create_design')

    await state.clear()
    await state.set_state(CreationStates.waiting_for_photo)
    await show_single_menu(callback.message, state, UPLOAD_PHOTO_TEXT, get_upload_photo_keyboard())
    await callback.answer()


# ===== ХЭНДЛЕР ОБРАБОТКИ ФОТО =====
@router.message(CreationStates.waiting_for_photo, F.photo)
async def photo_uploaded(message: Message, state: FSMContext, admins: list[int]):
    user_id = message.from_user.id
    await db.log_activity(user_id, 'photo_upload')

    # Блок альбомов
    if message.media_group_id:
        data = await state.get_data()
        cached_group_id = data.get('media_group_id')
        try:
            await message.delete()
        except Exception:
            pass
        if cached_group_id != message.media_group_id:
            await state.update_data(media_group_id=message.media_group_id)
            msg = await message.answer(TOO_MANY_PHOTOS_TEXT)
            await asyncio.sleep(3)
            try:
                await msg.delete()
            except Exception:
                pass
        return

    await state.update_data(media_group_id=None)
    photo_file_id = message.photo[-1].file_id

    # Проверка баланса
    if user_id not in admins:
        balance = await db.get_balance(user_id)
        if balance <= 0:
            await state.clear()
            await show_single_menu(message, state, NO_BALANCE_TEXT, get_payment_keyboard())
            return

    # Сохраняем фото и переходим к выбору комнаты
    await state.update_data(photo_id=photo_file_id)
    await state.set_state(CreationStates.choose_room)

    # Удаляем старое меню "Отправь фото"
    data = await state.get_data()
    old_menu_id = data.get('menu_message_id')
    if old_menu_id:
        try:
            await message.bot.delete_message(
                chat_id=message.chat.id,
                message_id=old_menu_id
            )
        except Exception as e:
            logger.debug(f"Не удалось удалить старое меню: {e}")

    # Добавляем баланс к тексту
    text_with_balance = await add_balance_to_text(PHOTO_SAVED_TEXT, user_id)

    # Отправляем НОВОЕ сообщение под фото
    sent_msg = await message.answer(
        text=text_with_balance,
        reply_markup=get_room_keyboard(),
        parse_mode="Markdown"
    )

    # Сохраняем ID нового меню
    await state.update_data(menu_message_id=sent_msg.message_id)


# ===== ВЫБОР КОМНАТЫ =====
@router.callback_query(CreationStates.choose_room, F.data.startswith("room_"))
async def room_chosen(callback: CallbackQuery, state: FSMContext, admins: list[int]):
    room = callback.data.replace("room_", "", 1)
    user_id = callback.from_user.id

    await db.log_activity(user_id, f'room_{room}')

    if user_id not in admins:
        balance = await db.get_balance(user_id)
        if balance <= 0:
            await state.clear()
            await show_single_menu(callback.message, state, NO_BALANCE_TEXT, get_payment_keyboard())
            return

    await state.update_data(room=room)
    await state.set_state(CreationStates.choose_style)
    await show_single_menu(callback.message, state, CHOOSE_STYLE_TEXT, get_style_keyboard())
    await callback.answer()


# ===== ОЧИСТКА ПРОСТРАНСТВА =====
@router.callback_query(CreationStates.choose_room, F.data == "clear_space_confirm")
async def clear_space_confirm_handler(callback: CallbackQuery, state: FSMContext):
    text = (
        "⚠️ Подтверждение очистки\n\n"
        "Хотите очистить изображение, "
        "нажмите кнопку «Очистить».\n\n"
        "Если нет — вернитесь назад."
    )
    await show_single_menu(callback.message, state, text, get_clear_space_confirm_keyboard())
    await callback.answer()


@router.callback_query(CreationStates.choose_room, F.data == "clear_space_execute")
async def clear_space_execute_handler(callback: CallbackQuery, state: FSMContext, admins: list[int], bot_token: str):
    user_id = callback.from_user.id
    await db.log_activity(user_id, 'clear_space')

    if user_id not in admins:
        balance = await db.get_balance(user_id)
        if balance <= 0:
            await state.clear()
            await show_single_menu(callback.message, state, NO_BALANCE_TEXT, get_payment_keyboard())
            return

    data = await state.get_data()
    photo_id = data.get('photo_id')

    if not photo_id:
        await callback.answer("Ошибка: фото не найдено", show_alert=True)
        return

    if user_id not in admins:
        await db.decrease_balance(user_id)

    progress_msg_id = await show_single_menu(
        callback.message,
        state,
        "⏳ Очищаю пространство...",
        None,
        show_balance=False
    )
    await callback.answer()

    try:
        result_image_url = await clear_space_image(photo_id, bot_token)
        success = result_image_url is not None
    except Exception as e:
        logger.error(f"Критическая ошибка очистки пространства: {e}")
        result_image_url = None
        success = False

        # Уведомление админов о критической ошибке
        try:
            from loader import bot
            admins_to_notify = await db.get_admins_for_notification("notify_critical_errors")
            for admin_id in admins_to_notify:
                try:
                    await bot.send_message(
                        admin_id,
                        f"⚠️ Критическая ошибка очистки:\nПользователь: `{user_id}`\n\n{str(e)[:500]}",
                        parse_mode="Markdown"
                    )
                except Exception:
                    pass
        except Exception:
            pass

    await db.log_generation(
        user_id=user_id,
        room_type='clear_space',
        style_type='clear_space',
        operation_type='clear_space',
        success=success
    )

    if progress_msg_id:
        try:
            await callback.message.bot.delete_message(
                chat_id=callback.message.chat.id,
                message_id=progress_msg_id
            )
        except Exception as e:
            logger.debug(f"Не удалось удалить сообщение о прогрессе: {e}")

    if result_image_url:
        await callback.message.answer_photo(
            photo=result_image_url,
            caption="✨ Пространство очищено!",
            parse_mode="Markdown"
        )
        await state.set_state(CreationStates.choose_room)
        await show_single_menu(
            callback.message,
            state,
            PHOTO_SAVED_TEXT,
            get_room_keyboard()
        )
    else:
        await show_single_menu(
            callback.message,
            state,
            "Ошибка очистки. Попробуйте еще раз.",
            get_room_keyboard()
        )


@router.callback_query(CreationStates.choose_room, F.data == "clear_space_cancel")
async def clear_space_cancel_handler(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CreationStates.choose_room)
    await show_single_menu(callback.message, state, PHOTO_SAVED_TEXT, get_room_keyboard())
    await callback.answer()


# ===== ВЫБОР СТИЛЯ/ВАРИАНТА И ГЕНЕРАЦИЯ =====
@router.callback_query(CreationStates.choose_style, F.data == "back_to_room")
async def back_to_room_selection(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CreationStates.choose_room)
    await show_single_menu(callback.message, state, PHOTO_SAVED_TEXT, get_room_keyboard())
    await callback.answer()


@router.callback_query(CreationStates.choose_style, F.data.startswith("style_"))
async def style_chosen(callback: CallbackQuery, state: FSMContext, admins: list[int], bot_token: str):
    style = callback.data.split("_")[-1]
    user_id = callback.from_user.id
    await db.log_activity(user_id, f'style_{style}')

    if user_id not in admins:
        balance = await db.get_balance(user_id)
        if balance <= 0:
            await state.clear()
            await show_single_menu(callback.message, state, NO_BALANCE_TEXT, get_payment_keyboard())
            return

    data = await state.get_data()
    photo_id = data.get('photo_id')
    room = data.get('room')

    if user_id not in admins:
        await db.decrease_balance(user_id)

    progress_msg_id = await show_single_menu(
        callback.message,
        state,
        "⏳ Создаю новый дизайн...",
        None,
        show_balance=False
    )
    await callback.answer()

    try:
        result_image_url = await generate_image_auto(photo_id, room, style, bot_token)
        success = result_image_url is not None
    except Exception as e:
        logger.error(f"Критическая ошибка генерации: {e}")
        result_image_url = None
        success = False

        # Уведомление админов о критической ошибке
        try:
            from loader import bot
            admins_to_notify = await db.get_admins_for_notification("notify_critical_errors")
            for admin_id in admins_to_notify:
                try:
                    await bot.send_message(
                        admin_id,
                        (
                            f"⚠️ Критическая ошибка генерации:\n"
                            f"Пользователь: `{user_id}`\nКомната: {room}\nСтиль: {style}\n\n{str(e)[:500]}"
                        ),
                        parse_mode="Markdown"
                    )
                except Exception:
                    pass
        except Exception:
            pass

    await db.log_generation(
        user_id=user_id,
        room_type=room,
        style_type=style,
        operation_type='design',
        success=success
    )

    if progress_msg_id:
        try:
            await callback.message.bot.delete_message(
                chat_id=callback.message.chat.id,
                message_id=progress_msg_id
            )
        except Exception as e:
            logger.debug(f"Не удалось удалить сообщение о прогрессе: {e}")

    if result_image_url:
        try:
            # Безопасные строки для HTML
            room_name = html.escape(room.replace('_', ' ').title(), quote=True)
            style_name = html.escape(style.replace('_', ' ').title(), quote=True)

            caption = f"✨ Ваш новый дизайн {room_name} в стиле <b>{style_name}</b>!"

            await callback.message.answer_photo(
                photo=URLInputFile(result_image_url),
                caption=caption,
                parse_mode="HTML"
            )
        except Exception as e:
            logger.error(f"Ошибка при отправке фото: {e}")
            await show_single_menu(
                callback.message,
                state,
                "❌ Ошибка при отправке изображения. Попробуйте еще раз.",
                get_main_menu_keyboard()
            )
            return
# cообщение после генерации картинки
        await show_single_menu(
            callback.message,
            state,
            "",
            get_post_generation_keyboard()
        )
    else:
        await show_single_menu(
            callback.message,
            state,
            "Ошибка генерации. Попробуйте еще раз.",
            get_main_menu_keyboard()
        )


@router.callback_query(F.data == "change_style")
async def change_style_after_gen(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CreationStates.choose_style)
    await show_single_menu(callback.message, state, CHOOSE_STYLE_TEXT, get_style_keyboard())
    await callback.answer()


# ===== Блокировки ввода =====
@router.message(CreationStates.waiting_for_photo)
async def invalid_photo(message: Message):
    try:
        await message.delete()
    except Exception:
        pass


@router.message(CreationStates.choose_room)
async def block_messages_in_choose_room(message: Message, state: FSMContext):
    """
    Блокируем любые сообщения на экране выбора помещения.
    Не трогаем FSM и menu_message_id.
    """
    try:
        await message.delete()
    except Exception:
        pass

    msg = await message.answer(
        "🚫 Используйте кнопки!",
        parse_mode=ParseMode.MARKDOWN
    )
    await asyncio.sleep(3)
    try:
        await msg.delete()
    except Exception:
        pass


@router.message(F.video | F.video_note | F.document | F.sticker | F.audio | F.voice | F.animation)
async def block_media_types(message: Message):
    try:
        await message.delete()
    except Exception:
        pass


@router.message(F.photo)
async def block_unexpected_photos(message: Message, state: FSMContext):
    try:
        await message.delete()
    except Exception:
        pass
    msg = await message.answer("🚫 Используйте кнопки меню!")
    await asyncio.sleep(3)
    try:
        await msg.delete()
    except Exception:
        pass


@router.message(F.text)
async def block_all_text_messages(message: Message):
    try:
        await message.delete()
    except Exception:
        pass
