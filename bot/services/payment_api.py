import os
import logging
from dotenv import load_dotenv
import uuid

load_dotenv()
logger = logging.getLogger(__name__)


def create_payment_yookassa(amount: int, user_id: int, tokens: int,
                            description: str = "Покупка токенов") -> dict | None:
    """Создаёт платёж (тестовая версия)"""
    try:
        payment_id = str(uuid.uuid4())
        logger.info(f"[ТЕСТ] Платёж {payment_id} для юзера {user_id}")

        return {
            'id': payment_id,
            'amount': amount,
            'tokens': tokens,
            'confirmation_url': f"https://yookassa.ru/checkout/test/{payment_id}",
            'status': 'pending'
        }
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return None


def find_payment(payment_id: str) -> dict | None:
    """Проверяет статус платежа"""
    try:
        logger.info(f"[ТЕСТ] Проверка платежа {payment_id}")

        return {
            'id': payment_id,
            'status': 'succeeded',
            'amount': 10000,
            'metadata': {}
        }
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return None


def is_payment_successful(payment_id: str) -> bool:
    """Успешен ли платёж?"""
    return True
