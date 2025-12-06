# bot/database/models.py
# --- ОБНОВЛЕН: 2025-12-04 11:35 - Добавлены таблицы admin_notifications и user_sources ---
"""SQL queries for database initialization"""

# ===== СУЩЕСТВУЮЩИЕ ТАБЛИЦЫ =====

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    balance INTEGER DEFAULT 3,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,


    -- Реферальные поля
    referral_code TEXT UNIQUE,
    referred_by INTEGER,
    referrals_count INTEGER DEFAULT 0,

    -- Финансовые поля
    referral_balance INTEGER DEFAULT 0,
    referral_total_earned INTEGER DEFAULT 0,
    referral_total_paid INTEGER DEFAULT 0,

    -- Реквизиты для выплат
    payment_method TEXT,
    payment_details TEXT,
    sbp_bank TEXT,

    -- Статистика
    total_generations INTEGER DEFAULT 0,
    successful_payments INTEGER DEFAULT 0,
    total_spent INTEGER DEFAULT 0,
    last_activity DATETIME DEFAULT CURRENT_TIMESTAMP,

    FOREIGN KEY (referred_by) REFERENCES users (user_id)
)
"""

CREATE_PAYMENTS_TABLE = """
CREATE TABLE IF NOT EXISTS payments (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    yookassa_payment_id TEXT UNIQUE NOT NULL,
    amount INTEGER NOT NULL,
    tokens INTEGER NOT NULL,
    status TEXT DEFAULT 'pending',
    payment_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
)
"""

# ===== ТАБЛИЦЫ ДЛЯ ОТСЛЕЖИВАНИЯ АКТИВНОСТИ =====

# Таблица генераций
CREATE_GENERATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS generations (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    room_type TEXT NOT NULL,
    style_type TEXT NOT NULL,
    operation_type TEXT DEFAULT 'design',
    success BOOLEAN DEFAULT 1,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
)
"""

# Таблица активности (для отслеживания активных пользователей)
CREATE_USER_ACTIVITY_TABLE = """
CREATE TABLE IF NOT EXISTS user_activity (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    action_type TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
)
"""

# ===== ТАБЛИЦЫ АДМИН-ФУНКЦИЙ (НОВОЕ) =====

# Настройки уведомлений для администраторов
CREATE_ADMIN_NOTIFICATIONS_TABLE = """
CREATE TABLE IF NOT EXISTS admin_notifications (
    admin_id INTEGER PRIMARY KEY,
    notify_new_users INTEGER DEFAULT 1,
    notify_new_payments INTEGER DEFAULT 1,
    notify_critical_errors INTEGER DEFAULT 1
)
"""

# Источники трафика (откуда пришел пользователь)
CREATE_USER_SOURCES_TABLE = """
CREATE TABLE IF NOT EXISTS user_sources (
    user_id INTEGER PRIMARY KEY,
    source TEXT NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
)
"""

# ===== ТАБЛИЦЫ РЕФЕРАЛЬНОЙ СИСТЕМЫ =====

CREATE_REFERRAL_EARNINGS_TABLE = """
CREATE TABLE IF NOT EXISTS referral_earnings (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    referrer_id INTEGER NOT NULL,
    referred_id INTEGER NOT NULL,
    payment_id TEXT NOT NULL,
    amount INTEGER NOT NULL,
    commission_percent INTEGER NOT NULL,
    earnings INTEGER NOT NULL,
    tokens_given INTEGER NOT NULL,
    status TEXT DEFAULT 'credited',
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (referrer_id) REFERENCES users (user_id),
    FOREIGN KEY (referred_id) REFERENCES users (user_id)
)
"""

CREATE_REFERRAL_EXCHANGES_TABLE = """
CREATE TABLE IF NOT EXISTS referral_exchanges (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount INTEGER NOT NULL,
    tokens INTEGER NOT NULL,
    exchange_rate INTEGER NOT NULL,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
)
"""

CREATE_REFERRAL_PAYOUTS_TABLE = """
CREATE TABLE IF NOT EXISTS referral_payouts (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    user_id INTEGER NOT NULL,
    amount INTEGER NOT NULL,
    payment_method TEXT,
    payment_details TEXT,
    status TEXT DEFAULT 'pending',
    admin_note TEXT,
    requested_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    processed_at DATETIME,
    processed_by INTEGER,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
)
"""

CREATE_SETTINGS_TABLE = """
CREATE TABLE IF NOT EXISTS settings (
    key TEXT PRIMARY KEY,
    value TEXT NOT NULL
)
"""

# ===== ДЕФОЛТНЫЕ НАСТРОЙКИ =====

DEFAULT_SETTINGS = {
    'welcome_bonus': '3',
    'referral_bonus_inviter': '2',
    'referral_bonus_invited': '2',
    'referral_enabled': '1',
    'referral_commission_percent': '10',
    'referral_min_payout': '500',
    'referral_exchange_rate': '29',
}

# ===== SQL QUERIES ДЛЯ CRUD ОПЕРАЦИЙ =====

