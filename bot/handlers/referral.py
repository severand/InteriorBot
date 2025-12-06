# bot/handlers/referral.py
"""Обработчики реферальной системы"""

import re
import logging
from aiogram import Router, F
from aiogram.types import CallbackQuery, Message
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from aiogram.types import InlineKeyboardMarkup

from database.db import db
from states.fsm import ReferralStates
from utils.navigation import edit_menu

logger = logging.getLogger(__name__)
router = Router()


# ===== ВСПОМОГАТЕЛЬНЫЕ ФУНКЦИИ =====

def format_number(num: int) -> str:
    """Форматирование числа с пробелами"""
    return f"{num:,}".replace(',', ' ')


def get_word_form(count: int, forms: tuple) -> str:
    """Получить правильную форму слова"""
    if count % 10 == 1 and count % 100 != 11:
        return forms[0]
    elif 2 <= count % 10 <= 4 and (count % 100 < 10 or count % 100 >= 20):
        return forms[1]
    else:
        return forms[2]


def validate_phone(phone: str) -> tuple[bool, str]:
    """Валидация и форматирование телефона"""
    phone = re.sub(r'[^\d+]', '', phone)
    if phone.startswith('8'):
        phone = '+7' + phone[1:]
    elif phone.startswith('7'):
        phone = '+' + phone
    if len(phone) != 12:
        return False, ""
    formatted = f"+7 ({phone[2:5]}) {phone[5:8]}-{phone[8:10]}-{phone[10:]}"
    return True, formatted


def mask_payment_details(method: str, details: str) -> str:
    """Маскирование реквизитов"""
    if method == 'card' and len(details) >= 16:
        return f"{details[:4]} **** **** {details[-4:]}"
    elif method == 'sbp' and len(details) >= 10:
        return f"+7 ({details[2:5]}) ***-**-{details[-2:]}"
    else:
        return details[:10] + '***' if len(details) > 10 else details


# ===== ОБМЕН НА ГЕНЕРАЦИИ =====

@router.callback_query(F.data == "referral_exchange_tokens")
async def exchange_to_tokens(callback: CallbackQuery, state: FSMContext):
    """Начало обмена реферального баланса на генерации"""
    user_id = callback.from_user.id
    balance = await db.get_referral_balance(user_id)
    exchange_rate = int(await db.get_setting('referral_exchange_rate') or '29')
    max_tokens = balance // exchange_rate

    if balance < exchange_rate:
        await callback.answer(f"⚠️ Недостаточно средств. Минимум: {exchange_rate} руб.", show_alert=True)
        return

    text = (
        f"💸 **ОБМЕН НА ГЕНЕРАЦИИ**\n\n"
        f"───────────────\n"
        f"💰 Доступно: **{format_number(balance)} руб.**\n"
        f"💱 Курс: {exchange_rate} руб/генерация\n"
        f"✨ Максимум: **{max_tokens}** генераций\n"
        f"───────────────\n\n"
        f"Введите количество генераций или `/all` для обмена всего:"
    )

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⏪ Назад в профиль", callback_data="show_profile"))

    await edit_menu(callback, state, text, builder.as_markup())
    await state.set_state(ReferralStates.entering_exchange_amount)
    await callback.answer()


@router.message(ReferralStates.entering_exchange_amount)
async def process_exchange_amount(message: Message, state: FSMContext):
    """Обработка количества генераций для обмена"""
    user_id = message.from_user.id

    try:
        await message.delete()
    except:
        pass

    balance = await db.get_referral_balance(user_id)
    exchange_rate = int(await db.get_setting('referral_exchange_rate') or '29')
    max_tokens = balance // exchange_rate

    if message.text == "/all":
        tokens = max_tokens
    else:
        try:
            tokens = int(message.text)
        except:
            await state.clear()
            data = await state.get_data()
            menu_message_id = data.get('menu_message_id')
            if menu_message_id:
                await state.update_data(menu_message_id=menu_message_id)
            return

    if tokens <= 0 or tokens > max_tokens:
        await state.clear()
        data = await state.get_data()
        menu_message_id = data.get('menu_message_id')
        if menu_message_id:
            await state.update_data(menu_message_id=menu_message_id)
        return

    cost = tokens * exchange_rate

    # Выполняем обмен
    await db.decrease_referral_balance(user_id, cost)
    await db.add_tokens(user_id, tokens)
    await db.log_referral_exchange(user_id, cost, tokens, exchange_rate)

    new_balance = await db.get_balance(user_id)

    text = (
        f"✅ **ОБМЕН ВЫПОЛНЕН!**\n\n"
        f"✨ Получено: **{tokens}** генераций\n"
        f"💸 Списано: {format_number(cost)} руб.\n"
        f"🎯 Новый баланс: **{new_balance}** генераций"
    )

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="👤 Профиль", callback_data="show_profile"))
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))

    data = await state.get_data()
    menu_message_id = data.get('menu_message_id')

    await state.clear()
    if menu_message_id:
        await state.update_data(menu_message_id=menu_message_id)

    try:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=menu_message_id,
            text=text,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
    except:
        pass


