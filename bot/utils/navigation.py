# bot/utils/navigation.py
# --- ОБНОВЛЕН: 2025-12-06 20:52 (ИСПРАВЛЕНИЕ: Сохранение menu_message_id) ---
# [2025-12-06 20:52] Исправлена потеря menu_message_id при переходе в главное меню из админ-панели
# Добавлено отображение баланса в функции edit_menu и show_main_menu
"""
Утилиты для навигации с единым меню.
Все переходы между экранами происходят через редактирование одного сообщения.
"""

import logging
from aiogram.types import CallbackQuery, InlineKeyboardMarkup
from aiogram.fsm.context import FSMContext
from aiogram.exceptions import TelegramBadRequest

from utils.helpers import add_balance_to_text  # НОВЫЙ ИМПОРТ для отображения баланса

logger = logging.getLogger(__name__)


async def edit_menu(
    callback: CallbackQuery,
    state: FSMContext,
    text: str,
    keyboard: InlineKeyboardMarkup = None,
    parse_mode: str = "Markdown",
    show_balance: bool = True  # НОВЫЙ ПАРАМЕТР
) -> bool:
    """
    Универсальная функция редактирования единого меню.
    Всегда редактирует ОДНО сообщение - никаких новых сообщений.
    АВТОМАТИЧЕСКИ ДОБАВЛЯЕТ БАЛАНС к тексту.

    Args:
        callback: CallbackQuery объект
        state: FSMContext для получения menu_message_id
        text: Новый текст сообщения
        keyboard: Новая клавиатура (может быть None)
        parse_mode: Режим парсинга (по умолчанию Markdown)
        show_balance: Показывать ли баланс (по умолчанию True)

    Returns:
        bool: True если успешно отредактировано, False если создано новое
    """
    # Добавляем баланс к тексту если нужно
    if show_balance:
        user_id = callback.from_user.id
        text = await add_balance_to_text(text, user_id)

    data = await state.get_data()
    menu_message_id = data.get('menu_message_id')

    if not menu_message_id:
        # Fallback: если ID потерян, создаем новое и сохраняем
        logger.warning(f"Menu message ID lost for user {callback.from_user.id}, creating new message")
        new_msg = await callback.message.answer(
            text=text,
            reply_markup=keyboard,
            parse_mode=parse_mode
        )
        await state.update_data(menu_message_id=new_msg.message_id)
        return False

    try:
        # Основной путь: редактируем существующее сообщение
        await callback.message.bot.edit_message_text(
            chat_id=callback.message.chat.id,
            message_id=menu_message_id,
            text=text,
            reply_markup=keyboard,
            parse_mode=parse_mode
        )
        logger.debug(f"✅ Menu edited successfully (msg_id={menu_message_id})")
        return True

    except TelegramBadRequest as e:
        # Если текст не изменился или другая ошибка
        if "message is not modified" in str(e).lower():
            logger.debug(f"Menu text unchanged (msg_id={menu_message_id})")
            return True

        logger.error(f"Failed to edit menu message: {e}")
        # Создаем новое сообщение как fallback
        new_msg = await callback.message.answer(
            text=text,
            reply_markup=keyboard,
            parse_mode=parse_mode
        )
        await state.update_data(menu_message_id=new_msg.message_id)
        return False

    except Exception as e:
        logger.error(f"Unexpected error editing menu: {e}")
        return False


async def show_main_menu(callback: CallbackQuery, state: FSMContext, admins: list[int]):
    """
    Показать главное меню.
    КРИТИЧНО: СОХРАНЯЕТ menu_message_id перед любыми операциями!
    Просто сбрасывает состояние и редактирует уже существующее меню.
    """
    from keyboards.inline import get_main_menu_keyboard
    from utils.texts import START_TEXT

    user_id = callback.from_user.id

    # ✅ КРИТИЧЕСКОЕ ИСПРАВЛЕНИЕ: Сохраняем menu_message_id ПЕРЕД любыми действиями
    data = await state.get_data()
    menu_message_id = data.get('menu_message_id')
    photo_message_id = data.get('photo_message_id')
    design_generated = data.get('design_generated', False)

    logger.info(f"🏠 [MAIN MENU] BEFORE: photo={photo_message_id}, design={design_generated}, menu_id={menu_message_id}")
    logger.debug(f"🏠 Returning to main menu for user {user_id}")

    # Сбрасываем ТОЛЬКО состояние FSM
    await state.set_state(None)

    # ✅ ВОССТАНАВЛИВАЕМ menu_message_id СРАЗУ после сброса состояния
    if menu_message_id:
        await state.update_data(menu_message_id=menu_message_id)
        logger.debug(f"✅ menu_message_id restored: {menu_message_id}")

    # Текст с балансом
    text = await add_balance_to_text(START_TEXT, user_id)

    # Пытаемся отредактировать текущее меню
    await edit_menu(
        callback=callback,
        state=state,
        text=text,
        keyboard=get_main_menu_keyboard(is_admin=user_id in admins),
        show_balance=False  # баланс уже в тексте
    )

    await callback.answer()


async def update_menu_after_photo(
    message,
    state: FSMContext,
    text: str,
    keyboard: InlineKeyboardMarkup,
    parse_mode: str = "Markdown"
) -> bool:
    """
    Обновление меню после загрузки фото пользователем.
    Используется в message handlers, а не callback handlers.

    Args:
        message: Message объект (сообщение с фото)
        state: FSMContext
        text: Новый текст меню
        keyboard: Новая клавиатура
        parse_mode: Режим парсинга

    Returns:
        bool: True если успешно
    """
    data = await state.get_data()
    menu_message_id = data.get('menu_message_id')

    if not menu_message_id:
        logger.warning(f"Menu message ID not found for user {message.from_user.id}")
        return False

    try:
        await message.bot.edit_message_text(
            chat_id=message.chat.id,
            message_id=menu_message_id,
            text=text,
            reply_markup=keyboard,
            parse_mode=parse_mode
        )
        logger.debug(f"✅ Menu updated after photo upload (msg_id={menu_message_id})")
        return True

    except TelegramBadRequest as e:
        logger.error(f"Failed to update menu after photo: {e}")
        return False

    except Exception as e:
        logger.error(f"Unexpected error updating menu: {e}")
        return False
