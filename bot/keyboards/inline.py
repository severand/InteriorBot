# --- ИСПРАВЛЕНИЯ ВЕРСИИ: bot/keyboards/inline.py ---
# [2025-11-22 18:05 CET] Добавлена кнопка "Назад к выбору комнаты" в get_style_keyboard.
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
    """Генерирует главное меню - ПО ОДНОЙ КНОПКЕ В РЯД."""
    builder = InlineKeyboardBuilder()

    builder.row(
        InlineKeyboardButton(text="🎨 Создать дизайн", callback_data="create_design")
    )
    builder.row(
        InlineKeyboardButton(text="👤 Профиль", callback_data="show_profile")
    )
    builder.row(
        InlineKeyboardButton(text="💎 Купить генерации", callback_data="buy_generations")
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
        InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="show_profile")
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
        InlineKeyboardButton(text="⬅️ Назад в меню", callback_data="show_profile")
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