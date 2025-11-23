# --- ИСПРАВЛЕНИЯ ВЕРСИИ: bot/keyboards/inline.py ---
# [2025-11-23 19:00 MSK] Обновление навигации:
# - Добавлена кнопка "🏠 Главное меню" во все клавиатуры
# - Улучшена структура кнопок "Назад"
# ---

from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from aiogram.types import InlineKeyboardMarkup

# --- Настройки пакетов для покупки ---
# (токены: цена)
PACKAGES = {
    10: 290,
    25: 490,
    60: 990
}

# --- Настройки комнат и стилей ---
ROOM_TYPES = {
    "living_room": "Гостиная 🛋️",
    "bedroom": "Спальня 🛌",
    "kitchen": "Кухня 🍽️",
    "office": "Офис 🖥️",
}

STYLE_TYPES = {
    "modern": "Современный ✨",
    "minimalist": "Минимализм ⚪",
    "scandinavian": "Скандинавский 🌲",
    "industrial": "Индустриальный ⚙️",
    "rustic": "Рустик 🌾",
}


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Главное меню: "Создать дизайн" и "Профиль".
    """
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="🎨 Создать дизайн", callback_data="create_design")
    )
    builder.row(
        InlineKeyboardButton(text="👤 Профиль", callback_data="show_profile")
    )
    builder.adjust(1)  # ОДНА кнопка в ряд
    return builder.as_markup()


def get_profile_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура профиля: Купить генерации + возврат в Главное меню.
    """
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="💰 Купить генерации", callback_data="buy_generations")
    )
    builder.row(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    )
    builder.adjust(1)
    return builder.as_markup()


def get_room_keyboard() -> InlineKeyboardMarkup:
    """
    Выбор типа комнаты + кнопки навигации.
    """
    builder = InlineKeyboardBuilder()

    # Добавляем кнопки комнат
    for key, text in ROOM_TYPES.items():
        builder.row(
            InlineKeyboardButton(text=text, callback_data=f"room_{key}")
        )

    # Кнопки навигации
    builder.row(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    )
    builder.adjust(1)
    return builder.as_markup()


def get_style_keyboard() -> InlineKeyboardMarkup:
    """
    Выбор стиля дизайна + кнопки навигации.
    """
    builder = InlineKeyboardBuilder()

    # Добавляем кнопки стилей
    for key, text in STYLE_TYPES.items():
        builder.row(
            InlineKeyboardButton(text=text, callback_data=f"style_{key}")
        )

    # Кнопки навигации
    builder.row(
        InlineKeyboardButton(text="⬅️ К выбору комнаты", callback_data="back_to_room")
    )
    builder.row(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    )
    builder.adjust(1)
    return builder.as_markup()


def get_payment_keyboard() -> InlineKeyboardMarkup:
    """
    Выбор пакета генераций + навигация.
    """
    builder = InlineKeyboardBuilder()

    # Добавляем кнопки пакетов
    for tokens, price in PACKAGES.items():
        button_text = f"{tokens} генераций - {price} руб."
        builder.row(
            InlineKeyboardButton(text=button_text, callback_data=f"pay_{tokens}_{price}")
        )

    # Кнопки навигации
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад в профиль", callback_data="show_profile")
    )
    builder.row(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    )
    builder.adjust(1)
    return builder.as_markup()


def get_payment_check_keyboard(url: str) -> InlineKeyboardMarkup:
    """
    Кнопки для оплаты: переход к оплате, проверка статуса, навигация.
    """
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="💰 Перейти к оплате", url=url)
    )
    builder.row(
        InlineKeyboardButton(text="🔄 Я оплатил! (Проверить)", callback_data="check_payment")
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад в профиль", callback_data="show_profile")
    )
    builder.row(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    )
    builder.adjust(1)
    return builder.as_markup()


def get_post_generation_keyboard() -> InlineKeyboardMarkup:
    """
    Кнопки после успешной генерации: новый стиль, новое фото, навигация.
    """
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="🔄 Другой стиль для этого фото", callback_data="change_style")
    )
    builder.row(
        InlineKeyboardButton(text="📸 Загрузить новое фото", callback_data="create_design")
    )
    builder.row(
        InlineKeyboardButton(text="👤 Перейти в профиль", callback_data="show_profile")
    )
    builder.row(
        InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu")
    )
    builder.adjust(1)
    return builder.as_markup()
