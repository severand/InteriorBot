from aiogram.fsm.state import StatesGroup, State

# Класс состояний для процесса генерации дизайна
class CreationStates(StatesGroup):
    # 1. Ждем фотографию комнаты от пользователя
    waiting_for_photo = State()

    # 2. Ждем, когда пользователь выберет тип комнаты (спальня, гостиная и т.д.)
    choose_room = State()

    # 3. Ждем, когда пользователь выберет стиль (скандинавский, хай-тек и т.д.)
    choose_style = State()


# Класс состояний для админ-панели
class AdminStates(StatesGroup):
    """Состояния админ-панели"""
    waiting_for_user_id = State()
    adding_balance = State()
    removing_balance = State()
    setting_balance = State()


# Класс состояний для реферальной системы
class ReferralStates(StatesGroup):
    """Состояния для реферальной системы"""
    entering_payout_amount = State()      # Ввод суммы выплаты
    entering_exchange_amount = State()    # Ввод количества генераций для обмена
    entering_card_number = State()        # Ввод номера карты
    entering_yoomoney = State()           # Ввод YooMoney
    entering_phone = State()              # Ввод телефона для СБП
    entering_other_method = State()       # Ввод другого способа


# Класс состояний для других процессов
class OtherStates(StatesGroup):
    pass
