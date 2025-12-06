# keyboards/inline.py
# Дата объединения: 05.12.2025

from aiogram.utils.keyboard import InlineKeyboardBuilder, InlineKeyboardButton
from aiogram.types import InlineKeyboardMarkup

# --- Настройки пакетов для покупки ---
PACKAGES = {
    10: 350,
    25: 787,
    60: 1989
}

# --- Настройки комнат ---
ROOM_TYPES = {
    "living_room": "Гостиная",
    "bedroom": "Спальня",
    "kitchen": "Кухня",
    "dining_room": "Столовая",
    "home_office": "Кабинет",
    "bathroom_full": "Ванная",
    "toilet": "Санузел",
    "wardrobe": "Гардеробная",
    "nursery": "Детская (малыш)",
    "teen_room_boy": "Комната подростка (М)",
    "teen_room_girl": "Комната подростка (Ж)",
    "man_cave": "Мужская берлога",
}

# --- 16 стилей, 2 кнопки в ряд ---
STYLE_TYPES = [
    ("modern", "Современный"),
    ("minimalist", "Минимализм"),
    ("scandinavian", "Скандинавский"),
    ("industrial", "Индустриальный (лофт)"),
    ("rustic", "Рустик"),
    ("japandi", "Джапанди"),
    ("boho", "Бохо / Эклектика"),
    ("mediterranean", "Средиземноморский"),
    ("midcentury", "Mid‑century / винтаж"),
    ("artdeco", "Ар‑деко"),
    ("hitech", "Хай-тек"),
    ("classic", "Классический"),
    ("contemporary", "Контемпорари"),
    ("eclectic", "Эклектика"),
    ("transitional", "Переходный"),
    ("coastal", "Прибрежный"),
]


def get_main_menu_keyboard(is_admin: bool = False) -> InlineKeyboardMarkup:
    """Главное меню с кнопкой админ-панели для админов"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="                   🎨 Создать дизайн       "
                                          "                  ", callback_data="create_design"))
    builder.row(InlineKeyboardButton(text="               👤 Личный кабинет          "
                                          "                    ", callback_data="show_profile"))
    if is_admin:
        builder.row(InlineKeyboardButton(text="         ⚙️ Админ-панель        ", callback_data="admin_panel"))
    builder.adjust(1)
    return builder.as_markup()


def get_upload_photo_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура для экрана загрузки фото с кнопкой назад"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    builder.adjust(1)
    return builder.as_markup()



def get_profile_keyboard() -> InlineKeyboardMarkup:
    """Профиль с реферальными кнопками"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💳 Купить генерации", callback_data="buy_generations"))
    builder.row(
        InlineKeyboardButton(text="💸 Вывести деньги", callback_data="referral_request_payout"),
        InlineKeyboardButton(text="💎 Обменять на генерации", callback_data="referral_exchange_tokens")
    )
    builder.row(InlineKeyboardButton(text="⚙️ Реквизиты для выплат", callback_data="referral_setup_payment"))
    builder.row(InlineKeyboardButton(text="📊 История операций", callback_data="referral_history"))
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    builder.adjust(2)
    return builder.as_markup()

def get_room_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура выбора комнаты с кнопкой 'Очистить пространство'"""
    builder = InlineKeyboardBuilder()
    # Кнопка очистки пространства вверху на всю ширину
    builder.row(InlineKeyboardButton(text="🧽 Очистить пространство", callback_data="clear_space_confirm"))
    # Комнаты
    for key, text in ROOM_TYPES.items():
        builder.row(InlineKeyboardButton(text=text, callback_data=f"room_{key}"))
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    builder.adjust(2)
    return builder.as_markup()

def get_clear_space_confirm_keyboard() -> InlineKeyboardMarkup:
    """Клавиатура подтверждения очистки пространства"""
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="✅ Очистить", callback_data="clear_space_execute"))
    builder.row(InlineKeyboardButton(text="❌ Отмена", callback_data="clear_space_cancel"))
    builder.adjust(1)
    return builder.as_markup()

def get_style_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    # 16 стилей — 2 в ряд
    style_rows = [STYLE_TYPES[i:i+2] for i in range(0, len(STYLE_TYPES), 2)]
    for row in style_rows:
        buttons = [
            InlineKeyboardButton(text=style_name, callback_data=f"style_{style_key}")
            for style_key, style_name in row
        ]
        builder.row(*buttons)
    # Кнопка "К выбору комнаты" и "Главное меню" — отдельно
    builder.row(InlineKeyboardButton(text="⬅️ К выбору комнаты", callback_data="back_to_room"))
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    return builder.as_markup()

def get_payment_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for tokens, price in PACKAGES.items():
        button_text = f"{tokens} генераций - {price} руб."
        builder.row(InlineKeyboardButton(text=button_text, callback_data=f"pay_{tokens}_{price}"))
    builder.row(InlineKeyboardButton(text="⬅️ Назад в профиль", callback_data="show_profile"))
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    builder.adjust(1)
    return builder.as_markup()

def get_payment_check_keyboard(url: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="💰 Перейти к оплате", url=url))
    builder.row(InlineKeyboardButton(text="🔄 Я оплатил! (Проверить)", callback_data="check_payment"))
    builder.row(InlineKeyboardButton(text="⬅️ Назад в профиль", callback_data="show_profile"))
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    builder.adjust(1)
    return builder.as_markup()

def get_post_generation_keyboard() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.row(InlineKeyboardButton(text="🔄 Другой стиль для этого фото", callback_data="change_style"))
    builder.row(InlineKeyboardButton(text="📸 Загрузить новое фото", callback_data="create_design"))
    builder.row(InlineKeyboardButton(text="👤 Перейти в профиль", callback_data="show_profile"))
    builder.row(InlineKeyboardButton(text="🏠 Главное меню", callback_data="main_menu"))
    builder.adjust(1)
    return builder.as_markup()