# ===== ВЫПЛАТА СРЕДСТВ =====

@router.callback_query(F.data == "referral_request_payout")
async def request_payout(callback: CallbackQuery, state: FSMContext):
    """Запрос на выплату"""
    user_id = callback.from_user.id
    balance = await db.get_referral_balance(user_id)
    min_payout = int(await db.get_setting('referral_min_payout') or '500')

    if balance < min_payout:
        await callback.answer(
            f"⚠️ Недостаточно средств.\nМинимальная сумма: {min_payout} руб.",
            show_alert=True
        )
        return

    payment_details = await db.get_payment_details(user_id)
    if not payment_details or not payment_details.get('payment_method'):
        await callback.answer("⚠️ Сначала укажите реквизиты", show_alert=True)
        return

    text = (
        f"💸 **ВЫВОД СРЕДСТВ**\n\n"
        f"💰 Доступно: **{format_number(balance)} руб.**\n"
        f"💵 Минимум: {format_number(min_payout)} руб.\n\n"
        f"Введите сумму или `/all` для вывода всего:"
    )

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⏪ Назад", callback_data="show_profile"))

    await edit_menu(callback, state, text, builder.as_markup())
    await state.set_state(ReferralStates.entering_payout_amount)
    await callback.answer()


@router.message(ReferralStates.entering_payout_amount)
async def process_payout_amount(message: Message, state: FSMContext):
    """Обработка суммы выплаты"""
    user_id = message.from_user.id

    try:
        await message.delete()
    except:
        pass

    balance = await db.get_referral_balance(user_id)
    min_payout = int(await db.get_setting('referral_min_payout') or '500')

    if message.text == "/all":
        amount = balance
    else:
        try:
            amount = int(message.text)
        except:
            await state.clear()
            data = await state.get_data()
            menu_message_id = data.get('menu_message_id')
            if menu_message_id:
                await state.update_data(menu_message_id=menu_message_id)
            return

    if amount < min_payout or amount > balance:
        await state.clear()
        data = await state.get_data()
        menu_message_id = data.get('menu_message_id')
        if menu_message_id:
            await state.update_data(menu_message_id=menu_message_id)
        return

    payment_details = await db.get_payment_details(user_id)
    method = payment_details.get('payment_method')
    details = payment_details.get('payment_details')

    # Создаем заявку
    payout_id = await db.create_payout_request(user_id, amount, method, details)
    await db.decrease_referral_balance(user_id, amount)

    text = (
        f"✅ **ЗАЯВКА СОЗДАНА**\n\n"
        f"💸 Сумма: **{format_number(amount)} руб.**\n"
        f"💳 Способ: {method}\n"
        f"📝 ID заявки: #{payout_id}\n\n"
        f"⏳ Заявка отправлена администратору.\n"
        f"Обычно обрабатывается в течение 24 часов."
    )

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="📊 История операций", callback_data="referral_history"))
    builder.row(InlineKeyboardButton(text="👤 Профиль", callback_data="show_profile"))

    data = await state.get_data()
    menu_message_id = data.get('menu_message_id')

    await state.clear()
    if menu_message_id:
        await state.update_data(menu_message_id=menu_message_id)

    try:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=menu_message_id,
            text=text,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
    except:
        pass


# ===== НАСТРОЙКА РЕКВИЗИТОВ =====

