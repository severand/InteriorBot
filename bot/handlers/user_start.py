# bot/handlers/user_start.py
# --- ОБНОВЛЕН: 2025-12-04 12:40 - Убрано дублирование баланса в профиле ---
# [2025-12-04 12:18] Исправлены отступы источников и уведомлений
# [2025-11-23 19:00 MSK] Реализована система единого меню
# [2025-12-03] Добавлена обработка реферальных ссылок и обновлен профиль
# [2025-12-03 19:46] Добавлено отображение баланса в cmd_start

import logging
from aiogram import Router, F
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext

# Импорты наших модулей
from database.db import db
from config import config
from states.fsm import CreationStates
from keyboards.inline import get_main_menu_keyboard, get_profile_keyboard, get_upload_photo_keyboard
from aiogram.types import Message, CallbackQuery, InlineKeyboardButton

from utils.texts import START_TEXT, UPLOAD_PHOTO_TEXT
from utils.navigation import edit_menu, show_main_menu
from utils.helpers import add_balance_to_text

logger = logging.getLogger(__name__)
router = Router()


@router.message(F.text.startswith("/start"))
async def cmd_start(message: Message, state: FSMContext, admins: list[int]):
    """
    Обрабатывает команду /start.
    Создает пользователя в базе и показывает главное меню.
    ВАЖНО: Сохраняет menu_message_id для дальнейшей навигации.
    ОБРАБАТЫВАЕТ РЕФЕРАЛЬНЫЕ ССЫЛКИ.
    """
    await state.clear()

    user_id = message.from_user.id
    username = message.from_user.username

    # Парсим реферальный код из /start ref_ABC12345
    referrer_code = None
    if len(message.text.split()) > 1:
        args = message.text.split()[1]
        if args.startswith('ref_'):
            referrer_code = args.replace('ref_', '')

    # Создаем пользователя в базе (если его нет) с реферальным кодом
    await db.create_user(user_id, username, referrer_code)

    # Разбор источника из start-параметра
    start_param = message.text.split()[1] if len(message.text.split()) > 1 else None
    if start_param and start_param.startswith("src_"):
        source = start_param[4:]
        await db.set_user_source(user_id, source)

    # Уведомление админов о новом пользователе
    try:
        from loader import bot
        admins_to_notify = await db.get_admins_for_notification("notify_new_users")
        for admin_id in admins_to_notify:
            try:
                await bot.send_message(
                    admin_id,
                    f"👤 Новый пользователь: ID `{user_id}`, username: @{username or 'не указан'}",
                    parse_mode="Markdown"
                )
            except Exception as e:
                logger.error(f"Не удалось отправить уведомление админу {admin_id}: {e}")
    except Exception as e:
        logger.error(f"Ошибка при отправке уведомлений о новом пользователе: {e}")

    # Добавляем баланс к тексту приветствия
    text = await add_balance_to_text(START_TEXT, user_id)

    # Отправляем главное меню и СОХРАНЯЕМ его ID
    menu_msg = await message.answer(
        text,
        reply_markup=get_main_menu_keyboard(is_admin=user_id in admins),
        parse_mode="Markdown"
    )

    # КРИТИЧЕСКОЕ: сохраняем ID главного меню
    await state.update_data(menu_message_id=menu_msg.message_id)


@router.callback_query(F.data == "main_menu")
async def back_to_main_menu(callback: CallbackQuery, state: FSMContext, admins: list[int]):
    """
    Возврат в главное меню из любого места.
    Очищает состояние FSM и показывает стартовый экран.
    """
    # 🔍 ЛОГ: ЧТО ПРИХОДИТ В ФУНКЦИЮ
    data = await state.get_data()
    logger.warning(
        f"🔍 [BACK TO MAIN] STEP 1 - BEFORE show_main_menu(): data={data}, callback.message.message_id={callback.message.message_id}")

    await show_main_menu(callback, state, admins)
    await callback.answer()



