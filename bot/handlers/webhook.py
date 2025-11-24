# webhook

from aiogram import Router, Request
from aiogram.types import Update
from services.payment_api import find_payment
from database.db import db

router = Router()


@router.post("/webhook/yookassa")
async def yookassa_webhook(request: Request):
    """Обработчик webhook от YooKassa"""
    data = await request.json()

    # Парсим платеж
    payment_data = data.get('object', {})
    payment_id = payment_data.get('id')
    status = payment_data.get('status')
    metadata = payment_data.get('metadata', {})

    if status == 'succeeded':
        user_id = int(metadata.get('user_id'))
        tokens = int(metadata.get('tokens'))

        # Обновляем статус платежа
        await db.update_payment_status(payment_id, 'succeeded')

        # Добавляем токены юзеру
        await db.add_tokens(user_id, tokens)

    return {"status": "ok"}
