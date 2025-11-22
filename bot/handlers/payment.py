from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder

# Импортируем наши модули (из-за отсутствия этих строк у тебя было красное)
from database.db import db
from keyboards.inline import get_payment_check_keyboard, get_payment_keyboard
from utils.texts import PAYMENT_CREATED
from services.payment_api import create_payment_yookassa, find_payment

router = Router()


@router.callback_query(F.data == "buy_generations")
async def show_packages(callback: CallbackQuery):
    """Показать пакеты генераций"""
    await callback.message.edit_text(
        "Выберите пакет генераций:",
        reply_markup=get_payment_keyboard()
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

    # Создаем платеж через сервис
    payment_data = create_payment_yookassa(amount, user_id, tokens_amount)

    if not payment_data:
        await callback.answer("Ошибка создания платежа", show_alert=True)
        return

    # Сохраняем в БД
    await db.create_payment(
        user_id=user_id,
        payment_id=payment_data['id'],
        amount=payment_data['amount'],
        tokens=payment_data['tokens']
    )

    # Отправляем ссылку
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
    """Проверить статус платежа"""
    user_id = callback.from_user.id

    # Ищем последний pending платеж пользователя
    last_payment = await db.get_last_pending_payment(user_id)

    if not last_payment:
        await callback.answer("Нет активных платежей для проверки.", show_alert=True)
        return

    # Проверяем в ЮКассе
    is_paid = find_payment(last_payment['yookassa_payment_id'])

    if is_paid:
        # Начисляем токены
        await db.set_payment_success(last_payment['yookassa_payment_id'])
        await db.add_tokens(user_id, last_payment['tokens'])

        await callback.message.edit_text(
            f"✅ Оплата прошла успешно!\nВам начислено {last_payment['tokens']} генераций.",
            reply_markup=None  # Или вернуть кнопку в меню
        )
    else:
        await callback.answer("Оплата пока не поступила. Попробуйте через минуту.", show_alert=True)