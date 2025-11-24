# --- Новый код: keyboards/reply.py ----
from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

# --- Ключи для заголовков (уникальные, без эмодзи, с разделителями) ---
TITLE_MAIN = "--- 📌 ГЛАВНОЕ МЕНЮ 📌 ---"
TITLE_PROFILE = "--- ВАШ ПРОФИЛЬ ---"
TITLE_ROOM_SELECT = "=== 👇 ВЫБЕРИТЕ КОМНАТУ 👇 ==="
TITLE_STYLE_SELECT = "=== 👇 ВЫБЕРИТЕ СТИЛЬ 👇 ==="


# --- Меню для навигации (Главное, Профиль) ---

def get_main_reply_keyboard() -> ReplyKeyboardMarkup:
    """Главное нижнее меню: Заголовок + 'Создать дизайн' и 'Профиль'."""
    buttons = [
        [
            KeyboardButton(text=TITLE_MAIN)  # Заголовок
        ],
        [
            KeyboardButton(text="🛠️ Создать дизайн"),
            KeyboardButton(text="👤 Профиль")
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def get_profile_reply_keyboard() -> ReplyKeyboardMarkup:
    """Меню профиля: Заголовок + 'Купить генерации' и 'Меню'."""
    buttons = [
        [
            KeyboardButton(text=TITLE_PROFILE)  # Заголовок
        ],
        [
            KeyboardButton(text="💰 Купить генерации"),
            KeyboardButton(text="🏠 Меню")
        ]
    ]
    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


# --- Меню для выбора комнаты/стиля (Шаги генерации) ---

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


def get_room_selection_reply_keyboard() -> ReplyKeyboardMarkup:
    """Меню для выбора типа комнаты: Заголовок + Комнаты."""
    buttons = [
        [
            KeyboardButton(text=TITLE_ROOM_SELECT)  # Заголовок
        ]
    ]
    # Добавляем комнаты (2 кнопки в ряд)
    room_keys = list(ROOM_TYPES.keys())
    for i in range(0, len(room_keys), 2):
        row = []
        for key in room_keys[i:i + 2]:
            row.append(KeyboardButton(text=ROOM_TYPES[key]))
        buttons.append(row)

    # Кнопка Назад
    buttons.append([KeyboardButton(text="⬅️ Назад")])

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)


def get_style_selection_reply_keyboard() -> ReplyKeyboardMarkup:
    """Меню для выбора стиля дизайна: Заголовок + Стили."""
    buttons = [
        [
            KeyboardButton(text=TITLE_STYLE_SELECT)  # Заголовок
        ]
    ]
    # Добавляем стили (2 кнопки в ряд)
    style_keys = list(STYLE_TYPES.keys())
    for i in range(0, len(style_keys), 2):
        row = []
        for key in style_keys[i:i + 2]:
            row.append(KeyboardButton(text=STYLE_TYPES[key]))
        buttons.append(row)

    # Кнопка Назад
    buttons.append([KeyboardButton(text="⬅️ Назад")])

    return ReplyKeyboardMarkup(keyboard=buttons, resize_keyboard=True)