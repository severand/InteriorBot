# --- ИСПРАВЛЕНИЯ ВЕРСИИ: bot/handlers/creation.py ---
# [2025-11-22 17:09 MSK] КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ:
# - Исправлена блокировка документов (включая Word, PDF и т.д.)
# - Изменено время автоудаления предупреждений с 5 на 3 секунды
# - Упрощён текст предупреждений до "Пожалуйста, используйте только кнопки меню!"
# - Исправлена логика удаления предупреждений для альбомов
# - Убрано сообщение "Пожалуйста, отправьте фотографию комнаты" — теперь просто игнорирование
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
# 1. ОБРАБОТКА ФОТО (ТОЛЬКО В СОСТОЯНИИ waiting_for_photo)
# ВАЖНО: Этот хэндлер ДОЛЖЕН быть ПЕРЕД глобальным блокировщиком!
# =========================================================================

@router.message(CreationStates.waiting_for_photo, F.photo)
async def photo_uploaded(message: Message, state: FSMContext, admins: list[int]):
    """
    Сохраняет фото в состояние и предлагает выбрать комнату.
    Блокирует отправку альбомов и УДАЛЯЕТ все фотографии из альбома.
    """
    logger.debug(f"✅ Хэндлер photo_uploaded сработал. ID пользователя: {message.from_user.id}")
    user_id = message.from_user.id

    # БЛОКИРОВКА АЛЬБОМОВ С УДАЛЕНИЕМ ВСЕХ ФОТОГРАФИЙ
    if message.media_group_id:
        data = await state.get_data()
        cached_group_id = data.get('media_group_id')

        # УДАЛЯЕМ ВСЕ фотографии из альбома
        try:
            await message.delete()
            logger.debug(f"🗑 Удалено фото из альбома. Msg ID: {message.message_id}")
        except Exception as e:
            logger.warning(f"❌ Не удалось удалить фото из альбома: {e}")

        # Если это первое фото из альбома - отправляем предупреждение
        if cached_group_id != message.media_group_id:
            await state.update_data(media_group_id=message.media_group_id)
            warning_msg = await message.answer(TOO_MANY_PHOTOS_TEXT)
            logger.debug(f"📨 Отправлено предупреждение об альбоме: {message.media_group_id}")

            # Автоудаление предупреждения через 3 секунды
            await asyncio.sleep(3)
            try:
                await warning_msg.delete()
                logger.debug(f"🗑 Предупреждение об альбоме удалено")
            except Exception:
                pass
        else:
            logger.debug(f"Игнорирование повторного сообщения альбома: {message.media_group_id}")

        return

    # Сбрасываем media_group_id если это одиночное фото
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
    logger.debug(f"✅ Состояние изменено на choose_room. Отправка меню выбора комнаты.")

    await message.answer(
        PHOTO_SAVED_TEXT,
        reply_markup=get_room_keyboard()
    )


@router.message(CreationStates.waiting_for_photo)
async def invalid_photo(message: Message):
    """
    Обрабатывает невалидный ввод вместо фото.
    Теперь просто удаляет сообщение без предупреждения.
    """
    logger.debug(f"Хэндлер invalid_photo сработал. Удаление невалидного сообщения.")
    try:
        await message.delete()
    except Exception:
        pass


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
            "🚫 Пожалуйста, используйте только кнопки меню!",
            parse_mode=ParseMode.MARKDOWN
        )

        logger.debug(f"📨 Предупреждение отправлено. ID: {warning_msg.message_id}")

        # АВТОУДАЛЕНИЕ через 3 секунды
        await asyncio.sleep(3)
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


# =========================================================================
# 5. ГЛОБАЛЬНАЯ БЛОКИРОВКА ВСЕХ ТИПОВ МЕДИА (КРОМЕ ФОТО)
# ВАЖНО: Эти хэндлеры ДОЛЖНЫ быть ПЕРЕД блокировщиком фото!
# =========================================================================

@router.message(F.video | F.video_note)
async def block_video(message: Message):
    """Блокирует видео и видеосообщения"""
    logger.debug(f"🚫 БЛОКИРОВКА ВИДЕО: User {message.from_user.id}")
    try:
        await message.delete()
        logger.debug(f"✅ Видео удалено. Msg ID: {message.message_id}")
    except Exception as e:
        logger.warning(f"❌ Не удалось удалить видео: {e}")


