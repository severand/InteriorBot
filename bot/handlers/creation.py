from aiogram import Router, F
from aiogram.fsm.context import FSMContext
from aiogram.types import CallbackQuery, Message
from aiogram.enums import ParseMode

# Импорты наших модулей
from database.db import db
from states.fsm import CreationStates
from keyboards.inline import get_room_keyboard, get_style_keyboard, get_payment_keyboard, get_post_generation_keyboard
from services.replicate_api import generate_image  # <-- Импорт теперь работает
from utils.texts import CHOOSE_STYLE_TEXT, PHOTO_SAVED_TEXT, NO_BALANCE_TEXT

router = Router()


# =========================================================================
# 1. ОБРАБОТКА ФОТО
# =========================================================================

@router.message(CreationStates.waiting_for_photo, F.photo)
async def photo_uploaded(message: Message, state: FSMContext, admins: list[int]):
    """Сохраняет фото в состояние и предлагает выбрать комнату"""

    photo_file_id = message.photo[-1].file_id
    user_id = message.from_user.id

    # ----------------------------------------------------
    print(f"\n--- ПРОВЕРКА АДМИНА: ОБРАБОТКА ФОТО ---")
    print(f"User ID: {user_id}")
    print(f"Admin IDs: {admins}")
    print(f"User ID in Admins: {user_id in admins}")
    print(f"----------------------------------------\n")
    # ----------------------------------------------------

    # 1. ПРОВЕРКА АДМИНА: пропускаем проверку баланса, если админ
    if user_id not in admins:
        balance = await db.get_balance(user_id)

        if balance <= 0:
            await state.clear()
            await message.answer(
                NO_BALANCE_TEXT,
                reply_markup=get_payment_keyboard()
            )
            return

    await state.update_data(photo_id=photo_file_id)

    await state.set_state(CreationStates.choose_room)

    await message.answer(
        PHOTO_SAVED_TEXT,
        reply_markup=get_room_keyboard()
    )


@router.message(CreationStates.waiting_for_photo)
async def invalid_photo(message: Message):
    """Обрабатывает невалидный ввод вместо фото"""
    await message.answer("Пожалуйста, отправьте фотографию комнаты.")


# =========================================================================
# 2. ВЫБОР КОМНАТЫ
# =========================================================================

@router.callback_query(CreationStates.choose_room, F.data.startswith("room_"))
async def room_chosen(callback: CallbackQuery, state: FSMContext, admins: list[int]):
    """Обрабатывает выбор типа комнаты и предлагает выбрать стиль"""

    room = callback.data.split("_")[-1]
    user_id = callback.from_user.id

    # ----------------------------------------------------
    print(f"\n--- ПРОВЕРКА АДМИНА: ВЫБОР КОМНАТЫ ---")
    print(f"User ID: {user_id}")
    print(f"Admin IDs: {admins}")
    print(f"User ID in Admins: {user_id in admins}")
    print(f"---------------------------------------\n")
    # ----------------------------------------------------

    # ПРОВЕРЯЕМ БАЛАНС ТОЛЬКО, ЕСЛИ ПОЛЬЗОВАТЕЛЬ НЕ АДМИН
    if user_id not in admins:
        balance = await db.get_balance(user_id)

        if balance <= 0:
            await state.clear()
            await callback.message.edit_text(
                NO_BALANCE_TEXT,
                reply_markup=get_payment_keyboard()
            )
            return

    await state.update_data(room=room)

    await state.set_state(CreationStates.choose_style)

    await callback.message.edit_text(
        CHOOSE_STYLE_TEXT,
        reply_markup=get_style_keyboard()
    )
    await callback.answer()


# =========================================================================
# 3. ВЫБОР СТИЛЯ И ГЕНЕРАЦИЯ
# =========================================================================

@router.callback_query(CreationStates.choose_style, F.data.startswith("style_"))
# ДОБАВЛЕНО: bot_token: str
async def style_chosen(callback: CallbackQuery, state: FSMContext, admins: list[int], bot_token: str):
    """Обрабатывает выбор стиля, генерирует изображение и уменьшает баланс"""

    style = callback.data.split("_")[-1]
    user_id = callback.from_user.id

    # ----------------------------------------------------
    print(f"\n--- ПРОВЕРКА АДМИНА: ОБРАБОТКА СТИЛЯ ---")
    print(f"User ID: {user_id}")
    print(f"Admin IDs: {admins}")
    print(f"User ID in Admins: {user_id in admins}")
    print(f"----------------------------------------\n")
    # ----------------------------------------------------

    # 1. Проверяем баланс (финальная проверка, только если не админ)
    if user_id not in admins:
        balance = await db.get_balance(user_id)
        if balance <= 0:
            await state.clear()
            await callback.message.edit_text(
                NO_BALANCE_TEXT,
                reply_markup=get_payment_keyboard()
            )
            return

    # 2. Получаем все данные для генерации
    data = await state.get_data()
    photo_id = data.get('photo_id')
    room = data.get('room')

    # state.clear() удалено, чтобы сохранить данные для кнопки "Показать новый стиль"

    # 3. Уменьшаем баланс (Только если пользователь НЕ админ)
    if user_id not in admins:
        await db.decrease_balance(user_id)

    # 4. Сообщаем о начале генерации
    await callback.message.edit_text("⏳ Генерирую новый дизайн... Это может занять до 30 секунд.")
    await callback.answer()

    # 5. Генерируем изображение через API Replicate
    # ИСПРАВЛЕНИЕ: Передаем bot_token
    result_image_url = await generate_image(photo_id, room, style, bot_token)

    if result_image_url:
        # 6. Отправляем результат
        await callback.message.answer_photo(
            photo=result_image_url,
            caption=f"Ваш новый дизайн в стиле *{style.replace('_', ' ').title()}*!",
            # ИСПОЛЬЗУЕМ НОВУЮ КЛАВИАТУРУ
            reply_markup=get_post_generation_keyboard()
        )
    else:
        await callback.message.answer("К сожалению, произошла ошибка генерации. Попробуйте еще раз.")


# =========================================================================
# 4. ОБРАБОТКА ПОСТ-ГЕНЕРАЦИОННЫХ КНОПОК
# =========================================================================

@router.callback_query(F.data == "change_style")
async def change_style_after_gen(callback: CallbackQuery, state: FSMContext):
    """
    Позволяет пользователю выбрать другой стиль для уже загруженной фотографии.
    """
    # 1. Устанавливаем новое состояние
    await state.set_state(CreationStates.choose_style)

    # 2. Выводим клавиатуру стилей
    await callback.message.edit_text(
        CHOOSE_STYLE_TEXT,
        reply_markup=get_style_keyboard()
    )
    await callback.answer()