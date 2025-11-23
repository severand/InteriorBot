# --- ИСПРАВЛЕНИЯ ВЕРСИИ: bot/keyboards/inline.py ---
# [2025-11-23 11:20 CET] Реализована новая навигация:
# - Главное меню: Создать дизайн, Профиль.
# - Меню Профиля: Купить генерации, Меню.
# ---аа

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


def get_profile_keyboard() -> InlineKeyboardMarkup:
    """
    Клавиатура для отображения в профиле. Содержит "Купить" и "Меню".
    """
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="💰 Купить генерации", callback_data="buy_generations")
    )
    builder.row(
        InlineKeyboardButton(text="🏠 Меню", callback_data="main_menu")
    )
    builder.adjust(1)
    return builder.as_markup()


def get_main_menu_keyboard() -> InlineKeyboardMarkup:
    """
    Главное меню: "Создать дизайн" и "Профиль" (2 кнопки).
    """
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="🛠️ Создать дизайн", callback_data="create_design")
    )
    builder.row(
        InlineKeyboardButton(text="👤 Профиль", callback_data="show_profile")
    )
    builder.adjust(1)  # ОДНА кнопка в ряд
    return builder.as_markup()


def get_room_keyboard() -> InlineKeyboardMarkup:
    """Генерирует кнопки для выбора типа комнаты - ПО ОДНОЙ КНОПКЕ В РЯД."""
    builder = InlineKeyboardBuilder()

    # Добавляем кнопки комнат ПО ОДНОЙ В РЯД
    for key, text in ROOM_TYPES.items():
        builder.row(
            InlineKeyboardButton(text=text, callback_data=f"room_{key}")
        )

    builder.row(
        InlineKeyboardButton(text="⬅️ Загрузить новое фото", callback_data="create_design")
    )
    builder.adjust(1)  # ОДНА кнопка в ряд
    return builder.as_markup()


def get_style_keyboard() -> InlineKeyboardMarkup:
    """Генерирует кнопки для выбора стиля дизайна - ПО ОДНОЙ КНОПКЕ В РЯД."""
    builder = InlineKeyboardBuilder()

    # Добавляем кнопки стилей ПО ОДНОЙ В РЯД
    for key, text in STYLE_TYPES.items():
        builder.row(
            InlineKeyboardButton(text=text, callback_data=f"style_{key}")
        )

    # --- НОВОЕ: Кнопка Назад ---
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад к выбору комнаты", callback_data="back_to_room")
    )

    builder.adjust(1)  # ОДНА кнопка в ряд
    return builder.as_markup()


def get_payment_keyboard() -> InlineKeyboardMarkup:
    """Генерирует кнопки для выбора пакетов генераций - ПО ОДНОЙ КНОПКЕ В РЯД."""
    builder = InlineKeyboardBuilder()

    # Добавляем кнопки пакетов ПО ОДНОЙ В РЯД
    for tokens, price in PACKAGES.items():
        button_text = f"{tokens} генераций - {price} руб."
        builder.row(
            InlineKeyboardButton(text=button_text, callback_data=f"pay_{tokens}_{price}")
        )

    builder.row(
        InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="show_profile") # Остается show_profile, т.к. из профиля сюда
    )
    builder.adjust(1)  # ОДНА кнопка в ряд
    return builder.as_markup()


def get_payment_check_keyboard(url: str) -> InlineKeyboardMarkup:
    """Кнопки для перехода к оплате и проверки статуса - ПО ОДНОЙ КНОПКЕ В РЯД."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="💰 Перейти к оплате", url=url)
    )
    builder.row(
        InlineKeyboardButton(text="🔄 Я оплатил! (Проверить)", callback_data="check_payment")
    )
    builder.row(
        InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="show_profile") # Остается show_profile
    )
    builder.adjust(1)  # ОДНА кнопка в ряд
    return builder.as_markup()


def get_post_generation_keyboard() -> InlineKeyboardMarkup:
    """Кнопки после успешной генерации с вариантами продолжения - ПО ОДНОЙ КНОПКЕ В РЯД."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="🎨 Выбрать новый стиль", callback_data="change_style")
    )
    builder.row(
        InlineKeyboardButton(text="📸 Загрузить другое фото", callback_data="create_design")
    )
    builder.row(
        InlineKeyboardButton(text="👤 Перейти в профиль", callback_data="show_profile")
    )
    builder.adjust(1)  # ОДНА кнопка в ряд
    return builder.as_markup()