@router.callback_query(F.data == "show_profile")
async def show_profile(callback: CallbackQuery, state: FSMContext):
    """
    Показывает профиль пользователя.
    ИСПОЛЬЗУЕТ PROFILE_TEXT из texts.py
    """
    user_id = callback.from_user.id

    # Получаем данные пользователя из БД
    user_data = await db.get_user_data(user_id)

    if not user_data:
        # Автоматически создаем пользователя
        username = callback.from_user.username
        await db.create_user(user_id, username)
        user_data = await db.get_user_data(user_id)

    if user_data:
        balance = user_data.get('balance', 0)
        reg_date = user_data.get('reg_date', 'неизвестно')
        username = user_data.get('username') or callback.from_user.username or 'не указан'

        # Форматируем текст профиля из texts.py
        from utils.texts import PROFILE_TEXT

        profile_text = PROFILE_TEXT.format(
            user_id=user_id,
            username=username,
            balance=balance,
            reg_date=reg_date
        )

        # Используем edit_menu (баланс НЕ добавляем - он уже в тексте!)
        await edit_menu(
            callback=callback,
            state=state,
            text=profile_text,
            keyboard=get_profile_keyboard(),
            show_balance=False  # КРИТИЧНО: баланс уже в profile_text!
        )
    else:
        await callback.answer("❌ Ошибка создания профиля. Попробуйте /start", show_alert=True)

    await callback.answer()


@router.callback_query(F.data == "buy_generations")
async def buy_generations_handler(callback: CallbackQuery, state: FSMContext):
    """
    Обрабатывает нажатие кнопки 'Купить генерации' в профиле.
    Переводит в меню выбора пакета.
    """
    from keyboards.inline import get_payment_keyboard

    await edit_menu(
        callback=callback,
        state=state,
        text="💰 **Выберите пакет генераций:**\n\nПосле оплаты баланс автоматически пополнится.",
        keyboard=get_payment_keyboard()
    )
    await callback.answer()



@router.callback_query(F.data == "create_design")
async def start_creation(callback: CallbackQuery, state: FSMContext):
    """
    Начинает процесс создания дизайна.
    Переводит в состояние ожидания фото и РЕДАКТИРУЕТ меню.
    """
    user_id = callback.from_user.id
    await db.log_activity(user_id, 'create_design')

    # СОХРАНЯЕМ важные данные перед очисткой
    data = await state.get_data()
    menu_message_id = data.get('menu_message_id')
    photo_message_id = data.get('photo_message_id')
    design_generated = data.get('design_generated', False)

    logger.info(f"📸 [CREATE DESIGN] BEFORE clear: photo={photo_message_id}, design={design_generated}")

    # Очищаем состояние
    await state.clear()

    # ВОССТАНАВЛИВАЕМ важные данные
    if menu_message_id:
        await state.update_data(menu_message_id=menu_message_id)
    if photo_message_id:
        await state.update_data(photo_message_id=photo_message_id)
        await state.update_data(design_generated=design_generated)
        logger.info(f"📸 [CREATE DESIGN] AFTER restore: photo={photo_message_id}")

    await state.set_state(CreationStates.waiting_for_photo)

    # Редактируем меню на инструкцию загрузки
    await edit_menu(
        callback=callback,
        state=state,
        text=UPLOAD_PHOTO_TEXT,
        keyboard=get_upload_photo_keyboard()
    )
    await callback.answer()




@router.callback_query(F.data == "show_statistics")
async def show_statistics(callback: CallbackQuery, state: FSMContext):
    """
    Показывает статистику пользователя (базовая версия)
    """
    user_id = callback.from_user.id

    # Получаем данные из БД
    user_data = await db.get_user_data(user_id)

    if not user_data:
        await callback.answer("❌ Ошибка получения данных", show_alert=True)
        return

    balance = user_data.get('balance', 0)
    reg_date = user_data.get('reg_date', 'неизвестно')

    stats_text = (
        f"📊 **СТАТИСТИКА**\n\n"
        f"─────────────────\n"
        f"✨ Текущий баланс: **{balance}** генераций\n"
        f"🗓️ С нами с: {reg_date}\n"
        f"─────────────────\n\n"
        f"ℹ️ Детальная статистика в разработке..."
    )

    # Клавиатура
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⬅️ Назад в профиль", callback_data="show_profile"))

    # Используем edit_menu
    await edit_menu(
        callback=callback,
        state=state,
        text=stats_text,
        keyboard=builder.as_markup(),
        show_balance=False
    )

    await callback.answer()



