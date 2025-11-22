from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

# Импорты наших модулей
from database.db import db
from states.fsm import CreationStates
from keyboards.inline import get_main_menu_keyboard
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
    """
    user_id = callback.from_user.id

    # Получаем данные пользователя из БД
    user_data = await db.get_user_data(user_id)

    if user_data:
        balance = user_data['balance']
        reg_date = user_data['reg_date']  # Предполагаем, что date_created есть в user_data

        await callback.message.edit_text(
            PROFILE_TEXT.format(
                user_id=user_id,
                username=user_data.get('username', 'Не указан'),
                balance=balance,
                reg_date=reg_date
            ),
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await callback.answer("Профиль не найден.", show_alert=True)

    await callback.answer()


@router.callback_query(F.data == "create_design")
async def start_creation(callback: CallbackQuery, state: FSMContext):
    """
    Начинает процесс создания дизайна, переводит в состояние ожидания фото.
    """
    await state.set_state(CreationStates.waiting_for_photo)
    await callback.message.edit_text(
        UPLOAD_PHOTO_TEXT,
        reply_markup=None  # Убираем кнопки меню
    )
    await callback.answer()