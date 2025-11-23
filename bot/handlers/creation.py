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
    get_profile_keyboard
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

logger = logging.getLogger(__name__)
router = Router()

# --- Универсальная функция нового меню с обновлением ID ---
async def safe_show_menu(sender, state: FSMContext, text: str, keyboard, parse_mode: str = "Markdown"):
    try:
        msg = await sender.edit_text(text, reply_markup=keyboard, parse_mode=parse_mode)
    except Exception:
        msg = await sender.answer(text, reply_markup=keyboard, parse_mode=parse_mode)
    await state.update_data(menu_message_id=msg.message_id)
    return msg

# --- Везде дальше применение safe_show_menu ---

@router.callback_query(F.data == "main_menu")
async def go_to_main_menu(callback: CallbackQuery, state: FSMContext):
    await safe_show_menu(callback.message, state, "🏠 Главное меню!\n\nВыберите действие ниже:", get_profile_keyboard())
    await state.clear()
    await callback.answer()

@router.callback_query(F.data == "create_design")
async def choose_new_photo(callback: CallbackQuery, state: FSMContext):
    await state.clear()
    await state.set_state(CreationStates.waiting_for_photo)
    await safe_show_menu(callback.message, state, UPLOAD_PHOTO_TEXT, None)
    await callback.answer()

@router.message(CreationStates.waiting_for_photo, F.photo)
async def photo_uploaded(message: Message, state: FSMContext, admins: list[int]):
    user_id = message.from_user.id

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
    if user_id not in admins:
        balance = await db.get_balance(user_id)
        if balance <= 0:
            await state.clear()
            await safe_show_menu(message, state, NO_BALANCE_TEXT, get_payment_keyboard())
            return
    await state.update_data(photo_id=photo_file_id)
    await state.set_state(CreationStates.choose_room)
    await safe_show_menu(message, state, PHOTO_SAVED_TEXT, get_room_keyboard())

@router.callback_query(CreationStates.choose_room, F.data.startswith("room_"))
async def room_chosen(callback: CallbackQuery, state: FSMContext, admins: list[int]):
    room = callback.data.split("_")[-1]
    user_id = callback.from_user.id
    if user_id not in admins:
        balance = await db.get_balance(user_id)
        if balance <= 0:
            await state.clear()
            await safe_show_menu(callback.message, state, NO_BALANCE_TEXT, get_payment_keyboard())
            return
    await state.update_data(room=room)
    await state.set_state(CreationStates.choose_style)
    await safe_show_menu(callback.message, state, CHOOSE_STYLE_TEXT, get_style_keyboard())
    await callback.answer()

@router.callback_query(CreationStates.choose_style, F.data == "back_to_room")
async def back_to_room_selection(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CreationStates.choose_room)
    await safe_show_menu(callback.message, state, PHOTO_SAVED_TEXT, get_room_keyboard())
    await callback.answer()

@router.callback_query(CreationStates.choose_style, F.data.startswith("style_"))
async def style_chosen(callback: CallbackQuery, state: FSMContext, admins: list[int], bot_token: str):
    style = callback.data.split("_")[-1]
    user_id = callback.from_user.id
    if user_id not in admins:
        balance = await db.get_balance(user_id)
        if balance <= 0:
            await state.clear()
            await safe_show_menu(callback.message, state, NO_BALANCE_TEXT, get_payment_keyboard())
            return
    data = await state.get_data()
    photo_id = data.get('photo_id')
    room = data.get('room')
    if user_id not in admins:
        await db.decrease_balance(user_id)
    loading_msg = await safe_show_menu(callback.message, state, "⏳ Генерирую новый дизайн...", None)
    await callback.answer()
    result_image_url = await generate_image(photo_id, room, style, bot_token)
    try:
        await loading_msg.delete()
    except Exception:
        pass
    if result_image_url:
        msg = await callback.message.answer_photo(
            photo=result_image_url,
            caption=f"Ваш новый дизайн в стиле *{style.replace('_', ' ').title()}*!",
            reply_markup=get_post_generation_keyboard()
        )
        await state.update_data(menu_message_id=msg.message_id)
    else:
        await safe_show_menu(callback.message, state, "Ошибка генерации. Попробуйте еще раз.", get_profile_keyboard())

@router.callback_query(F.data == "change_style")
async def change_style_after_gen(callback: CallbackQuery, state: FSMContext):
    await state.set_state(CreationStates.choose_style)
    await safe_show_menu(callback.message, state, CHOOSE_STYLE_TEXT, get_style_keyboard())
    await callback.answer()

@router.callback_query(F.data == "show_profile")
async def show_profile_handler(callback: CallbackQuery, state: FSMContext):
    user_id = callback.from_user.id
    balance = await db.get_balance(user_id)
    username = callback.from_user.username or "Не указано"
    text = PROFILE_TEXT.format(
        user_id=user_id,
        username=username,
        balance=balance,
        reg_date="Недавно"
    )
    await safe_show_menu(callback.message, state, text, get_profile_keyboard())
    await callback.answer()

@router.message(CreationStates.waiting_for_photo)
async def invalid_photo(message: Message):
    try:
        await message.delete()
    except:
        pass

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
