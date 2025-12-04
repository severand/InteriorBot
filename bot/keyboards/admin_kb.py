# bot/keyboards/admin_kb.py
# --- ОБНОВЛЕН: 2025-12-04 11:38 - Добавлены кнопки уведомлений и источников ---
# Клавиатуры для админ-панели

from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton


def get_admin_main_menu() -> InlineKeyboardMarkup:
    """Главное меню админ-панели"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="📊 Статистика системы", callback_data="admin_stats")],
        [InlineKeyboardButton(text="👥 Все пользователи", callback_data="admin_users")],
        [InlineKeyboardButton(text="🔍 Найти пользователя", callback_data="admin_find_user")],
        [InlineKeyboardButton(text="💰 История платежей", callback_data="admin_payments")],
        [InlineKeyboardButton(text="🔔 Уведомления", callback_data="admin_notifications")],
        [InlineKeyboardButton(text="🌐 Источники трафика", callback_data="admin_sources")],
        [InlineKeyboardButton(text="🏠 Главное меню бота", callback_data="main_menu")]
    ])
    return keyboard


def get_back_to_admin_menu() -> InlineKeyboardMarkup:
    """Кнопка возврата в админ-меню"""
    keyboard = InlineKeyboardMarkup(inline_keyboard=[
        [InlineKeyboardButton(text="⬅️ Назад в админку", callback_data="admin_main")]
    ])
    return keyboard


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
    buttons.append([InlineKeyboardButton(text="⬅️ Назад в админку", callback_data="admin_main")])

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
