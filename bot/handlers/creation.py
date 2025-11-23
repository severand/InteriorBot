# --- ФИНАЛЬНАЯ ВЕРСИЯ: bot/handlers/creation.py -----
import asyncio
import logging

from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.exceptions import TelegramBadRequest

# Импорты наших модулей
from database.db import db
from keyboards.inline import (
    get_room_keyboard,
    get_style_keyboard,
    get_payment_keyboard,
    get_post_generation_keyboard,
    get_profile_keyboard # <--- Добавлен get_profile_keyboard
)
from services.replicate_api import generate_image
from states.fsm import CreationStates
from utils.texts import (
    CHOOSE_STYLE_TEXT,
    PHOTO_SAVED_TEXT,
    NO_BALANCE_TEXT,
    TOO_MANY_PHOTOS_TEXT,
    UPLOAD_PHOTO_TEXT,
    PROFILE_TEXT
)

# Инициализация логгера
logger = logging.getLogger(__name__)

router = Router()


# =========================================================================
# 1. ГЛОБАЛЬНЫЕ КНОПКИ (ПОСЛЕ ГЕНЕРАЦИИ)
# =========================================================================

@router.callback_query(F.data == "create_design")
async def choose_new_photo(callback: CallbackQuery, state: FSMContext):
    """
    Кнопка 'Загрузить новое/другое фото'.
    Убирает кнопки у старого сообщения, сбрасывает состояние и просит фото.
    ВАЖНО: ИЗОБРАЖЕНИЕ НЕ УДАЛЯЕТСЯ.
    """
    logger.debug("🔄 Нажата кнопка 'Загрузить новое фото'.")

    # 1. Убираем кнопки у сообщения с изображением (изображение остается)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    await state.clear()
    await state.set_state(CreationStates.waiting_for_photo)

    # 2. Отправляем НОВОЕ сообщение с просьбой загрузить фото
    await callback.message.answer(UPLOAD_PHOTO_TEXT)
    await callback.answer()


@router.callback_query(F.data == "show_profile")
async def show_profile_handler(callback: CallbackQuery, state: FSMContext):
    """
    Кнопка 'Перейти в профиль'.
    Сгенерированная картинка и ее кнопки ОСТАЮТСЯ. Показ профиля новым сообщением с новым меню.
    """
    logger.debug("👤 Нажата кнопка 'Профиль'.")

    # Кнопки у старого сообщения НЕ УДАЛЯЕМ (согласно требованию)

    await state.clear()

    user_id = callback.from_user.id
    balance = await db.get_balance(user_id)
    username = callback.from_user.username or "Не указано"

    text = PROFILE_TEXT.format(
        user_id=user_id,
        username=username,
        balance=balance,
        reg_date="Недавно"
    )

    # Отправляем профиль новым сообщением
    await callback.message.answer(text, reply_markup=get_profile_keyboard(), parse_mode=ParseMode.MARKDOWN) # <--- ИСПОЛЬЗУЕМ НОВОЕ МЕНЮ
    await callback.answer()


@router.callback_query(F.data == "change_style")
async def change_style_after_gen(callback: CallbackQuery, state: FSMContext):
    """
    Кнопка 'Показать новый стиль' (после генерации).
    Убирает кнопки у фото с результатом и присылает меню стилей.
    """
    logger.debug("🎨 Нажата кнопка 'Показать новый стиль'.")

    data = await state.get_data()

    if 'photo_id' not in data:
        logger.warning("Нет photo_id. Сброс.")
        try:
            await callback.message.edit_reply_markup(reply_markup=None)
        except:
            pass
        await state.set_state(CreationStates.waiting_for_photo)
        await callback.answer("⚠️ Сессия истекла. Загрузите фото.", show_alert=True)
        await callback.message.answer(UPLOAD_PHOTO_TEXT)
        return

    # Удаляем кнопки у сообщения с результатом (картинка остается)
    try:
        await callback.message.edit_reply_markup(reply_markup=None)
    except Exception:
        pass

    await state.set_state(CreationStates.choose_style)

    # Отправляем меню стилей НОВЫМ сообщением
    await callback.message.answer(CHOOSE_STYLE_TEXT, reply_markup=get_style_keyboard())
    await callback.answer()


# =========================================================================
# 2. ОБРАБОТКА ФОТО (waiting_for_photo)
# =========================================================================

@router.message(CreationStates.waiting_for_photo, F.photo)
async def photo_uploaded(message: Message, state: FSMContext, admins: list[int]):
    """Загрузка фото."""
    logger.debug(f"✅ Фото получено. User: {message.from_user.id}")
    user_id = message.from_user.id

    # Блокировка альбомов
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
            except:
                pass
        return

    await state.update_data(media_group_id=None)
    photo_file_id = message.photo[-1].file_id

    # Проверка баланса
    if user_id not in admins:
        balance = await db.get_balance(user_id)
        if balance <= 0:
            await state.clear()
            await message.answer(NO_BALANCE_TEXT, reply_markup=get_payment_keyboard())
            return

    await state.update_data(photo_id=photo_file_id)
    await state.set_state(CreationStates.choose_room)
    await message.answer(PHOTO_SAVED_TEXT, reply_markup=get_room_keyboard())