@router.callback_query(F.data == "referral_setup_payment")
async def setup_payment_method(callback: CallbackQuery, state: FSMContext):
    """Выбор способа выплаты"""
    text = (
        "⚙️ **РЕКВИЗИТЫ ДЛЯ ВЫПЛАТ**\n\n"
        "Выберите способ выплаты:"
    )

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💳 Банковская карта", callback_data="payment_method_card"))
    builder.row(InlineKeyboardButton(text="📱 СБП", callback_data="payment_method_sbp"))
    builder.row(InlineKeyboardButton(text="💵 YooMoney", callback_data="payment_method_yoomoney"))
    builder.row(InlineKeyboardButton(text="💰 Другой", callback_data="payment_method_other"))
    builder.row(InlineKeyboardButton(text="⏪ Назад", callback_data="show_profile"))

    await edit_menu(callback, state, text, builder.as_markup())
    await callback.answer()


@router.callback_query(F.data == "payment_method_card")
async def setup_card(callback: CallbackQuery, state: FSMContext):
    """Настройка карты"""
    text = (
        "💳 **БАНКОВСКАЯ КАРТА**\n\n"
        "Введите номер карты (16-19 цифр):"
    )

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⏪ Назад", callback_data="referral_setup_payment"))

    await edit_menu(callback, state, text, builder.as_markup())
    await state.set_state(ReferralStates.entering_card_number)
    await callback.answer()


@router.message(ReferralStates.entering_card_number)
async def process_card_number(message: Message, state: FSMContext):
    """Обработка номера карты"""
    user_id = message.from_user.id

    try:
        await message.delete()
    except:
        pass

    card = re.sub(r'[^\d]', '', message.text)

    if len(card) < 16 or len(card) > 19:
        await state.clear()
        data = await state.get_data()
        menu_message_id = data.get('menu_message_id')
        if menu_message_id:
            await state.update_data(menu_message_id=menu_message_id)
        return

    await db.set_payment_details(user_id, "card", card)

    masked = mask_payment_details("card", card)
    text = f"✅ **КАРТА СОХРАНЕНА**\n\n💳 {masked}"

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="👤 Профиль", callback_data="show_profile"))

    data = await state.get_data()
    menu_message_id = data.get('menu_message_id')

    await state.clear()
    if menu_message_id:
        await state.update_data(menu_message_id=menu_message_id)

    try:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=menu_message_id,
            text=text,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
    except:
        pass


@router.callback_query(F.data == "payment_method_sbp")
async def setup_sbp(callback: CallbackQuery, state: FSMContext):
    """Настройка СБП"""
    text = (
        "📱 **СБП**\n\n"
        "Введите номер телефона (формат: +7XXXXXXXXXX):"
    )

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⏪ Назад", callback_data="referral_setup_payment"))

    await edit_menu(callback, state, text, builder.as_markup())
    await state.set_state(ReferralStates.entering_phone)
    await callback.answer()


@router.message(ReferralStates.entering_phone)
async def process_phone(message: Message, state: FSMContext):
    """Обработка телефона"""
    user_id = message.from_user.id

    try:
        await message.delete()
    except:
        pass

    is_valid, formatted = validate_phone(message.text)

    if not is_valid:
        await state.clear()
        data = await state.get_data()
        menu_message_id = data.get('menu_message_id')
        if menu_message_id:
            await state.update_data(menu_message_id=menu_message_id)
        return

    await db.set_payment_details(user_id, "sbp", formatted)

    masked = mask_payment_details("sbp", formatted)
    text = f"✅ **СБП СОХРАНЕН**\n\n📱 {masked}"

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="👤 Профиль", callback_data="show_profile"))

    data = await state.get_data()
    menu_message_id = data.get('menu_message_id')

    await state.clear()
    if menu_message_id:
        await state.update_data(menu_message_id=menu_message_id)

    try:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=menu_message_id,
            text=text,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
    except:
        pass


@router.callback_query(F.data == "payment_method_yoomoney")
async def setup_yoomoney(callback: CallbackQuery, state: FSMContext):
    """Настройка YooMoney"""
    text = (
        "💵 **YooMoney**\n\n"
        "Введите номер кошелька (11-15 цифр):"
    )

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⏪ Назад", callback_data="referral_setup_payment"))

    await edit_menu(callback, state, text, builder.as_markup())
    await state.set_state(ReferralStates.entering_yoomoney)
    await callback.answer()


