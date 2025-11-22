# --- ИСПРАВЛЕНИЯ ВЕРСИИ: bot/handlers/creation.py ---
# [2025-11-22 10:30 CET] Исправление: Добавлена блокировка отправки альбомов (проверка message.media_group_id).
# [2025-11-22 10:30 CET] Исправление: Добавлена проверка 'photo_id' в change_style_after_gen для предотвращения ошибок без фото.
# [2025-11-22 11:00 CET] Исправление: Добавлено кэширование media_group_id для отправки предупреждения об альбоме только ОДИН раз.
# [2025-11-22 11:15 CET] Исправление: Блокировка всех сообщений, кроме кнопок, в состоянии choose_room. Добавлен хэндлер кнопки "Загрузить новое фото".
# [2025-11-22 11:40 CET] Исправление: Внедрена гарантированная блокировка новых фото/текста в choose_room. Добавлено подробное логирование (logger.debug) для отладки приоритетов хэндлеров.
# [2025-11-22 11:45 CET] Критическое исправление: Консолидация блокировки сообщений в choose_room в один Catch-All хэндлер и добавление сброса состояния при попытке отправить фото/текст, чтобы принудительно вернуть пользователя в начало потока (waiting_for_photo).
# [2025-11-22 15:01 MSK] КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Упрощена логика блокировки сообщений, убраны счетчики спама, добавлено корректное удаление сообщений с обработкой ошибок.
# [2025-11-22 15:12 MSK] НОВОЕ ИСПРАВЛЕНИЕ: Добавлен глобальный блокировщик фото ВНЕ состояния waiting_for_photo. Теперь фото можно загружать ТОЛЬКО после нажатия "Создать дизайн".
# ---

import asyncio
import logging

from aiogram import Router, F
from aiogram.enums import ParseMode
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.exceptions import TelegramBadRequest

# Импорты наших модулей
from database.db import db
from keyboards.inline import get_room_keyboard, get_style_keyboard, get_payment_keyboard, get_post_generation_keyboard
from services.replicate_api import generate_image
from states.fsm import CreationStates
from utils.texts import CHOOSE_STYLE_TEXT, PHOTO_SAVED_TEXT, NO_BALANCE_TEXT, TOO_MANY_PHOTOS_TEXT, UPLOAD_PHOTO_TEXT

# Инициализация логгера
logger = logging.getLogger(__name__)

router = Router()


# =========================================================================
# 0. ГЛОБАЛЬНАЯ БЛОКИРОВКА ФОТО ВНЕ ПРОЦЕССА СОЗДАНИЯ
# =========================================================================

@router.message(F.photo)
async def block_unexpected_photos(message: Message, state: FSMContext):
    """
    КРИТИЧЕСКИЙ БЛОКИРОВЩИК: Если пользователь НЕ в состоянии waiting_for_photo,
    любые фото блокируются и удаляются.
    """
    current_state = await state.get_state()

    # Проверяем: находится ли пользователь в правильном состоянии
    if current_state != CreationStates.waiting_for_photo:
        logger.debug(
            f"🚫 БЛОКИРОВКА: Попытка загрузить фото вне процесса создания. "
            f"User: {message.from_user.id}, State: {current_state}"
        )

        # Удаляем нежелательное фото
        try:
            await message.delete()
            logger.debug(f"✅ Неожиданное фото удалено. Msg ID: {message.message_id}")
        except TelegramBadRequest as e:
            logger.warning(f"❌ Не удалось удалить фото: {e}")
        except Exception as e:
            logger.error(f"❌ Ошибка удаления фото: {e}")

        # Отправляем предупреждение
        warning_msg = await message.answer(
            "🚫 Для загрузки фото сначала выберите пункт *'Создать дизайн'* в меню!",
            parse_mode=ParseMode.MARKDOWN
        )

        # Автоудаление предупреждения через 5 секунд
        await asyncio.sleep(5)
        try:
            await warning_msg.delete()
        except Exception:
            pass

        return  # Прерываем дальнейшую обработку


# =========================================================================
# 1. ОБРАБОТКА ФОТО (ТОЛЬКО В СОСТОЯНИИ waiting_for_photo)
# =========================================================================

