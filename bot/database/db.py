import aiosqlite
from typing import Optional, Dict, Any

# ИСПРАВЛЕНО: Импортируем config из папки bot (абсолютный импорт)
from config import config

from database.models import (
    CREATE_USERS_TABLE, CREATE_PAYMENTS_TABLE,
    GET_USER, CREATE_USER, UPDATE_BALANCE, DECREASE_BALANCE,
    GET_BALANCE, CREATE_PAYMENT, GET_PENDING_PAYMENT, UPDATE_PAYMENT_STATUS
)


class Database:
    """Async database operations handler"""

    def __init__(self, db_path: str):
        self.db_path = db_path

    async def init_db(self):
        """Initialize database with required tables"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(CREATE_USERS_TABLE)
            await db.execute(CREATE_PAYMENTS_TABLE)
            await db.commit()

    async def get_user(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user by ID"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(GET_USER, (user_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
                return None

    async def create_user(self, user_id: int, username: Optional[str] = None) -> bool:
        """Create new user if not exists"""
        user_exists = await self.get_user(user_id)
        if user_exists:
            return False

        # Используем FREE_GENERATIONS из config
        initial_balance = config.FREE_GENERATIONS

        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(CREATE_USER, (user_id, username, initial_balance))
            await db.commit()
            return True

    async def get_balance(self, user_id: int) -> int:
        """Get user's current balance"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(GET_BALANCE, (user_id,)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def increase_balance(self, user_id: int, amount: int) -> bool:
        """Increase user's balance"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(UPDATE_BALANCE, (amount, user_id))
            await db.commit()
            return True

    async def decrease_balance(self, user_id: int) -> bool:
        """Decrease user's balance by 1"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(DECREASE_BALANCE, (user_id,))
            await db.commit()
            return True

    async def create_payment(self, user_id: int, payment_id: str,
                             amount: int, tokens: int) -> bool:
        """Create new payment record"""
        try:
            async with aiosqlite.connect(self.db_path) as db:
                await db.execute(CREATE_PAYMENT,
                                 (user_id, payment_id, amount, tokens, 'pending'))
                await db.commit()
                return True
        except Exception:
            return False

    async def get_pending_payment(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Get user's last pending payment"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(GET_PENDING_PAYMENT, (user_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
                return None

    # Добавлены методы для payments.py, которых не хватало в твоем коде
    async def get_last_pending_payment(self, user_id: int):
        return await self.get_pending_payment(user_id)

    async def set_payment_success(self, payment_id: str) -> bool:
        return await self.update_payment_status(payment_id, 'succeeded')

    async def add_tokens(self, user_id: int, tokens: int) -> bool:
        return await self.increase_balance(user_id, tokens)

    async def get_user_data(self, user_id: int):
        return await self.get_user(user_id)

    async def update_payment_status(self, payment_id: str, status: str) -> bool:
        """Update payment status"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(UPDATE_PAYMENT_STATUS, (status, payment_id))
            await db.commit()
            return True


# Инициализация БД
db = Database(config.DB_PATH)