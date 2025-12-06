# bot/keyboards/admin_kb.py
# --- ОБНОВЛЕН: 2025-12-06 20:13 - Добавлены настройки с builder.adjust(2), убраны лишние проверки ---
# Клавиатуры для админ-панели

from aiogram.utils.keyboard import InlineKeyboardBuilder
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_admin_main_menu():
    """Главное меню админ-панели"""
    builder = InlineKeyboardBuilder()

    builder.button(text="📊 Статистика системы", callback_data="admin_stats")
    builder.button(text="👥 Все пользователи", callback_data="admin_users")
    builder.button(text="🔍 Найти пользователя", callback_data="admin_find_user")
    builder.button(text="💰 История платежей", callback_data="admin_payments")
    builder.button(text="🔔 Уведомления", callback_data="admin_notifications")
    builder.button(text="🌐 Источники трафика", callback_data="admin_sources")
    builder.button(text="⚙️ Настройки", callback_data="admin_settings")
    builder.button(text="🏠 Главное меню бота", callback_data="main_menu")

    builder.adjust(2)  # ПО 2 КНОПКИ В РЯД

    return builder.as_markup()


def get_admin_settings_menu():
    """Меню настроек: 6 кнопок по 2 в ряд + большая кнопка назад"""
    builder = InlineKeyboardBuilder()

    builder.button(text="💰 Управление балансом", callback_data="settings_balance")
    builder.button(text="📦 Настройка пакетов", callback_data="settings_packages")
    builder.button(text="🎁 Скидки и акции", callback_data="settings_discounts")
    builder.button(text="🎯 Бонусные настройки", callback_data="settings_bonuses")
    builder.button(text="👥 Реферальная система", callback_data="settings_referral")
    builder.button(text="🔧 Настройки", callback_data="settings_system")
    builder.button(text="⬅️ Назад", callback_data="admin_main")

    builder.adjust(2, 2, 2, 1)  # ВОТ ПРАВИЛЬНАЯ НАСТРОЙКА!

    return builder.as_markup()


def get_back_to_admin_menu() -> InlineKeyboardMarkup:
    """Кнопка возврата в админ-меню"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад ", callback_data="admin_main")]
    ])
    return keyboard


def get_back_to_settings():
    """Кнопка возврата в меню настроек"""
    builder = InlineKeyboardBuilder()
    builder.button(text="⬅️ Назад", callback_data="admin_settings")
    return builder.as_markup()


def get_users_list_keyboard(current_page: int, total_pages: int) -> InlineKeyboardMarkup:
    """Клавиатура списка пользователей с пагинацией"""
    buttons = []

    # Кнопки пагинации
    nav_buttons = []
    if current_page > 1:
        nav_buttons.append(
            InlineKeyboardButton(text="⬅️", callback_data=f"admin_users_page_{current_page - 1}")
        )

    nav_buttons.append(
        InlineKeyboardButton(text=f"{current_page}/{total_pages}", callback_data="noop")
    )

    if current_page < total_pages:
        nav_buttons.append(
            InlineKeyboardButton(text="➡️", callback_data=f"admin_users_page_{current_page + 1}")
        )

    buttons.append(nav_buttons)
    buttons.append([InlineKeyboardButton(text="⬅️ Назад ", callback_data="admin_main")])

    keyboard = InlineKeyboardMarkup(inline_keyboard=buttons)
    return keyboard


def get_user_card_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура карточки пользователя"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Добавить генерации", callback_data=f"admin_balance_add_{user_id}"),
            InlineKeyboardButton(text="➖ Списать генерации", callback_data=f"admin_balance_remove_{user_id}")
        ],
        [InlineKeyboardButton(text="🔄 Установить баланс", callback_data=f"admin_balance_set_{user_id}")],
        [InlineKeyboardButton(text="⬅️ Назад к списку", callback_data="admin_users")],
        [InlineKeyboardButton(text="🏠 Главное меню админки", callback_data="admin_main")]
    ])
    return keyboard


def get_balance_management_keyboard(user_id: int) -> InlineKeyboardMarkup:
    """Клавиатура управления балансом"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [
            InlineKeyboardButton(text="➕ Добавить", callback_data=f"admin_balance_add_{user_id}"),
            InlineKeyboardButton(text="➖ Списать", callback_data=f"admin_balance_remove_{user_id}")
        ],
        [InlineKeyboardButton(text="🔄 Установить", callback_data=f"admin_balance_set_{user_id}")],
        [InlineKeyboardButton(text="⬅️ Назад", callback_data=f"admin_user_{user_id}")]
    ])
    return keyboard
