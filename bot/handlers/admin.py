# bot/handlers/admin.py
# --- ОБНОВЛЕН: 2025-12-04 10:55 - Добавлены реальные данные генераций и активности ---
# Убраны заглушки "Скоро", показываются реальные данные из БД

import logging
from aiogram import Router, F
from aiogram.filters import Command
from aiogram.types import Message, CallbackQuery
from aiogram.fsm.context import FSMContext
from datetime import datetime

from database.db import db
from states.fsm import AdminStates
from keyboards.admin_kb import (
    get_admin_main_menu,
    get_back_to_admin_menu,
    get_users_list_keyboard
)

logger = logging.getLogger(__name__)
router = Router()


# ===== ПРОВЕРКА АДМИНА =====
def is_admin(user_id: int, admins: list[int]) -> bool:
    """Проверка, является ли пользователь админом"""
    return user_id in admins


# ===== ГЛАВНОЕ МЕНЮ АДМИН-ПАНЕЛИ (КНОПКА) =====
@router.callback_query(F.data == "admin_panel")
async def show_admin_panel(callback: CallbackQuery, state: FSMContext, admins: list[int]):
    """
    Показывает главное меню админ-панели.
    Срабатывает при нажатии кнопки "⚙️ Админ-панель".
    """
    user_id = callback.from_user.id

    # Проверка прав админа
    if not is_admin(user_id, admins):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return

    # Очищаем FSM-состояние при возврате в главное меню
    await state.clear()

    # Получаем статистику
    total_users = await db.get_total_users_count()
    total_revenue = await db.get_total_revenue()
    new_today = await db.get_new_users_count(days=1)
    successful_payments = await db.get_successful_payments_count()

    # Формируем текст
    admin_text = (
        "👑 **АДМИН-ПАНЕЛЬ**\n\n"
        f"📊 **Общая статистика:**\n"
        f"• Всего пользователей: **{total_users}**\n"
        f"• Новых за сегодня: **{new_today}**\n"
        f"• Общая выручка: **{total_revenue} руб.**\n"
        f"• Успешных платежей: **{successful_payments}**\n\n"
        "Выберите действие:"
    )

    # Редактируем сообщение
    try:
        await callback.message.edit_text(
            text=admin_text,
            reply_markup=get_admin_main_menu(),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка редактирования сообщения админ-панели: {e}")
        await callback.message.answer(
            text=admin_text,
            reply_markup=get_admin_main_menu(),
            parse_mode="Markdown"
        )

    await callback.answer()


# ===== ВОЗВРАТ В ГЛАВНОЕ МЕНЮ АДМИНКИ =====
@router.callback_query(F.data == "admin_main")
async def back_to_admin_main(callback: CallbackQuery, state: FSMContext, admins: list[int]):
    """Возврат в главное меню админ-панели"""
    await show_admin_panel(callback, state, admins)


# ===== ДЕТАЛЬНАЯ СТАТИСТИКА =====
@router.callback_query(F.data == "admin_stats")
async def show_admin_stats(callback: CallbackQuery, admins: list[int]):
    """Показать детальную статистику системы"""
    user_id = callback.from_user.id

    if not is_admin(user_id, admins):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return

    # ПОЛЬЗОВАТЕЛИ
    total_users = await db.get_total_users_count()
    new_today = await db.get_new_users_count(days=1)
    new_week = await db.get_new_users_count(days=7)
    active_today = await db.get_active_users_count(days=1)
    active_week = await db.get_active_users_count(days=7)

    # ГЕНЕРАЦИИ
    total_generations = await db.get_total_generations()
    generations_today = await db.get_generations_count(days=1)
    generations_week = await db.get_generations_count(days=7)
    conversion_rate = await db.get_conversion_rate()

    # ФИНАНСЫ
    total_revenue = await db.get_total_revenue()
    revenue_today = await db.get_revenue_by_period(days=1)
    revenue_week = await db.get_revenue_by_period(days=7)
    successful_payments = await db.get_successful_payments_count()
    average_payment = await db.get_average_payment()

    # ПОПУЛЯРНЫЕ КОМНАТЫ И СТИЛИ
    popular_rooms = await db.get_popular_rooms(limit=5)
    popular_styles = await db.get_popular_styles(limit=5)

    # Формируем списки
    if popular_rooms:
        rooms_text = "\n".join([f"  • {room['room_type']}: **{room['count']}**" for room in popular_rooms])
    else:
        rooms_text = "  • Данных пока нет"

    if popular_styles:
        styles_text = "\n".join([f"  • {style['style_type']}: **{style['count']}**" for style in popular_styles])
    else:
        styles_text = "  • Данных пока нет"

    stats_text = (
        "📊 **ДЕТАЛЬНАЯ СТАТИСТИКА СИСТЕМЫ**\n\n"
        "👥 **Пользователи:**\n"
        f"• Всего: **{total_users}**\n"
        f"• Новых за сегодня: **{new_today}**\n"
        f"• Новых за неделю: **{new_week}**\n"
        f"• Активных за сегодня: **{active_today}**\n"
        f"• Активных за неделю: **{active_week}**\n\n"
        "🎨 **Генерации:**\n"
        f"• Всего сгенерировано: **{total_generations}**\n"
        f"• За сегодня: **{generations_today}**\n"
        f"• За неделю: **{generations_week}**\n"
        f"• Средняя конверсия: **{conversion_rate}**\n\n"
        "💰 **Финансы:**\n"
        f"• Общая выручка: **{total_revenue} руб.**\n"
        f"• Выручка за сегодня: **{revenue_today} руб.**\n"
        f"• Выручка за неделю: **{revenue_week} руб.**\n"
        f"• Успешных платежей: **{successful_payments}**\n"
        f"• Средний чек: **{average_payment} руб.**\n\n"
        "🏠 **Популярные комнаты:**\n"
        f"{rooms_text}\n\n"
        "🎨 **Популярные стили:**\n"
        f"{styles_text}"
    )

    try:
        await callback.message.edit_text(
            text=stats_text,
            reply_markup=get_back_to_admin_menu(),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка показа статистики: {e}")

    await callback.answer()


# ===== СПИСОК ВСЕХ ПОЛЬЗОВАТЕЛЕЙ =====
@router.callback_query(F.data == "admin_users")
async def show_all_users(callback: CallbackQuery, admins: list[int]):
    """Показать список всех пользователей (первая страница)"""
    await show_users_page(callback, page=1, admins=admins)


@router.callback_query(F.data.startswith("admin_users_page_"))
async def show_users_page_handler(callback: CallbackQuery, admins: list[int]):
    """Обработчик пагинации пользователей"""
    user_id = callback.from_user.id

    if not is_admin(user_id, admins):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return

    # Извлекаем номер страницы
    page = int(callback.data.split("_")[-1])
    await show_users_page(callback, page=page, admins=admins)


async def show_users_page(callback: CallbackQuery, page: int, admins: list[int]):
    """Показать конкретную страницу пользователей"""
    user_id = callback.from_user.id

    if not is_admin(user_id, admins):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return

    # Получаем пользователей для страницы
    users, total_pages = await db.get_all_users_paginated(page=page, per_page=10)

    if not users:
        await callback.answer("📭 Пользователей нет.", show_alert=True)
        return

    # Формируем текст
    users_text = f"👥 **СПИСОК ПОЛЬЗОВАТЕЛЕЙ** (стр. {page}/{total_pages})\n\n"
    for idx, user in enumerate(users, start=1):
        user_id_str = user['user_id']
        username = user['username']
        balance = user['balance']

        # Экранируем username
        username_clean = username.replace('@', '').replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(
            ']', '\\]').replace('`', '\\`')

        users_text += f"{idx}. ID: `{user_id_str}` | {username_clean} | 💰 {balance}\n"

    try:
        await callback.message.edit_text(
            text=users_text,
            reply_markup=get_users_list_keyboard(page, total_pages),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка показа пользователей: {e}")

    await callback.answer()


# ===== ПОИСК ПОЛЬЗОВАТЕЛЯ =====
@router.callback_query(F.data == "admin_find_user")
async def start_find_user(callback: CallbackQuery, state: FSMContext, admins: list[int]):
    """Начало поиска пользователя"""
    user_id = callback.from_user.id

    if not is_admin(user_id, admins):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return

    # Устанавливаем состояние ожидания поискового запроса
    await state.set_state(AdminStates.waiting_for_search)

    search_text = (
        "🔍 **ПОИСК ПОЛЬЗОВАТЕЛЯ**\n\n"
        "Отправьте мне один из следующих данных:\n\n"
        "• `ID пользователя` (например: `123456789`)\n"
        "• `@username` (например: `@ivan_petrov`)\n"
        "• `Реферальный код` (например: `abc123xyz`)\n\n"
        "⚠️ Для отмены нажмите кнопку ниже."
    )

    try:
        await callback.message.edit_text(
            text=search_text,
            reply_markup=get_back_to_admin_menu(),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка показа поиска: {e}")

    await callback.answer()


@router.message(AdminStates.waiting_for_search)
async def process_search_query(message: Message, state: FSMContext, admins: list[int]):
    """Обработка поискового запроса"""
    user_id = message.from_user.id

    if not is_admin(user_id, admins):
        await message.answer("❌ У вас нет прав администратора.")
        return

    query = message.text.strip()

    # Выполняем поиск
    user_data = await db.search_user(query)

    if not user_data:
        await message.answer(
            "❌ **Пользователь не найден!**\n\n"
            "Попробуйте другой запрос.",
            parse_mode="Markdown"
        )
        return

    # Очищаем состояние
    await state.clear()

    # Получаем данные пользователя
    found_user_id = user_data['user_id']
    username = user_data['username'] or "Не указан"
    balance = user_data['balance']
    referral_balance = user_data['referral_balance']
    referral_code = user_data['referral_code']
    referrals_count = user_data['referrals_count']
    reg_date = user_data['reg_date']
    total_generations = user_data.get('total_generations', 0)

    # Получаем статистику платежей
    payments_stats = await db.get_user_payments_stats(found_user_id)
    payments_count = payments_stats['count']
    total_paid = payments_stats['total_amount']

    # Получаем последние платежи
    recent_payments = await db.get_user_recent_payments(found_user_id, limit=5)

    # Получаем информацию о рефере
    referrer_info = await db.get_referrer_info(found_user_id)

    # Формируем ссылку на Telegram
    tg_link = f"[{username}](tg://user?id={found_user_id})"

    # Формируем информацию о рефере
    if referrer_info:
        referrer_id = referrer_info['referrer_id']
        referrer_username = referrer_info['referrer_username'] or "Не указан"
        referrer_text = f"[{referrer_username}](tg://user?id={referrer_id}) (ID: `{referrer_id}`)"
    else:
        referrer_text = "Нет"

    # Формируем список последних платежей
    if recent_payments:
        payments_text = ""
        for payment in recent_payments:
            # Парсим дату
            try:
                payment_date = datetime.fromisoformat(payment['payment_date'])
                date_str = payment_date.strftime("%d.%m.%Y %H:%M")
            except:
                date_str = payment['payment_date']
            
            payments_text += f"  • {payment['amount']} руб. ({payment['tokens']} ток.) - {date_str}\n"
    else:
        payments_text = "  • Платежей нет\n"

    result_text = (
        "✅ **ПОЛЬЗОВАТЕЛЬ НАЙДЕН!**\n\n"
        f"🆔 **ID:** `{found_user_id}`\n"
        f"👤 **Username:** {tg_link}\n"
        f"💰 **Баланс генераций:** {balance}\n"
        f"💸 **Реферальный баланс:** {referral_balance} руб.\n"
        f"🔗 **Реферальный код:** `{referral_code}`\n"
        f"👥 **Привлечено рефералов:** {referrals_count}\n"
        f"🔽 **Пригласил:** {referrer_text}\n"
        f"📅 **Дата регистрации:** {reg_date}\n\n"
        "📊 **Статистика:**\n"
        f"• Количество оплат: **{payments_count}**\n"
        f"• Всего оплачено: **{total_paid} руб.**\n"
        f"• Выполнено генераций: **{total_generations}**\n\n"
        "💳 **Последние платежи:**\n"
        f"{payments_text}\n"
        "⚙️ **Доступные действия:**\n"
        f"• `/add_tokens {found_user_id} <кол-во>` - добавить токены\n"
        f"• `/balance {found_user_id}` - проверить баланс"
    )

    await message.answer(
        text=result_text,
        reply_markup=get_back_to_admin_menu(),
        parse_mode="Markdown"
    )


# ===== ИСТОРИЯ ПЛАТЕЖЕЙ =====
@router.callback_query(F.data == "admin_payments")
async def show_payments_history(callback: CallbackQuery, admins: list[int]):
    """Показать историю платежей"""
    user_id = callback.from_user.id

    if not is_admin(user_id, admins):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return

    # Получаем последние 20 платежей
    payments = await db.get_all_payments(limit=20)

    if not payments:
        await callback.answer("📭 Платежей пока нет.", show_alert=True)
        return

    # Формируем текст
    payments_text = "💰 **ИСТОРИЯ ПЛАТЕЖЕЙ** (последние 20)\n\n"
    for idx, payment in enumerate(payments, start=1):
        status_emoji = "✅" if payment['status'] == 'succeeded' else "⏳"
        # Экранируем username
        username_clean = payment['username'].replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']',
                                                                                                                 '\\]').replace(
            '`', '\\`')

        payments_text += (
            f"{idx}. {status_emoji} `{payment['user_id']}` | "
            f"{username_clean} | "
            f"**{payment['amount']} руб.** | "
            f"{payment['tokens']} токенов\n"
        )

    try:
        await callback.message.edit_text(
            text=payments_text,
            reply_markup=get_back_to_admin_menu(),
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Ошибка показа платежей: {e}")

    await callback.answer()


# ===== КОМАНДЫ =====

@router.message(Command("add_tokens"))
async def cmd_add_tokens(message: Message, admins: list[int]):
    """
    Добавить токены пользователю
    Использование: /add_tokens <user_id> <количество>
    Пример: /add_tokens 123456789 10
    """
    user_id = message.from_user.id

    if not is_admin(user_id, admins):
        await message.answer("❌ У вас нет прав администратора.")
        return

    try:
        args = message.text.split()
        if len(args) != 3:
            await message.answer(
                "❌ Неверный формат команды!\n\n"
                "Использование: `/add_tokens <user_id> <количество>`\n"
                "Пример: `/add_tokens 123456789 10`",
                parse_mode="Markdown"
            )
            return

        target_user_id = int(args[1])
        tokens_to_add = int(args[2])

        if tokens_to_add <= 0:
            await message.answer("❌ Количество токенов должно быть больше 0!")
            return

        await db.add_tokens(target_user_id, tokens_to_add)
        new_balance = await db.get_balance(target_user_id)

        await message.answer(
            f"✅ **Успешно!**\n\n"
            f"👤 Пользователь: `{target_user_id}`\n"
            f"➕ Добавлено токенов: **{tokens_to_add}**\n"
            f"💰 Новый баланс: **{new_balance}**",
            parse_mode="Markdown"
        )

        logger.info(f"Admin {user_id} added {tokens_to_add} tokens to user {target_user_id}")

    except ValueError:
        await message.answer(
            "❌ Ошибка! ID пользователя и количество токенов должны быть числами.\n\n"
            "Пример: `/add_tokens 123456789 10`",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error in add_tokens: {e}")
        await message.answer(f"❌ Произошла ошибка: {e}")


@router.message(Command("balance"))
async def cmd_check_balance(message: Message, admins: list[int]):
    """
    Проверить баланс пользователя
    Использование: /balance <user_id>
    Пример: /balance 123456789
    """
    user_id = message.from_user.id

    if not is_admin(user_id, admins):
        await message.answer("❌ У вас нет прав администратора.")
        return

    try:
        args = message.text.split()
        if len(args) != 2:
            await message.answer(
                "❌ Неверный формат команды!\n\n"
                "Использование: `/balance <user_id>`\n"
                "Пример: `/balance 123456789`",
                parse_mode="Markdown"
            )
            return

        target_user_id = int(args[1])
        balance = await db.get_balance(target_user_id)

        await message.answer(
            f"💰 **Баланс пользователя**\n\n"
            f"👤 ID: `{target_user_id}`\n"
            f"✨ Токенов: **{balance}**",
            parse_mode="Markdown"
        )

    except ValueError:
        await message.answer(
            "❌ Ошибка! ID пользователя должен быть числом.\n\n"
            "Пример: `/balance 123456789`",
            parse_mode="Markdown"
        )
    except Exception as e:
        logger.error(f"Error in check_balance: {e}")
        await message.answer(f"❌ Произошла ошибка: {e}")


@router.message(Command("users"))
async def cmd_list_users(message: Message, admins: list[int]):
    """
    Показать список последних 10 пользователей
    Использование: /users
    """
    user_id = message.from_user.id

    if not is_admin(user_id, admins):
        await message.answer("❌ У вас нет прав администратора.")
        return

    try:
        users = await db.get_recent_users(limit=10)

        if not users:
            await message.answer("📭 Пользователей пока нет.")
            return

        text = "👥 **Последние пользователи:**\n\n"
        for idx, user in enumerate(users, 1):
            user_id_str = user.get('user_id', 'Unknown')
            username = user.get('username', 'Не указано')
            balance = user.get('balance', 0)

            # Экранируем username
            username_clean = username.replace('_', '\\_').replace('*', '\\*').replace('[', '\\[').replace(']',
                                                                                                          '\\]').replace(
                '`', '\\`')

            text += f"{idx}. ID: `{user_id_str}` | {username_clean} | 💰 {balance}\n"

        await message.answer(text, parse_mode="Markdown")

    except Exception as e:
        logger.error(f"Error in list_users: {e}")
        await message.answer(f"❌ Произошла ошибка: {e}")

# ===== УВЕДОМЛЕНИЯ АДМИНОВ =====

@router.callback_query(F.data == "admin_notifications")
async def show_admin_notifications(callback: CallbackQuery, admins: list[int]):
    user_id = callback.from_user.id
    if not is_admin(user_id, admins):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return

    settings = await db.get_admin_notifications(user_id)

    text = (
        "🔔 **НАСТРОЙКИ УВЕДОМЛЕНИЙ**\n\n"
        f"• Новый пользователь: {'✅' if settings['notify_new_users'] else '❌'}\n"
        f"• Новая оплата: {'✅' if settings['notify_new_payments'] else '❌'}\n"
        f"• Критические ошибки: {'✅' if settings['notify_critical_errors'] else '❌'}\n\n"
        "Нажмите на кнопку, чтобы переключить."
    )

    from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton

    kb = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(
            text=f"👤 Новый пользователь {'✅' if settings['notify_new_users'] else '❌'}",
            callback_data="notify_toggle_new_users"
        )],
        [InlineKeyboardButton(
            text=f"💳 Новая оплата {'✅' if settings['notify_new_payments'] else '❌'}",
            callback_data="notify_toggle_new_payments"
        )],
        [InlineKeyboardButton(
            text=f"⚠️ Критические ошибки {'✅' if settings['notify_critical_errors'] else '❌'}",
            callback_data="notify_toggle_critical"
        )],
        [InlineKeyboardButton(text="⬅️ Назад в админку", callback_data="admin_main")]
    ])

    await callback.message.edit_text(text=text, reply_markup=kb, parse_mode="Markdown")
    await callback.answer()


async def _toggle_notify_field(callback: CallbackQuery, admins: list[int], field: str):
    user_id = callback.from_user.id
    if not is_admin(user_id, admins):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return

    settings = await db.get_admin_notifications(user_id)
    settings[field] = 0 if settings[field] else 1
    await db.set_admin_notifications(
        admin_id=user_id,
        notify_new_users=settings["notify_new_users"],
        notify_new_payments=settings["notify_new_payments"],
        notify_critical_errors=settings["notify_critical_errors"],
    )
    await show_admin_notifications(callback, admins)


@router.callback_query(F.data == "notify_toggle_new_users")
async def notify_toggle_new_users(callback: CallbackQuery, admins: list[int]):
    await _toggle_notify_field(callback, admins, "notify_new_users")


@router.callback_query(F.data == "notify_toggle_new_payments")
async def notify_toggle_new_payments(callback: CallbackQuery, admins: list[int]):
    await _toggle_notify_field(callback, admins, "notify_new_payments")


@router.callback_query(F.data == "notify_toggle_critical")
async def notify_toggle_critical(callback: CallbackQuery, admins: list[int]):
    await _toggle_notify_field(callback, admins, "notify_critical_errors")


# ===== ИСТОЧНИКИ ТРАФИКА =====

@router.callback_query(F.data == "admin_sources")
async def show_sources_stats(callback: CallbackQuery, admins: list[int]):
    user_id = callback.from_user.id
    if not is_admin(user_id, admins):
        await callback.answer("❌ У вас нет прав администратора.", show_alert=True)
        return

    sources = await db.get_sources_stats()
    if not sources:
        text = "🌐 **Источники трафика**\n\nДанных пока нет."
    else:
        text = "🌐 **Источники трафика**\n\n"
        for item in sources:
            text += f"• `{item['source']}` — **{item['count']}** пользователей\n"

    await callback.message.edit_text(
        text=text,
        reply_markup=get_back_to_admin_menu(),
        parse_mode="Markdown"
    )
    await callback.answer()