# --- Пользователи ---
GET_USER = "SELECT * FROM users WHERE user_id = ?"
CREATE_USER = "INSERT INTO users (user_id, username, balance, referral_code) VALUES (?, ?, ?, ?)"
UPDATE_BALANCE = "UPDATE users SET balance = balance + ? WHERE user_id = ?"
DECREASE_BALANCE = "UPDATE users SET balance = balance - 1 WHERE user_id = ?"
GET_BALANCE = "SELECT balance FROM users WHERE user_id = ?"
UPDATE_LAST_ACTIVITY = "UPDATE users SET last_activity = CURRENT_TIMESTAMP WHERE user_id = ?"

# --- Реферальные коды ---
UPDATE_REFERRAL_CODE = "UPDATE users SET referral_code = ? WHERE user_id = ?"
GET_USER_BY_REFERRAL_CODE = "SELECT * FROM users WHERE referral_code = ?"
UPDATE_REFERRED_BY = "UPDATE users SET referred_by = ? WHERE user_id = ?"
INCREMENT_REFERRALS_COUNT = "UPDATE users SET referrals_count = referrals_count + 1 WHERE user_id = ?"

# --- Платежи ---
CREATE_PAYMENT = """
INSERT INTO payments (user_id, yookassa_payment_id, amount, tokens, status)
VALUES (?, ?, ?, ?, ?)
"""
GET_PENDING_PAYMENT = """
SELECT * FROM payments 
WHERE user_id = ? AND status = 'pending' 
ORDER BY created_at DESC LIMIT 1
"""
UPDATE_PAYMENT_STATUS = """
UPDATE payments 
SET status = ?, payment_date = CURRENT_TIMESTAMP
WHERE yookassa_payment_id = ?
"""

# --- Генерации ---
CREATE_GENERATION = """
INSERT INTO generations (user_id, room_type, style_type, operation_type, success)
VALUES (?, ?, ?, ?, ?)
"""
INCREMENT_TOTAL_GENERATIONS = "UPDATE users SET total_generations = total_generations + 1 WHERE user_id = ?"

# --- Активность ---
LOG_USER_ACTIVITY = """
INSERT INTO user_activity (user_id, action_type)
VALUES (?, ?)
"""

# --- Реферальный баланс ---
GET_REFERRAL_BALANCE = "SELECT referral_balance FROM users WHERE user_id = ?"
ADD_REFERRAL_BALANCE = "UPDATE users SET referral_balance = referral_balance + ?, referral_total_earned = referral_total_earned + ? WHERE user_id = ?"
DECREASE_REFERRAL_BALANCE = "UPDATE users SET referral_balance = referral_balance - ? WHERE user_id = ?"
UPDATE_TOTAL_PAID = "UPDATE users SET referral_total_paid = referral_total_paid + ? WHERE user_id = ?"

# --- Реферальные начисления ---
CREATE_REFERRAL_EARNING = """
INSERT INTO referral_earnings (referrer_id, referred_id, payment_id, amount, commission_percent, earnings, tokens_given)
VALUES (?, ?, ?, ?, ?, ?, ?)
"""
GET_USER_REFERRAL_EARNINGS = """
SELECT * FROM referral_earnings 
WHERE referrer_id = ? 
ORDER BY created_at DESC 
LIMIT ?
"""

# --- Обмены ---
CREATE_REFERRAL_EXCHANGE = """
INSERT INTO referral_exchanges (user_id, amount, tokens, exchange_rate)
VALUES (?, ?, ?, ?)
"""
GET_USER_EXCHANGES = """
SELECT * FROM referral_exchanges 
WHERE user_id = ? 
ORDER BY created_at DESC 
LIMIT ?
"""

# --- Выплаты ---
CREATE_PAYOUT_REQUEST = """
INSERT INTO referral_payouts (user_id, amount, payment_method, payment_details)
VALUES (?, ?, ?, ?)
"""
GET_USER_PAYOUTS = """
SELECT * FROM referral_payouts 
WHERE user_id = ? 
ORDER BY requested_at DESC 
LIMIT ?
"""
GET_PENDING_PAYOUTS = """
SELECT * FROM referral_payouts 
WHERE status = 'pending' 
ORDER BY requested_at ASC
"""
UPDATE_PAYOUT_STATUS = """
UPDATE referral_payouts 
SET status = ?, processed_at = CURRENT_TIMESTAMP, processed_by = ?, admin_note = ?
WHERE id = ?
"""

# --- Реквизиты ---
SET_PAYMENT_DETAILS = """
UPDATE users 
SET payment_method = ?, payment_details = ?, sbp_bank = ?
WHERE user_id = ?
"""
GET_PAYMENT_DETAILS = """
SELECT payment_method, payment_details, sbp_bank 
FROM users 
WHERE user_id = ?
"""

# --- Настройки ---
GET_SETTING = "SELECT value FROM settings WHERE key = ?"
SET_SETTING = "INSERT OR REPLACE INTO settings (key, value) VALUES (?, ?)"
GET_ALL_SETTINGS = "SELECT key, value FROM settings"