@router.message(CreationStates.waiting_for_photo)
async def invalid_photo(message: Message):
    try:
        await message.delete()
    except:
        pass


# =========================================================================
# 3. ВЫБОР КОМНАТЫ
# =========================================================================

@router.callback_query(CreationStates.choose_room, F.data.startswith("room_"))
async def room_chosen(callback: CallbackQuery, state: FSMContext, admins: list[int]):
    """Выбор комнаты."""
    logger.debug(f"🛋 Комната выбрана: {callback.data}")
    room = callback.data.split("_")[-1]
    user_id = callback.from_user.id

    if user_id not in admins:
        balance = await db.get_balance(user_id)
        if balance <= 0:
            await state.clear()
            await callback.message.edit_text(NO_BALANCE_TEXT, reply_markup=get_payment_keyboard())
            return

    await state.update_data(room=room)
    await state.set_state(CreationStates.choose_style)
    await callback.message.edit_text(CHOOSE_STYLE_TEXT, reply_markup=get_style_keyboard())
    await callback.answer()


# Блокировка сообщений в choose_room
@router.message(CreationStates.choose_room)
async def block_messages_in_choose_room(message: Message, state: FSMContext):
    try:
        await message.delete()
    except:
        pass
    await state.clear()
    await state.set_state(CreationStates.waiting_for_photo)

    msg = await message.answer("🚫 Используйте кнопки! Начните заново, отправив фото.", parse_mode=ParseMode.MARKDOWN)
    await asyncio.sleep(3)
    try:
        await msg.delete()
    except:
        pass


# =========================================================================
# 4. ВЫБОР СТИЛЯ И ГЕНЕРАЦИЯ
# =========================================================================

@router.callback_query(CreationStates.choose_style, F.data == "back_to_room")
async def back_to_room_selection(callback: CallbackQuery, state: FSMContext):
    """Кнопка НАЗАД."""
    logger.debug("🔙 Назад к комнатам.")
    await state.set_state(CreationStates.choose_room)
    await callback.message.edit_text(PHOTO_SAVED_TEXT, reply_markup=get_room_keyboard())
    await callback.answer()


@router.callback_query(CreationStates.choose_style, F.data.startswith("style_"))
async def style_chosen(callback: CallbackQuery, state: FSMContext, admins: list[int], bot_token: str):
    """Генерация."""
    logger.debug(f"🎨 Стиль выбран: {callback.data}")
    style = callback.data.split("_")[-1]
    user_id = callback.from_user.id

    if user_id not in admins:
        balance = await db.get_balance(user_id)
        if balance <= 0:
            await state.clear()
            await callback.message.edit_text(NO_BALANCE_TEXT, reply_markup=get_payment_keyboard())
            return

    data = await state.get_data()
    photo_id = data.get('photo_id')
    room = data.get('room')

    if user_id not in admins:
        await db.decrease_balance(user_id)

    # Отправляем сообщение о генерации
    loading_msg = await callback.message.edit_text("⏳ Генерирую новый дизайн... Это может занять до 30 секунд.")
    await callback.answer()

    result_image_url = await generate_image(photo_id, room, style, bot_token)

    # УДАЛЯЕМ сообщение "Генерирую..." перед отправкой фото, чтобы не было мусора
    try:
        await loading_msg.delete()
    except Exception:
        pass

    if result_image_url:
        await callback.message.answer_photo(
            photo=result_image_url,
            caption=f"Ваш новый дизайн в стиле *{style.replace('_', ' ').title()}*!",
            reply_markup=get_post_generation_keyboard()
        )
    else:
        await callback.message.answer("Ошибка генерации. Попробуйте еще раз.")


# =========================================================================
# 5. ГЛОБАЛЬНЫЕ БЛОКИРОВЩИКИ (ЗАЩИТА ОТ СПАМА)
# =========================================================================

@router.message(F.video | F.video_note | F.document | F.sticker | F.audio | F.voice | F.animation)
async def block_media_types(message: Message):
    try:
        await message.delete()
    except:
        pass


@router.message(F.photo)
async def block_unexpected_photos(message: Message, state: FSMContext):
    try:
        await message.delete()
    except:
        pass
    msg = await message.answer("🚫 Используйте кнопки меню!")
    await asyncio.sleep(3)
    try:
        await msg.delete()
    except:
        pass


@router.message(F.text)
async def block_all_text_messages(message: Message):
    try:
        await message.delete()
    except:
        pass

    #  python bot/main.py