@router.message(CreationStates.waiting_for_photo, F.photo)
async def photo_uploaded(message: Message, state: FSMContext, admins: list[int]):
    """
    Сохраняет фото в состояние и предлагает выбрать комнату.
    Блокирует отправку альбомов.
    """
    logger.debug(f"Хэндлер photo_uploaded сработал. ID пользователя: {message.from_user.id}")
    user_id = message.from_user.id

    # БЛОКИРОВКА АЛЬБОМОВ С КЭШИРОВАНИЕМ
    if message.media_group_id:
        data = await state.get_data()
        cached_group_id = data.get('media_group_id')

        if cached_group_id == message.media_group_id:
            logger.debug(f"Игнорирование повторного сообщения альбома: {message.media_group_id}")
            return

        await state.update_data(media_group_id=message.media_group_id)
        await message.answer(TOO_MANY_PHOTOS_TEXT)
        logger.debug(f"Отправлено предупреждение об альбоме: {message.media_group_id}")
        return

    await state.update_data(media_group_id=None)

    photo_file_id = message.photo[-1].file_id

    # ПРОВЕРКА АДМИНА: пропускаем проверку баланса, если админ
    if user_id not in admins:
        balance = await db.get_balance(user_id)

        if balance <= 0:
            logger.info(f"Пользователь {user_id} исчерпал баланс.")
            await state.clear()
            await message.answer(
                NO_BALANCE_TEXT,
                reply_markup=get_payment_keyboard()
            )
            return

    await state.update_data(photo_id=photo_file_id)
    await state.set_state(CreationStates.choose_room)
    logger.debug(f"Состояние изменено на choose_room. Отправка меню выбора комнаты.")

    await message.answer(
        PHOTO_SAVED_TEXT,
        reply_markup=get_room_keyboard()
    )


@router.message(CreationStates.waiting_for_photo)
async def invalid_photo(message: Message):
    """Обрабатывает невалидный ввод вместо фото"""
    logger.debug(f"Хэндлер invalid_photo сработал. Пользователь отправил не фото в ожидании фото.")
    await message.answer("Пожалуйста, отправьте фотографию комнаты.")


# =========================================================================
# 2. ВЫБОР КОМНАТЫ
# =========================================================================