@router.callback_query(F.data == "show_referral_program")
async def show_referral_program(callback: CallbackQuery, state: FSMContext):
    """
    Показывает экран партнёрской программы с реферальной информацией
    """
    user_id = callback.from_user.id

    # Получаем данные пользователя
    user_data = await db.get_user_data(user_id)

    if not user_data:
        await callback.answer("❌ Ошибка получения данных", show_alert=True)
        return

    # Реферальная информация
    referral_code = user_data.get('referral_code', '')
    referrals_count = user_data.get('referrals_count', 0)
    referral_balance = user_data.get('referral_balance', 0)
    referral_total_earned = user_data.get('referral_total_earned', 0) or 0
    referral_total_paid = user_data.get('referral_total_paid', 0) or 0

    # Получаем процент комиссии из настроек
    commission_percent = await db.get_setting('referral_commission_percent') or '10'

    # Формируем реферальную ссылку
    bot_username = config.BOT_USERNAME.replace('@', '')
    referral_link = f"t.me/{bot_username}?start=ref_{referral_code}"

    # Правильное склонение слова "друг"
    def get_word_form(count: int) -> str:
        if count % 10 == 1 and count % 100 != 11:
            return "друг"
        elif 2 <= count % 10 <= 4 and (count % 100 < 10 or count % 100 >= 20):
            return "друга"
        else:
            return "друзей"

    referrals_word = get_word_form(referrals_count)

    # Форматирование чисел с пробелами
    def format_number(num: int) -> str:
        return f"{num:,}".replace(',', ' ')

    # Текст партнёрской программы
    referral_text = (
        f"🎁 **ПАРТНЁРСКАЯ ПРОГРАММА**\n\n"
        f"─────────────────\n"
        f"🔗 Ваша ссылка:\n`{referral_link}`\n\n"
        f"👥 Приглашено: **{referrals_count}** {referrals_word}\n"
        f"─────────────────\n\n"
        f"💰 **Реферальный баланс:**\n"
        f"• Доступно: **{format_number(referral_balance)} руб.**\n"
        f"• Всего заработано: {format_number(referral_total_earned)} руб.\n"
        f"• Выплачено: {format_number(referral_total_paid)} руб.\n\n"
        f"🎯 **Ваши условия:**\n"
        f"• За регистрацию: +2 генерации\n"
        f"• % от покупок: {commission_percent}%\n"
        f"─────────────────"
    )

    # Клавиатура для партнёрской программы
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="💸 Вывести деньги", callback_data="referral_request_payout"),
        InlineKeyboardButton(text="💎 Обменять на генерации", callback_data="referral_exchange_tokens")
    )
    builder.row(InlineKeyboardButton(text="⚙️ Реквизиты для выплат", callback_data="referral_setup_payment"))
    builder.row(InlineKeyboardButton(text="📊 История операций", callback_data="referral_history"))
    builder.row(InlineKeyboardButton(text="⬅️ Назад в профиль", callback_data="show_profile"))

    builder.adjust(2, 1, 1, 1)

    # Используем edit_menu
    await edit_menu(
        callback=callback,
        state=state,
        text=referral_text,
        keyboard=builder.as_markup(),
        show_balance=False
    )

    await callback.answer()


@router.callback_query(F.data == "show_support")
async def show_support(callback: CallbackQuery, state: FSMContext):
    """
    Показывает информацию о поддержке
    """
    support_text = (
        "💬 **ПОДДЕРЖКА**\n\n"
        "─────────────────\n"
        "📧 Email: support@example.com\n"
        "💬 Telegram: `@support_bot`\n"
        "─────────────────\n\n"
        "ℹ️ Мы ответим в течение 24 часов"
    )

    # Клавиатура
    from aiogram.utils.keyboard import InlineKeyboardBuilder
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="⬅️ Назад в профиль", callback_data="show_profile"))

    # Используем edit_menu
    await edit_menu(
        callback=callback,
        state=state,
        text=support_text,
        keyboard=builder.as_markup(),
        show_balance=False
    )

    await callback.answer()
