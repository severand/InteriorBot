# БЫСТРАЯ ШПАРГАЛКА РАЗРАБОТЧИКА InteriorBot

**Последнее обновление:** 2025-12-06

---

## 🔥 САМОЕ ВАЖНОЕ

### state.clear() vs state.set_state(None)

```python
# ✅ Навигация между меню
await state.set_state(None)

# ❌ НЕ ДЕЛАТЬ при навигации!
await state.clear()

# ✅ Только при /start или полном сбросе
await state.clear()
```

---

## 🎯 Золотое правило

**menu_message_id НЕ ДОЛЖЕН ТЕРЯТЬСЯ при навигации!**

---

## 🛠️ Редактирование меню

```python
# ✅ ВСЕГДА так
from utils.navigation import edit_menu

await edit_menu(
    callback=callback,
    state=state,
    text="Текст",
    keyboard=get_keyboard()
)

# ❌ НЕ делать так
await callback.message.edit_text(
    text="Текст",
    reply_markup=keyboard
)
```

---

## 📋 Шаблон обработчика меню

```python
@router.callback_query(F.data == "menu_name")
async def show_menu(callback: CallbackQuery, state: FSMContext):
    # 1. Сброс состояния (НЕ данных!)
    await state.set_state(None)
    
    # 2. Редактирование через edit_menu
    await edit_menu(
        callback=callback,
        state=state,
        text="Текст меню",
        keyboard=get_keyboard()
    )
    
    await callback.answer()
```

---

## 🔍 Быстрая отладка

```python
# Добавьте в начало функции
data = await state.get_data()
logger.warning(f"🔍 menu_id={data.get('menu_message_id')}")

# Если menu_id=None - ищите state.clear() выше по коду!
```

---

## ⚡ Частые ошибки

### ❌ Ошибка 1: state.clear() в навигации
```python
# НЕПРАВИЛЬНО
@router.callback_query(F.data == "settings")
async def show_settings(callback, state):
    await state.clear()  # ❌ Удалит menu_message_id!
```

**Исправление:**
```python
# ПРАВИЛЬНО
@router.callback_query(F.data == "settings")
async def show_settings(callback, state):
    await state.set_state(None)  # ✅ Сохранит menu_message_id!
```

### ❌ Ошибка 2: Прямое редактирование
```python
# НЕПРАВИЛЬНО
await callback.message.edit_text(...)  # ❌ Может потерять контекст
```

**Исправление:**
```python
# ПРАВИЛЬНО
await edit_menu(callback, state, text, keyboard)  # ✅ Безопасно
```

---

## 📚 Полная документация

См. [DEVELOPMENT_RULES.md](DEVELOPMENT_RULES.md) для детальных правил и примеров.

---

## 🤖 Для ИИ-ассистентов

**Перед любыми изменениями в навигации:**
1. Прочитайте DEVELOPMENT_RULES.md
2. Проверьте, что используете `state.set_state(None)` вместо `state.clear()`
3. Используйте только `edit_menu()` для редактирования
4. Добавьте логи для проверки

**Запомните:** `state.clear()` = враг навигации! 🚫