@router.callback_query(CreationStates.choose_room, F.data == "create_design")
async def choose_new_photo(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает нажатие на кнопку 'Загрузить новое фото' и переводит в состояние ожидания фото.
    """
    logger.debug("Хэндлер choose_new_photo сработал. Переход в waiting_for_photo.")

    current_data = await state.get_data()
    photo_id = current_data.get('photo_id')
    await state.clear()

    if photo_id:
        await state.update_data(photo_id=photo_id)

    await state.set_state(CreationStates.waiting_for_photo)
    await callback.message.edit_text(UPLOAD_PHOTO_TEXT)
    await callback.answer()


@router.callback_query(CreationStates.choose_room, F.data.startswith("room_"))
async def room_chosen(callback: CallbackQuery, state: FSMContext, admins: list[int]):
    """Обрабатывает выбор типа комнаты и предлагает выбрать стиль"""
    logger.debug(f"Хэндлер room_chosen сработал. Выбрана комната: {callback.data.split('_')[-1]}")

    room = callback.data.split("_")[-1]
    user_id = callback.from_user.id

    # ПРОВЕРЯЕМ БАЛАНС ТОЛЬКО, ЕСЛИ ПОЛЬЗОВАТЕЛЬ НЕ АДМИН
    if user_id not in admins:
        balance = await db.get_balance(user_id)

        if balance <= 0:
            logger.info(f"Пользователь {user_id} исчерпал баланс при выборе комнаты.")
            await state.clear()
            await callback.message.edit_text(
                NO_BALANCE_TEXT,
                reply_markup=get_payment_keyboard()
            )
            return

    await state.update_data(room=room)
    await state.set_state(CreationStates.choose_style)
    logger.debug("Состояние изменено на choose_style. Отправка меню выбора стиля.")

    await callback.message.edit_text(
        CHOOSE_STYLE_TEXT,
        reply_markup=get_style_keyboard()
    )
    await callback.answer()


# КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Блокировка всех сообщений в choose_room
@router.message(CreationStates.choose_room)
async def block_messages_in_choose_room(message: Message, state: FSMContext):
    """
    Блокирует любое сообщение в состоянии choose_room.
    УДАЛЯЕТ сообщение и сбрасывает состояние.
    """
    logger.debug(
        f"🚫 Блокировка сообщения в choose_room. "
        f"User: {message.from_user.id}, Msg ID: {message.message_id}"
    )

    # УДАЛЯЕМ нежелательное сообщение
    try:
        await message.delete()
        logger.debug(f"✅ Сообщение {message.message_id} удалено")
    except TelegramBadRequest as e:
        logger.warning(f"❌ Не удалось удалить сообщение: {e}")
    except Exception as e:
        logger.error(f"❌ Ошибка удаления сообщения: {e}")

    # СБРОС СОСТОЯНИЯ
    await state.clear()
    await state.set_state(CreationStates.waiting_for_photo)

    # ОТПРАВКА ПРЕДУПРЕЖДЕНИЯ
    try:
        warning_msg = await message.answer(
            "🚫 Пожалуйста, используйте только кнопки меню!\n\n"
            "Загрузите новую фотографию для начала.",
            parse_mode=ParseMode.MARKDOWN
        )

        logger.debug(f"📨 Предупреждение отправлено. ID: {warning_msg.message_id}")

        # АВТОУДАЛЕНИЕ через 5 секунд
        await asyncio.sleep(5)
        try:
            await warning_msg.delete()
            logger.debug(f"🗑 Предупреждение удалено")
        except Exception:
            pass

    except Exception as e:
        logger.error(f"Ошибка отправки предупреждения: {e}")


# =========================================================================
# 3. ВЫБОР СТИЛЯ И ГЕНЕРАЦИЯ
# =========================================================================

@router.callback_query(CreationStates.choose_style, F.data.startswith("style_"))
async def style_chosen(callback: CallbackQuery, state: FSMContext, admins: list[int], bot_token: str):
    """Обрабатывает выбор стиля, генерирует изображение и уменьшает баланс"""
    logger.debug(f"Хэндлер style_chosen сработал. Выбран стиль: {callback.data.split('_')[-1]}")

    style = callback.data.split("_")[-1]
    user_id = callback.from_user.id

    # Проверяем баланс (финальная проверка, только если не админ)
    if user_id not in admins:
        balance = await db.get_balance(user_id)
        if balance <= 0:
            logger.info(f"Пользователь {user_id} исчерпал баланс перед генерацией.")
            await state.clear()
            await callback.message.edit_text(
                NO_BALANCE_TEXT,
                reply_markup=get_payment_keyboard()
            )
            return

    # Получаем все данные для генерации
    data = await state.get_data()
    photo_id = data.get('photo_id')
    room = data.get('room')

    # Уменьшаем баланс (Только если пользователь НЕ админ)
    if user_id not in admins:
        await db.decrease_balance(user_id)
        logger.info(f"Баланс пользователя {user_id} уменьшен на 1.")

    # Сообщаем о начале генерации
    await callback.message.edit_text("⏳ Генерирую новый дизайн... Это может занять до 30 секунд.")
    await callback.answer()

    # Генерируем изображение через API Replicate
    result_image_url = await generate_image(photo_id, room, style, bot_token)
    logger.debug(f"Генерация завершена. Результат URL: {result_image_url}")

    if result_image_url:
        await callback.message.answer_photo(
            photo=result_image_url,
            caption=f"Ваш новый дизайн в стиле *{style.replace('_', ' ').title()}*!",
            reply_markup=get_post_generation_keyboard()
        )
    else:
        logger.error("Ошибка при генерации изображения через API Replicate.")
        await callback.message.answer("К сожалению, произошла ошибка генерации. Попробуйте еще раз.")


# =========================================================================
# 4. ОБРАБОТКА ПОСТ-ГЕНЕРАЦИОННЫХ КНОПОК
# =========================================================================

@router.callback_query(F.data == "change_style")
async def change_style_after_gen(callback: CallbackQuery, state: FSMContext):
    """
    Позволяет пользователю выбрать другой стиль для уже загруженной фотографии.
    """
    logger.debug("Хэндлер change_style_after_gen сработал.")

    data = await state.get_data()
    if 'photo_id' not in data:
        logger.warning("Попытка сменить стиль без загруженного фото. Сброс состояния.")
        await state.set_state(CreationStates.waiting_for_photo)
        await callback.answer("⚠️ Сначала загрузите фотографию!", show_alert=True)
        await callback.message.edit_text(UPLOAD_PHOTO_TEXT)
        return

    await state.set_state(CreationStates.choose_style)
    logger.debug("Состояние изменено на choose_style. Отправка меню выбора стиля.")

    await callback.message.edit_text(
        CHOOSE_STYLE_TEXT,
        reply_markup=get_style_keyboard()
    )
    await callback.answer()
