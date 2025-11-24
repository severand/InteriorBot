#

from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from dotenv import load_dotenv
from database.db import db
from keyboards.inline import get_payment_check_keyboard, get_payment_keyboard, get_main_menu_keyboard
from utils.texts import PAYMENT_CREATED, PAYMENT_SUCCESS_TEXT, PAYMENT_ERROR_TEXT, MAIN_MENU_TEXT
from services.payment_api import create_payment_yookassa, find_payment

router = Router()

@router.callback_query(F.data == "buy_generations")
async def show_packages(callback: CallbackQuery):
    """Показать пакеты генераций с возвратом к главному меню"""
    await callback.message.edit_text(
        "Выберите пакет генераций:",
        reply_markup=get_payment_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery):
    """Возврат к главному меню из экрана оплаты"""
    await callback.message.edit_text(
        MAIN_MENU_TEXT,
        reply_markup=get_main_menu_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data.startswith("pay_"))
async def create_payment(callback: CallbackQuery):
    """Создать платеж в ЮКассе"""
    # Парсим данные из кнопки (pay_10_290) -> tokens=10, price=290
    _, tokens, price = callback.data.split("_")
    user_id = callback.from_user.id
    amount = int(price)
    tokens_amount = int(tokens)
    payment_data = create_payment_yookassa(amount, user_id, tokens_amount)
    if not payment_data:
        await callback.answer("Ошибка создания платежа", show_alert=True)
        return
    await db.create_payment(
        user_id=user_id,
        payment_id=payment_data['id'],
        amount=payment_data['amount'],
        tokens=payment_data['tokens']
    )
    await callback.message.edit_text(
        PAYMENT_CREATED.format(
            amount=amount,
            tokens=tokens_amount
        ),
        reply_markup=get_payment_check_keyboard(payment_data['confirmation_url'])
    )
    await callback.answer()

@router.callback_query(F.data == "check_payment")
async def check_payment(callback: CallbackQuery):
    """Проверить статус платежа + возврат к главному меню"""
    user_id = callback.from_user.id
    last_payment = await db.get_last_pending_payment(user_id)
    if not last_payment:
        await callback.answer("Нет активных платежей для проверки.", show_alert=True)
        return
    is_paid = find_payment(last_payment['yookassa_payment_id'])
    if is_paid:
        await db.set_payment_success(last_payment['yookassa_payment_id'])
        await db.add_tokens(user_id, last_payment['tokens'])
        await callback.message.edit_text(
            PAYMENT_SUCCESS_TEXT.format(balance=await db.get_balance(user_id)),
            reply_markup=get_main_menu_keyboard()
        )
    else:
        await callback.answer(PAYMENT_ERROR_TEXT, show_alert=True)

@router.callback_query(F.data == "show_profile")
async def show_profile_payment(callback: CallbackQuery):
    from keyboards.inline import get_profile_keyboard
    from utils.texts import PROFILE_TEXT
    user_id = callback.from_user.id
    balance = await db.get_balance(user_id)
    username = callback.from_user.username or "Не указано"
    await callback.message.edit_text(
        PROFILE_TEXT.format(
            user_id=user_id,
            username=username,
            balance=balance,
            reg_date="Недавно"
        ),
        reply_markup=get_profile_keyboard()
    )
    await callback.answer()
