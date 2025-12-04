# bot/handlers/payment.py
# --- ОБНОВЛЕН: 2025-12-04 12:15 - Исправлены отступы уведомлений о платежах ---

import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.utils.keyboard import InlineKeyboardBuilder
from database.db import db
from keyboards.inline import get_payment_check_keyboard, get_payment_keyboard, get_main_menu_keyboard
from utils.texts import PAYMENT_CREATED, PAYMENT_SUCCESS_TEXT, PAYMENT_ERROR_TEXT, MAIN_MENU_TEXT
from services.payment_api import create_payment_yookassa, find_payment
from utils.helpers import add_balance_to_text

logger = logging.getLogger(__name__)
router = Router()

@router.callback_query(F.data == "buy_generations")
async def show_packages(callback: CallbackQuery):
    """Показать пакеты генераций с возвратом к главному меню"""
    text = "Выберите пакет генераций:"
    text = await add_balance_to_text(text, callback.from_user.id)
    await callback.message.edit_text(
        text,
        reply_markup=get_payment_keyboard()
    )
    await callback.answer()

@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery, admins: list[int]):
    """Возврат к главному меню из экрана оплаты"""
    text = await add_balance_to_text(MAIN_MENU_TEXT, callback.from_user.id)
    await callback.message.edit_text(
        text,
        reply_markup=get_main_menu_keyboard(is_admin=callback.from_user.id in admins)
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
        payment_id=payment_data['id'],
        user_id=user_id,
        amount=payment_data['amount'],
        tokens=payment_data['tokens']
    )
    text = PAYMENT_CREATED.format(
        amount=amount,
        tokens=tokens_amount
    )
    text = await add_balance_to_text(text, user_id)
    await callback.message.edit_text(
        text,
        reply_markup=get_payment_check_keyboard(payment_data['confirmation_url'])
    )
    await callback.answer()


async def _process_referral_commission(user_id: int, payment_id: str, amount: int, tokens: int):
    """
    Начисление реферальной комиссии при успешной оплате.
    """
    try:
        # 1. Проверяем включена ли реферальная программа
        enabled = await db.get_setting('referral_enabled')
        if str(enabled) != '1':
            return
        
        # 2. Находим реферера
        user_data = await db.get_user_data(user_id)
        if not user_data:
            return
        
        referrer_id = user_data.get('referred_by')
        if not referrer_id:
            logger.debug(f"Пользователь {user_id} не имеет реферера")
            return
        
        # 3. Рассчитываем комиссию
        commission_percent = int(await db.get_setting('referral_commission_percent') or '10')
        earnings = int(amount * commission_percent / 100)
        
        logger.info(f"[REFERRAL] Расчет: {amount} руб * {commission_percent}% = {earnings} руб")
        
        # 4. Начисляем рубли на реферальный баланс
        await db.add_referral_balance(referrer_id, earnings)
        logger.info(f"[REFERRAL] Начислено {earnings} руб на реф. баланс реферера {referrer_id}")
        
        # 5. Конвертируем в генерации и начисляем на основной баланс
        exchange_rate = int(await db.get_setting('referral_exchange_rate') or '29')
        tokens_to_give = earnings // exchange_rate
        
        logger.info(f"[REFERRAL] Конвертация: {earnings} руб = {tokens_to_give} генераций")
        
        if tokens_to_give > 0:
            await db.add_tokens(referrer_id, tokens_to_give)
            logger.info(f"[REFERRAL] Начислено {tokens_to_give} генераций рефереру {referrer_id}")
        
        # 6. Логируем операцию
        await db.log_referral_earning(
            referrer_id=referrer_id,
            referred_id=user_id,
            payment_id=payment_id,
            amount=amount,
            commission_percent=commission_percent,
            earnings=earnings,
            tokens=tokens_to_give
        )
        logger.info(f"[REFERRAL] ✅ Запись в referral_earnings создана")
        
    except Exception as e:
        logger.error(f"[REFERRAL] Ошибка обработки реферальной комиссии: {e}")


@router.callback_query(F.data == "check_payment")
async def check_payment(callback: CallbackQuery, admins: list[int]):
    """Проверить статус платежа + возврат к главному меню"""
    user_id = callback.from_user.id
    last_payment = await db.get_last_pending_payment(user_id)
    if not last_payment:
        await callback.answer("Нет активных платежей для проверки.", show_alert=True)
        return
    
    is_paid = find_payment(last_payment['yookassa_payment_id'])
    if is_paid:
        # 1. Обновляем статус платежа
        await db.set_payment_success(last_payment['yookassa_payment_id'])
        
        # 2. Начисляем токены покупателю
        await db.add_tokens(user_id, last_payment['tokens'])
        
        # 3. Начисляем реферальную комиссию (если есть реферер)
        await _process_referral_commission(
            user_id=user_id,
            payment_id=last_payment['yookassa_payment_id'],
            amount=last_payment['amount'],
            tokens=last_payment['tokens']
        )
        
        # 4. Уведомление админов о новой оплате
        try:
            from loader import bot
            admins_to_notify = await db.get_admins_for_notification("notify_new_payments")
            for admin_id in admins_to_notify:
                try:
                    await bot.send_message(
                        admin_id,
                        f"💳 Новая оплата: пользователь `{user_id}`, сумма: {last_payment['amount']} руб., токенов: {last_payment['tokens']}",
                        parse_mode="Markdown"
                    )
                except Exception as e:
                    logger.error(f"Не удалось отправить уведомление о платеже админу {admin_id}: {e}")
        except Exception as e:
            logger.error(f"Ошибка при отправке уведомлений о платеже: {e}")
        
        # 5. Показываем успех
        balance = await db.get_balance(user_id)
        text = PAYMENT_SUCCESS_TEXT.format(balance=balance)
        text = await add_balance_to_text(text, user_id)
        await callback.message.edit_text(
            text,
            reply_markup=get_main_menu_keyboard(is_admin=user_id in admins)
        )
    else:
        await callback.answer(PAYMENT_ERROR_TEXT, show_alert=True)


@router.callback_query(F.data == "show_profile")
async def show_profile_payment(callback: CallbackQuery):
    # Этот хэндлер больше не нужен, так как основной в user_start.py
    # Но оставляем для обратной совместимости
    from handlers.user_start import show_profile as main_show_profile
    await main_show_profile(callback, None)  # state не используется в основном
    await callback.answer()
