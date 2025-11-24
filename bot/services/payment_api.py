# payment_api

import os
import logging
from yookassa import Configuration, Payment
from datetime import datetime

# Загружаем переменные окружения
load_dotenv()
SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")

logger = logging.getLogger(__name__)

# Настраиваем ЮKassa
Configuration.account_id = SHOP_ID
Configuration.secret_key = SECRET_KEY


def create_payment_yookassa(amount: int, user_id: int, tokens: int,
                            description: str = "Покупка токенов") -> dict | None:
    """
    Создаёт РЕАЛЬНЫЙ платёж через ЮKassa.

    Args:
        amount: Сумма в копейках (100 = 1 рубль)
        user_id: ID пользователя в боте
        tokens: Количество токенов для зачисления
        description: Описание платежа

    Returns:
        Словарь с данными платежа или None если ошибка
    """
    try:
        # Создаём платёж через ЮKassa
        payment = Payment.create({
            "amount": {
                "value": str(amount / 100),  # Преобразуем копейки в рубли
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": "https://yoursite.com/success"  # Где юзер вернётся после оплаты
            },
            "capture": True,  # Автоматически подтверждать платежи
            "description": description,
            "metadata": {
                "user_id": str(user_id),
                "tokens": str(tokens)
            }
        })

        # Возвращаем информацию о платеже
        return {
            'id': payment.id,
            'amount': amount,
            'tokens': tokens,
            'confirmation_url': payment.confirmation.confirmation_url,
            'status': payment.status
        }

    except Exception as e:
        logger.error(f"Ошибка при создании платежа: {e}")
        return None


def find_payment(payment_id: str) -> dict | None:
    """
    Проверяет статус платежа в ЮKassa.

    Args:
        payment_id: ID платежа от ЮKassa

    Returns:
        Словарь с информацией о платеже или None
    """
    try:
        payment = Payment.find_one(payment_id)

        return {
            'id': payment.id,
            'status': payment.status,  # 'succeeded', 'pending', 'canceled'
            'amount': int(payment.amount.value * 100),  # В копейках
            'metadata': payment.metadata if hasattr(payment, 'metadata') else {}
        }

    except Exception as e:
        logger.error(f"Ошибка при проверке платежа {payment_id}: {e}")
        return None


def is_payment_successful(payment_id: str) -> bool:
    """Проверяет, успешен ли платёж"""
    payment = find_payment(payment_id)
    if payment:
        return payment['status'] == 'succeeded'
    return False