@router.message(F.document)
async def block_documents(message: Message):
    """Блокирует ВСЕ документы (Word, PDF, Excel и т.д.)"""
    logger.debug(f"🚫 БЛОКИРОВКА ДОКУМЕНТА: User {message.from_user.id}")
    try:
        await message.delete()
        logger.debug(f"✅ Документ удалён. Msg ID: {message.message_id}")
    except Exception as e:
        logger.warning(f"❌ Не удалось удалить документ: {e}")


@router.message(F.sticker)
async def block_stickers(message: Message):
    """Блокирует стикеры"""
    logger.debug(f"🚫 БЛОКИРОВКА СТИКЕРА: User {message.from_user.id}")
    try:
        await message.delete()
        logger.debug(f"✅ Стикер удалён. Msg ID: {message.message_id}")
    except Exception as e:
        logger.warning(f"❌ Не удалось удалить стикер: {e}")


@router.message(F.audio | F.voice)
async def block_audio(message: Message):
    """Блокирует аудио и голосовые"""
    logger.debug(f"🚫 БЛОКИРОВКА АУДИО: User {message.from_user.id}")
    try:
        await message.delete()
        logger.debug(f"✅ Аудио удалено. Msg ID: {message.message_id}")
    except Exception as e:
        logger.warning(f"❌ Не удалось удалить аудио: {e}")


@router.message(F.animation)
async def block_animation(message: Message):
    """Блокирует GIF-анимации"""
    logger.debug(f"🚫 БЛОКИРОВКА GIF: User {message.from_user.id}")
    try:
        await message.delete()
        logger.debug(f"✅ GIF удалён. Msg ID: {message.message_id}")
    except Exception as e:
        logger.warning(f"❌ Не удалось удалить GIF: {e}")


# =========================================================================
# 6. ГЛОБАЛЬНАЯ БЛОКИРОВКА ФОТО ВНЕ ПРОЦЕССА СОЗДАНИЯ
# ВАЖНО: Этот хэндлер ДОЛЖЕН быть ПОСЛЕ блокировщиков других медиа!
# =========================================================================

@router.message(F.photo)
async def block_unexpected_photos(message: Message, state: FSMContext):
    """
    КРИТИЧЕСКИЙ БЛОКИРОВЩИК: Если пользователь НЕ в состоянии waiting_for_photo,
    любые фото блокируются и удаляются.
    Этот хэндлер срабатывает только если фото не было обработано выше.
    """
    current_state = await state.get_state()

    logger.debug(
        f"🚫 ГЛОБАЛЬНАЯ БЛОКИРОВКА ФОТО: Попытка загрузить фото вне процесса создания. "
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
        "🚫 Пожалуйста, используйте только кнопки меню!",
        parse_mode=ParseMode.MARKDOWN
    )

    # Автоудаление предупреждения через 3 секунды
    await asyncio.sleep(3)
    try:
        await warning_msg.delete()
    except Exception:
        pass


# =========================================================================
# 7. ГЛОБАЛЬНАЯ БЛОКИРОВКА ВСЕХ ТЕКСТОВЫХ СООБЩЕНИЙ
# ВАЖНО: Этот хэндлер ДОЛЖЕН быть В САМОМ КОНЦЕ как catch-all!
# =========================================================================

@router.message(F.text)
async def block_all_text_messages(message: Message):
    """
    ГЛОБАЛЬНЫЙ БЛОКИРОВЩИК ТЕКСТА: Удаляет любые текстовые сообщения от пользователя.
    Срабатывает только если сообщение не было обработано другими хэндлерами выше.
    """
    logger.debug(
        f"🚫 ГЛОБАЛЬНАЯ БЛОКИРОВКА ТЕКСТА: Попытка отправить текст. "
        f"User: {message.from_user.id}, Text: {message.text[:50]}..."
    )

    # УДАЛЯЕМ текстовое сообщение БЕЗ предупреждения
    try:
        await message.delete()
        logger.debug(f"✅ Текстовое сообщение удалено. Msg ID: {message.message_id}")
    except TelegramBadRequest as e:
        logger.warning(f"❌ Не удалось удалить текст: {e}")
    except Exception as e:
        logger.error(f"❌ Ошибка удаления текста: {e}")
