"""SQL queries for database initialization"""

CREATE_USERS_TABLE = """
CREATE TABLE IF NOT EXISTS users (
    user_id INTEGER PRIMARY KEY,
    username TEXT,
    balance INTEGER DEFAULT 3,
    reg_date DATETIME DEFAULT CURRENT_TIMESTAMP
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
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (user_id) REFERENCES users (user_id)
)
"""

# SQL queries for CRUD operations
GET_USER = "SELECT * FROM users WHERE user_id = ?"
CREATE_USER = "INSERT INTO users (user_id, username, balance) VALUES (?, ?, ?)"
UPDATE_BALANCE = "UPDATE users SET balance = balance + ? WHERE user_id = ?"
DECREASE_BALANCE = "UPDATE users SET balance = balance - 1 WHERE user_id = ?"
GET_BALANCE = "SELECT balance FROM users WHERE user_id = ?"

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
SET status = ? 
WHERE yookassa_payment_id = ?
"""

