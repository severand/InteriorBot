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
from keyboards.inline import get_main_menu_keyboard, get_profile_keyboard
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
    await show_main_menu(callback, state, admins)
    await callback.answer()


@router.callback_query(F.data == "show_profile")
async def show_profile(callback: CallbackQuery, state: FSMContext):
    """
    Показывает профиль пользователя (баланс, дата регистрации, РЕФЕРАЛЬНАЯ ИНФО).
    РЕДАКТИРУЕТ существующее меню.
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
        
        # Текст профиля с реферальной информацией
        profile_text = (
            f"👤 **ВАШ ПРОФИЛЬ**\n\n"
            f"─────────────────\n"
            f"🎯 **Баланс генераций:** {balance}\n"
            f"─────────────────\n\n"
            f"🎁 **Партнёрская программа:**\n"
            f"🔗 Ваша ссылка: `{referral_link}`\n"
            f"👥 Приглашено: **{referrals_count}** {referrals_word}\n\n"
            f"💰 **Реферальный баланс:**\n"
            f"• Доступно: **{format_number(referral_balance)} руб.**\n"
            f"• Всего заработано: {format_number(referral_total_earned)} руб.\n"
            f"• Выплачено: {format_number(referral_total_paid)} руб.\n\n"
            f"🎯 **Ваши условия:**\n"
            f"• За регистрацию: +2 генерации\n"
            f"• % от покупок: {commission_percent}%\n"
            f"─────────────────"
        )

        # Используем edit_menu вместо edit_text
        # ПРОФИЛЬ УЖЕ СОДЕРЖИТ БАЛАНС - НЕ ДОБАВЛЯЕМ ЕГО ВТОРОЙ РАЗ!
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
    # Очищаем данные о предыдущем фото (если было)
    data = await state.get_data()
    menu_message_id = data.get('menu_message_id')
    
    # Очищаем все данные, кроме menu_message_id
    await state.clear()
    if menu_message_id:
        await state.update_data(menu_message_id=menu_message_id)
    
    await state.set_state(CreationStates.waiting_for_photo)
    
    # Редактируем меню на инструкцию загрузки
    await edit_menu(
        callback=callback,
        state=state,
        text=UPLOAD_PHOTO_TEXT,
        keyboard=None  # Убираем кнопки во время ожидания фото
    )
    await callback.answer()