@router.message(ReferralStates.entering_yoomoney)
async def process_yoomoney(message: Message, state: FSMContext):
    """Обработка YooMoney"""
    user_id = message.from_user.id

    try:
        await message.delete()
    except:
        pass

    wallet = re.sub(r'[^\d]', '', message.text)

    if len(wallet) < 11 or len(wallet) > 15:
        await state.clear()
        data = await state.get_data()
        menu_message_id = data.get('menu_message_id')
        if menu_message_id:
            await state.update_data(menu_message_id=menu_message_id)
        return

    await db.set_payment_details(user_id, "yoomoney", wallet)

    text = f"✅ **YooMoney СОХРАНЕН**\n\n💵 {wallet}"

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="👤 Профиль", callback_data="show_profile"))

    data = await state.get_data()
    menu_message_id = data.get('menu_message_id')

    await state.clear()
    if menu_message_id:
        await state.update_data(menu_message_id=menu_message_id)

    try:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=menu_message_id,
            text=text,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
    except:
        pass


@router.callback_query(F.data == "payment_method_other")
async def setup_other(callback: CallbackQuery, state: FSMContext):
    """Настройка другого способа"""
    text = (
        "💰 **ДРУГОЙ СПОСОБ**\n\n"
        "Введите реквизиты (минимум 5 символов):"
    )

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⏪ Назад", callback_data="referral_setup_payment"))

    await edit_menu(callback, state, text, builder.as_markup())
    await state.set_state(ReferralStates.entering_other_method)
    await callback.answer()


@router.message(ReferralStates.entering_other_method)
async def process_other_method(message: Message, state: FSMContext):
    """Обработка другого способа"""
    user_id = message.from_user.id

    try:
        await message.delete()
    except:
        pass

    details = message.text.strip()

    if len(details) < 5:
        await state.clear()
        data = await state.get_data()
        menu_message_id = data.get('menu_message_id')
        if menu_message_id:
            await state.update_data(menu_message_id=menu_message_id)
        return

    await db.set_payment_details(user_id, "other", details)

    text = f"✅ **РЕКВИЗИТЫ СОХРАНЕНЫ**\n\n💰 {details[:50]}"

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="👤 Профиль", callback_data="show_profile"))

    data = await state.get_data()
    menu_message_id = data.get('menu_message_id')

    await state.clear()
    if menu_message_id:
        await state.update_data(menu_message_id=menu_message_id)

    try:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=menu_message_id,
            text=text,
            reply_markup=builder.as_markup(),
            parse_mode="Markdown"
        )
    except:
        pass


# ===== ИСТОРИЯ ОПЕРАЦИЙ =====

@router.callback_query(F.data == "referral_history")
async def show_referral_history(callback: CallbackQuery, state: FSMContext):
    """Показать историю операций"""
    user_id = callback.from_user.id

    earnings = await db.get_user_referral_earnings(user_id, 5)
    exchanges = await db.get_user_exchanges(user_id, 5)
    payouts = await db.get_user_payouts(user_id, 5)

    text = "📊 **ИСТОРИЯ ОПЕРАЦИЙ**\n\n"

    if earnings:
        text += "💰 **Заработки:**\n"
        for e in earnings:
            text += f"  • +{e['earnings']} руб. ({e['tokens_given']} ген.)\n"
        text += "\n"

    if exchanges:
        text += "🔄 **Обмены:**\n"
        for ex in exchanges:
            text += f"  • -{ex['amount']} руб. → +{ex['tokens']} ген.\n"
        text += "\n"

    if payouts:
        text += "💸 **Выплаты:**\n"
        for p in payouts:
            status_emoji = {"pending": "⏳", "completed": "✅", "rejected": "❌"}.get(p['status'], "❓")
            text += f"  • {status_emoji} {p['amount']} руб.\n"

    if not earnings and not exchanges and not payouts:
        text += "ℹ️ Пока нет операций"

    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⏪ Назад", callback_data="show_profile"))

    await edit_menu(callback, state, text, builder.as_markup())
    await callback.answer()
