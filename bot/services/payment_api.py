import os
import uuid
from dotenv import load_dotenv

# Загружаем переменные окружения (хотя они фейковые, но код их ждет)
load_dotenv()
SHOP_ID = os.getenv("YOOKASSA_SHOP_ID")
SECRET_KEY = os.getenv("YOOKASSA_SECRET_KEY")


# --- ФЕЙКОВЫЕ ФУНКЦИИ ДЛЯ ЗАПУСКА И ТЕСТИРОВАНИЯ ---
# ВНИМАНИЕ: Если ты захочешь принимать реальные платежи, этот код нужно 
# заменить на реальную интеграцию с библиотекой yookassa (YooKassa.create_payment).

def create_payment_yookassa(amount: int, user_id: int, tokens: int) -> dict | None:
    """
    [ЗАГЛУШКА] Имитирует создание платежа ЮKassa.
    В реальной жизни здесь используется API Yookassa.
    """
    try:
        # Генерируем фейковый ID платежа и ссылку для перехода
        fake_payment_id = str(uuid.uuid4())
        fake_confirmation_url = f"https://example.com/pay/{fake_payment_id}"

        return {
            'id': fake_payment_id,
            'amount': amount,
            'tokens': tokens,
            'confirmation_url': fake_confirmation_url
        }
    except Exception as e:
        print(f"Ошибка в фейковом создании платежа: {e}")
        return None


def find_payment(payment_id: str) -> bool:
    """
    [ЗАГЛУШКА] Имитирует проверку статуса платежа.
    В реальной жизни здесь используется API Yookassa для получения статуса.
    """
    # Для теста мы просто делаем вид, что платеж всегда успешен.
    # Это позволит тебе проверить логику зачисления токенов в БД.
    return True

    # --- КОНЕЦ ФЕЙКОВЫХ ФУНКЦИЙ ---