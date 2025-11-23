# --- ИСПРАВЛЕНИЕ: bot/handlers/user_start.py -----
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

# Импорты наших модулей
from database.db import db
from states.fsm import CreationStates
from keyboards.inline import get_main_menu_keyboard, get_profile_keyboard # <--- Добавлен get_profile_keyboard
from utils.texts import START_TEXT, PROFILE_TEXT, UPLOAD_PHOTO_TEXT

router = Router()


@router.message(F.text == "/start")
async def cmd_start(message: Message, state: FSMContext):
    """
    Обрабатывает команду /start.
    Создает пользователя в базе данных (если его нет) и показывает главное меню.
    """
    await state.clear()

    user_id = message.from_user.id
    username = message.from_user.username

    # Создаем пользователя. Если он уже есть, функция вернет False (что нормально).
    await db.create_user(user_id, username)

    await message.answer(
        START_TEXT,
        reply_markup=get_main_menu_keyboard()
    )


@router.callback_query(F.data == "show_profile")
async def show_profile(callback: CallbackQuery):
    """
    Показывает профиль пользователя (баланс, дата регистрации).
    Пытается отредактировать текущее сообщение, чтобы избежать дублирования.
    Использует get_profile_keyboard.
    """
    user_id = callback.from_user.id

    # Получаем данные пользователя из БД
    user_data = await db.get_user_data(user_id)

    if user_data:
        balance = user_data.get('balance', 0)
        reg_date = user_data.get('reg_date', 'Неизвестно')
        username = user_data.get('username', 'Не указан')

        profile_text = PROFILE_TEXT.format(
            user_id=user_id,
            username=username,
            balance=balance,
            reg_date=reg_date
        )

        try:
            # Пытаемся отредактировать сообщение с кнопкой
            await callback.message.edit_text(
                profile_text,
                reply_markup=get_profile_keyboard() # <--- ИСПОЛЬЗУЕМ НОВОЕ МЕНЮ
            )
        except TelegramBadRequest:
            # Если не смогли отредактировать (например, из-за медиа-контента), отправляем новое сообщение
            await callback.message.answer(
                profile_text,
                reply_markup=get_profile_keyboard() # <--- ИСПОЛЬЗУЕМ НОВОЕ МЕНЮ
            )
    else:
        await callback.answer("Профиль не найден.", show_alert=True)

    await callback.answer()


@router.callback_query(F.data == "main_menu")
async def go_to_main_menu(callback: CallbackQuery, state: FSMContext):
    """
    Возвращает пользователя в главное меню (Создать дизайн, Профиль) из Профиля.
    """
    await state.clear()

    try:
        # Редактируем текущее сообщение (сообщение профиля) на приветственное
        await callback.message.edit_text(
            START_TEXT,
            reply_markup=get_main_menu_keyboard()
        )
    except TelegramBadRequest:
        # Если не удалось отредактировать, отправляем новое
        await callback.message.answer(
            START_TEXT,
            reply_markup=get_main_menu_keyboard()
        )

    await callback.answer()


@router.callback_query(F.data == "buy_generations")
async def buy_generations_handler(callback: CallbackQuery):
    """
    Обрабатывает нажатие кнопки 'Купить генерации' в профиле.
    """
    # Здесь можно добавить логику для перехода к оплате (get_payment_keyboard)
    await callback.answer("🛍️ Переход к оплате временно недоступен.", show_alert=True)


@router.callback_query(F.data == "create_design")
async def start_creation(callback: CallbackQuery, state: FSMContext):
    """
    Начинает процесс создания дизайна, переводит в состояние ожидания фото.
    Надежно редактирует или отправляет новое сообщение.
    """
    await state.set_state(CreationStates.waiting_for_photo)

    try:
        # Пытаемся отредактировать сообщение с кнопкой
        await callback.message.edit_text(
            UPLOAD_PHOTO_TEXT,
            reply_markup=None  # Убираем кнопки меню
        )
    except TelegramBadRequest:
        # Если не удалось отредактировать (например, это было фото),
        # удаляем старое сообщение и отправляем новое.
        try:
            await callback.message.delete()
        except:
            pass  # Игнорируем ошибки удаления

        await callback.message.answer(
            UPLOAD_PHOTO_TEXT,
            reply_markup=None
        )

    await callback.answer()