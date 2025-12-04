# bot/services/payment_api.py
# --- ОБНОВЛЕН: 2025-12-04 13:25 - Добавлено предупреждение о тестовой заглушке ---

# ⚠️⚠️⚠️ КРИТИЧЕСКОЕ ПРЕДУПРЕЖДЕНИЕ ⚠️⚠️⚠️
# ============================================
# ЭТО ТЕСТОВАЯ ЗАГЛУШКА (MOCK) ДЛЯ РАЗРАБОТКИ!
# ============================================
#
# ❌ НЕ ИСПОЛЬЗОВАТЬ В ПРОДАКШЕНЕ!
# ❌ ВСЕ ПЛАТЕЖИ АВТОМАТИЧЕСКИ "УСПЕШНЫ" БЕЗ РЕАЛЬНОЙ ОПЛАТЫ!
# ❌ ДЕНЬГИ НЕ СПИСЫВАЮТСЯ И НЕ ПРИХОДЯТ!
#
# ✅ ДЛЯ ПРОДАКШЕНА:
# Заменить этот файл на реальную интеграцию с YooKassa API
# Документация: https://yookassa.ru/developers/api
# Установить: pip install yookassa
#
# Пример реальной интеграции см. в конце этого файла (закомментирован)
# ============================================

import os
import logging
from dotenv import load_dotenv
import uuid

load_dotenv()
logger = logging.getLogger(__name__)


def create_payment_yookassa(amount: int, user_id: int, tokens: int,
                            description: str = "Покупка токенов") -> dict | None:
    """
    ⚠️ ТЕСТОВАЯ ВЕРСИЯ - создаёт фейковый платёж!
    
    В продакшене заменить на реальный вызов YooKassa API.
    
    Args:
        amount: Сумма в рублях
        user_id: ID пользователя
        tokens: Количество генераций
        description: Описание платежа
    
    Returns:
        dict: Данные о платеже (ФЕЙКОВЫЕ!)
    """
    try:
        payment_id = str(uuid.uuid4())
        logger.info(f"[ТЕСТ] Платёж {payment_id} для юзера {user_id}")
        logger.warning("⚠️ ИСПОЛЬЗУЕТСЯ ТЕСТОВАЯ ЗАГЛУШКА! Реальный платёж НЕ создан!")

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
    """
    ⚠️ ТЕСТОВАЯ ВЕРСИЯ - всегда возвращает "успешный" статус!
    
    В продакшене заменить на реальный вызов YooKassa API.
    
    Args:
        payment_id: ID платежа
    
    Returns:
        dict: Статус платежа (ВСЕГДА succeeded!)
    """
    try:
        logger.info(f"[ТЕСТ] Проверка платежа {payment_id}")
        logger.warning("⚠️ ТЕСТОВАЯ ЗАГЛУШКА: платёж автоматически помечен как успешный!")

        return {
            'id': payment_id,
            'status': 'succeeded',  # ⚠️ ВСЕГДА УСПЕШНО!
            'amount': 10000,
            'metadata': {}
        }
    except Exception as e:
        logger.error(f"Ошибка: {e}")
        return None


def is_payment_successful(payment_id: str) -> bool:
    """
    ⚠️ ТЕСТОВАЯ ВЕРСИЯ - всегда возвращает True!
    
    В продакшене заменить на реальную проверку статуса.
    
    Args:
        payment_id: ID платежа
    
    Returns:
        bool: ВСЕГДА True (тестовая заглушка!)
    """
    logger.warning("⚠️ ТЕСТОВАЯ ЗАГЛУШКА: is_payment_successful всегда возвращает True!")
    return True


# ============================================
# ПРИМЕР РЕАЛЬНОЙ ИНТЕГРАЦИИ ДЛЯ ПРОДАКШЕНА:
# ============================================
#
# from yookassa import Payment, Configuration
#
# # Настройка YooKassa (в config.py или .env)
# Configuration.account_id = os.getenv('YOOKASSA_SHOP_ID')
# Configuration.secret_key = os.getenv('YOOKASSA_SECRET_KEY')
#
#
# def create_payment_yookassa(amount: int, user_id: int, tokens: int,
#                             description: str = "Покупка токенов") -> dict | None:
#     """Реальное создание платежа в YooKassa"""
#     try:
#         payment = Payment.create({
#             "amount": {
#                 "value": f"{amount}.00",
#                 "currency": "RUB"
#             },
#             "confirmation": {
#                 "type": "redirect",
#                 "return_url": "https://your-bot.com/payment/success"
#             },
#             "capture": True,
#             "description": description,
#             "metadata": {
#                 "user_id": str(user_id),
#                 "tokens": str(tokens)
#             }
#         })
#         
#         logger.info(f"✅ Платёж создан: {payment.id}")
#         
#         return {
#             'id': payment.id,
#             'amount': amount,
#             'tokens': tokens,
#             'confirmation_url': payment.confirmation.confirmation_url,
#             'status': payment.status
#         }
#     except Exception as e:
#         logger.error(f"Ошибка создания платежа YooKassa: {e}")
#         return None
#
#
# def find_payment(payment_id: str) -> dict | None:
#     """Реальная проверка статуса платежа"""
#     try:
#         payment = Payment.find_one(payment_id)
#         
#         return {
#             'id': payment.id,
#             'status': payment.status,
#             'amount': int(float(payment.amount.value)),
#             'metadata': payment.metadata
#         }
#     except Exception as e:
#         logger.error(f"Ошибка проверки платежа: {e}")
#         return None
#
#
# def is_payment_successful(payment_id: str) -> bool:
#     """Реальная проверка успешности платежа"""
#     try:
#         payment = Payment.find_one(payment_id)
#         return payment.status == "succeeded"
#     except Exception as e:
#         logger.error(f"Ошибка проверки статуса: {e}")
#         return False
#
# ============================================
# ИНСТРУКЦИЯ ПО ЗАМЕНЕ:
# ============================================
# 1. Установить библиотеку: pip install yookassa
# 2. Добавить в .env:
#    YOOKASSA_SHOP_ID=ваш_shop_id
#    YOOKASSA_SECRET_KEY=ваш_secret_key
# 3. Раскомментировать код выше
# 4. Удалить тестовые функции
# 5. Протестировать на тестовых платежах YooKassa
# ============================================