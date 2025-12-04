# bot/database/db.py
# --- ОБНОВЛЕН: 2025-12-04 11:36 - Добавлены методы для уведомлений и источников трафика ---
# Добавлены методы get_user_recent_payments и get_referrer_info для расширенного поиска

import aiosqlite
import logging
import secrets
from typing import Optional, Dict, Any, List, Tuple
from datetime import datetime, timedelta

from database.models import (
    # Таблицы
    CREATE_USERS_TABLE, CREATE_PAYMENTS_TABLE,
    CREATE_REFERRAL_EARNINGS_TABLE, CREATE_REFERRAL_EXCHANGES_TABLE,
    CREATE_REFERRAL_PAYOUTS_TABLE, CREATE_SETTINGS_TABLE,
    CREATE_GENERATIONS_TABLE, CREATE_USER_ACTIVITY_TABLE,
    CREATE_ADMIN_NOTIFICATIONS_TABLE, CREATE_USER_SOURCES_TABLE,
    DEFAULT_SETTINGS,
    # Пользователи
    GET_USER, CREATE_USER, UPDATE_BALANCE, DECREASE_BALANCE, GET_BALANCE, UPDATE_LAST_ACTIVITY,
    # Реферальные коды
    UPDATE_REFERRAL_CODE, GET_USER_BY_REFERRAL_CODE, UPDATE_REFERRED_BY, INCREMENT_REFERRALS_COUNT,
    # Платежи
    CREATE_PAYMENT, GET_PENDING_PAYMENT, UPDATE_PAYMENT_STATUS,
    # Генерации
    CREATE_GENERATION, INCREMENT_TOTAL_GENERATIONS,
    # Активность
    LOG_USER_ACTIVITY,
    # Реферальный баланс
    GET_REFERRAL_BALANCE, ADD_REFERRAL_BALANCE, DECREASE_REFERRAL_BALANCE, UPDATE_TOTAL_PAID,
    # Реферальные начисления
    CREATE_REFERRAL_EARNING, GET_USER_REFERRAL_EARNINGS,
    # Обмены
    CREATE_REFERRAL_EXCHANGE, GET_USER_EXCHANGES,
    # Выплаты
    CREATE_PAYOUT_REQUEST, GET_USER_PAYOUTS, GET_PENDING_PAYOUTS, UPDATE_PAYOUT_STATUS,
    # Реквизиты
    SET_PAYMENT_DETAILS, GET_PAYMENT_DETAILS,
    # Настройки
    GET_SETTING, SET_SETTING, GET_ALL_SETTINGS
)

logger = logging.getLogger(__name__)


class Database:
    def __init__(self, db_path: str = "bot.db"):
        self.db_path = db_path

    async def init_db(self):
        """Инициализация таблиц БД"""
        async with aiosqlite.connect(self.db_path) as db:
            # Создаем все таблицы
            await db.execute(CREATE_USERS_TABLE)
            await db.execute(CREATE_PAYMENTS_TABLE)
            await db.execute(CREATE_GENERATIONS_TABLE)
            await db.execute(CREATE_USER_ACTIVITY_TABLE)
            await db.execute(CREATE_ADMIN_NOTIFICATIONS_TABLE)
            await db.execute(CREATE_USER_SOURCES_TABLE)
            await db.execute(CREATE_REFERRAL_EARNINGS_TABLE)
            await db.execute(CREATE_REFERRAL_EXCHANGES_TABLE)
            await db.execute(CREATE_REFERRAL_PAYOUTS_TABLE)
            await db.execute(CREATE_SETTINGS_TABLE)
            
            # Инициализируем дефолтные настройки
            for key, value in DEFAULT_SETTINGS.items():
                await db.execute("INSERT OR IGNORE INTO settings (key, value) VALUES (?, ?)", (key, value))
            
            await db.commit()
            logger.info("База данных инициализирована")

    # ===== ПОЛЬЗОВАТЕЛИ =====

    async def create_user(self, user_id: int, username: str = None, referrer_code: str = None) -> bool:
        """Создать нового пользователя с реферальным кодом"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                # Проверяем, есть ли уже пользователь
                async with db.execute(GET_USER, (user_id,)) as cursor:
                    existing = await cursor.fetchone()
                    if existing:
                        return False
                
                # Генерируем уникальный реферальный код
                ref_code = secrets.token_urlsafe(8)
                
                # Получаем начальный бонус
                initial_balance = int(await self.get_setting('welcome_bonus') or '3')
                
                # Создаем пользователя
                await db.execute(CREATE_USER, (user_id, username, initial_balance, ref_code))
                
                # Обрабатываем реферальную систему
                if referrer_code:
                    await self._process_referral(db, user_id, referrer_code)
                
                await db.commit()
                logger.info(f"Пользователь {user_id} создан с реф. кодом {ref_code}")
                return True
            except Exception as e:
                logger.error(f"Ошибка создания пользователя: {e}")
                return False

    async def _process_referral(self, db: aiosqlite.Connection, user_id: int, referrer_code: str):
        """Обработка реферальной системы при регистрации"""
        try:
            # Находим реферера
            async with db.execute(GET_USER_BY_REFERRAL_CODE, (referrer_code,)) as cursor:
                referrer = await cursor.fetchone()
                if not referrer:
                    return
            
            referrer_id = referrer[0]
            
            # Связываем пользователя с реферером
            await db.execute(UPDATE_REFERRED_BY, (referrer_id, user_id))
            
            # Увеличиваем счетчик рефералов
            await db.execute(INCREMENT_REFERRALS_COUNT, (referrer_id,))
            
            # Начисляем бонусы
            inviter_bonus = int(await self.get_setting('referral_bonus_inviter') or '2')
            invited_bonus = int(await self.get_setting('referral_bonus_invited') or '2')
            
            await db.execute(UPDATE_BALANCE, (inviter_bonus, referrer_id))
            await db.execute(UPDATE_BALANCE, (invited_bonus, user_id))
            
            logger.info(f"Реферал: {referrer_id} пригласил {user_id}")
        except Exception as e:
            logger.error(f"Ошибка обработки реферала: {e}")

    async def get_user_data(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получить данные пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(GET_USER, (user_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
                return None

    async def get_balance(self, user_id: int) -> int:
        """Получить баланс генераций"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(GET_BALANCE, (user_id,)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def decrease_balance(self, user_id: int) -> bool:
        """Уменьшить баланс на 1"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(DECREASE_BALANCE, (user_id,))
                await db.commit()
                return True
            except Exception as e:
                logger.error(f"Ошибка уменьшения баланса: {e}")
                return False

    async def add_tokens(self, user_id: int, tokens: int) -> bool:
        """Добавить генерации"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(UPDATE_BALANCE, (tokens, user_id))
                await db.commit()
                logger.info(f"Добавлено {tokens} генераций пользователю {user_id}")
                return True
            except Exception as e:
                logger.error(f"Ошибка добавления токенов: {e}")
                return False

    # ===== ПЛАТЕЖИ =====

    async def create_payment(self, payment_id: str, user_id: int, amount: int, tokens: int) -> bool:
        """Создать запись о платеже"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(CREATE_PAYMENT, (user_id, payment_id, amount, tokens, 'pending'))
                await db.commit()
                return True
            except Exception as e:
                logger.error(f"Ошибка создания платежа: {e}")
                return False

    async def update_payment_status(self, payment_id: str, status: str) -> bool:
        """Обновить статус платежа"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(UPDATE_PAYMENT_STATUS, (status, payment_id))
                await db.commit()
                return True
            except Exception as e:
                logger.error(f"Ошибка обновления статуса платежа: {e}")
                return False

    async def get_payment(self, payment_id: str) -> Optional[Dict[str, Any]]:
        """Получить информацию о платеже"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute("SELECT * FROM payments WHERE yookassa_payment_id = ?", (payment_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
                return None

    async def get_last_pending_payment(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получить последний ожидающий платеж"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(GET_PENDING_PAYMENT, (user_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
                return None

    async def set_payment_success(self, payment_id: str) -> bool:
        """Отметить платеж как успешный"""
        return await self.update_payment_status(payment_id, 'succeeded')

    # ===== ГЕНЕРАЦИИ =====

    async def log_generation(self, user_id: int, room_type: str, style_type: str, 
                            operation_type: str = 'design', success: bool = True) -> bool:
        """
        Залогировать генерацию.
        Параметры:
        - user_id: ID пользователя
        - room_type: тип комнаты (напр. 'гостиная', 'кухня')
        - style_type: стиль (напр. 'минимализм', 'лофт')
        - operation_type: тип операции ('design' или др.)
        - success: успешность генерации
        """
        async with aiosqlite.connect(self.db_path) as db:
            try:
                # Логируем в таблицу generations
                await db.execute(CREATE_GENERATION, (user_id, room_type, style_type, operation_type, success))
                
                # Увеличиваем счетчик в таблице users
                await db.execute(INCREMENT_TOTAL_GENERATIONS, (user_id,))
                
                # Обновляем время последней активности
                await db.execute(UPDATE_LAST_ACTIVITY, (user_id,))
                
                await db.commit()
                logger.info(f"Генерация: user={user_id}, room={room_type}, style={style_type}")
                return True
            except Exception as e:
                logger.error(f"Ошибка логирования генерации: {e}")
                return False

    async def get_total_generations(self) -> int:
        """Общее количество генераций"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM generations") as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def get_generations_count(self, days: int = 1) -> int:
        """Количество генераций за период"""
        date_threshold = datetime.now() - timedelta(days=days)
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM generations WHERE created_at >= ?",
                (date_threshold.isoformat(),)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def get_failed_generations_count(self, days: int = 1) -> int:
        """
        Количество неудачных генераций за период.
        Параметры:
        - days: количество дней назад (1 = за сегодня, 7 = за неделю)
        """
        date_threshold = datetime.now() - timedelta(days=days)
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM generations WHERE success = 0 AND created_at >= ?",
                (date_threshold.isoformat(),)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def get_conversion_rate(self) -> float:
        """
        Рассчитать конверсию (генераций на пользователя).
        Возвращает среднее количество генераций на пользователя.
        """
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT AVG(total_generations) FROM users WHERE total_generations > 0"
            ) as cursor:
                row = await cursor.fetchone()
                return round(row[0], 2) if row and row[0] else 0.0

    async def get_popular_rooms(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получить популярные типы комнат"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT room_type, COUNT(*) as count
                FROM generations
                GROUP BY room_type
                ORDER BY count DESC
                LIMIT ?
                """,
                (limit,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [{'room_type': row[0], 'count': row[1]} for row in rows]

    async def get_popular_styles(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Получить популярные стили"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT style_type, COUNT(*) as count
                FROM generations
                GROUP BY style_type
                ORDER BY count DESC
                LIMIT ?
                """,
                (limit,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [{'style_type': row[0], 'count': row[1]} for row in rows]

    # ===== АКТИВНОСТЬ =====

    async def log_activity(self, user_id: int, action_type: str) -> bool:
        """
        Залогировать активность пользователя.
        Параметры:
        - user_id: ID пользователя
        - action_type: тип действия (напр. 'start', 'generation', 'payment', 'referral')
        """
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(LOG_USER_ACTIVITY, (user_id, action_type))
                await db.execute(UPDATE_LAST_ACTIVITY, (user_id,))
                await db.commit()
                return True
            except Exception as e:
                logger.error(f"Ошибка логирования активности: {e}")
                return False

    async def get_active_users_count(self, days: int = 1) -> int:
        """
        Количество активных пользователей за период.
        Активным считается пользователь, который совершил любое действие.
        """
        date_threshold = datetime.now() - timedelta(days=days)
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT COUNT(DISTINCT user_id) FROM user_activity WHERE created_at >= ?",
                (date_threshold.isoformat(),)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    # ===== УВЕДОМЛЕНИЯ АДМИНОВ (НОВОЕ) =====

    async def get_admin_notifications(self, admin_id: int) -> Dict[str, Any]:
        """
        Получить настройки уведомлений для админа.
        Возвращает словарь с флагами уведомлений.
        """
        query = """
            SELECT admin_id, notify_new_users, notify_new_payments, notify_critical_errors
            FROM admin_notifications
            WHERE admin_id = ?
        """
        async with aiosqlite.connect(self.db_path) as conn:
            async with conn.execute(query, (admin_id,)) as cursor:
                row = await cursor.fetchone()
                if not row:
                    # Если запись не создана – по умолчанию все включено
                    return {
                        "admin_id": admin_id,
                        "notify_new_users": 1,
                        "notify_new_payments": 1,
                        "notify_critical_errors": 1,
                    }
                return {
                    "admin_id": row[0],
                    "notify_new_users": row[1],
                    "notify_new_payments": row[2],
                    "notify_critical_errors": row[3],
                }

    async def set_admin_notifications(self, admin_id: int, notify_new_users: int, 
                                     notify_new_payments: int, notify_critical_errors: int) -> None:
        """
        Установить настройки уведомлений для админа.
        """
        query = """
            INSERT INTO admin_notifications (admin_id, notify_new_users, notify_new_payments, notify_critical_errors)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(admin_id) DO UPDATE SET
                notify_new_users = excluded.notify_new_users,
                notify_new_payments = excluded.notify_new_payments,
                notify_critical_errors = excluded.notify_critical_errors
        """
        async with aiosqlite.connect(self.db_path) as conn:
            await conn.execute(query, (admin_id, notify_new_users, notify_new_payments, notify_critical_errors))
            await conn.commit()

    async def get_admins_for_notification(self, notify_field: str) -> List[int]:
        """
        Получить список админов, у которых включен определённый тип уведомлений.
        notify_field: 'notify_new_users' | 'notify_new_payments' | 'notify_critical_errors'
        Возвращает список admin_id.
        """
        if notify_field not in ("notify_new_users", "notify_new_payments", "notify_critical_errors"):
            raise ValueError("Invalid notify_field")

        query = f"""
            SELECT admin_id FROM admin_notifications
            WHERE {notify_field} = 1
        """
        async with aiosqlite.connect(self.db_path) as conn:
            async with conn.execute(query) as cursor:
                rows = await cursor.fetchall()
                return [r[0] for r in rows]

    # ===== ИСТОЧНИКИ ТРАФИКА (НОВОЕ) =====

    async def set_user_source(self, user_id: int, source: str) -> None:
        """
        Сохранить источник для пользователя, если еще не сохранен.
        """
        query_check = "SELECT 1 FROM user_sources WHERE user_id = ?"
        query_insert = "INSERT INTO user_sources (user_id, source) VALUES (?, ?)"
        async with aiosqlite.connect(self.db_path) as conn:
            async with conn.execute(query_check, (user_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return
            await conn.execute(query_insert, (user_id, source))
            await conn.commit()

    async def get_sources_stats(self) -> List[Dict[str, Any]]:
        """
        Получить статистику по источникам трафика.
        Возвращает список источников и количество пользователей с каждого из них.
        """
        query = """
            SELECT source, COUNT(*) as count
            FROM user_sources
            GROUP BY source
            ORDER BY count DESC
        """
        async with aiosqlite.connect(self.db_path) as conn:
            async with conn.execute(query) as cursor:
                rows = await cursor.fetchall()
                return [{"source": r[0], "count": r[1]} for r in rows]

    # ===== РЕФЕРАЛЬНЫЙ БАЛАНС =====

    async def get_referral_balance(self, user_id: int) -> int:
        """Получить реферальный баланс (рубли)"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(GET_REFERRAL_BALANCE, (user_id,)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def add_referral_balance(self, user_id: int, amount: int) -> bool:
        """Добавить к реферальному балансу"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(ADD_REFERRAL_BALANCE, (amount, amount, user_id))
                await db.commit()
                return True
            except Exception as e:
                logger.error(f"Ошибка добавления реф. баланса: {e}")
                return False

    async def decrease_referral_balance(self, user_id: int, amount: int) -> bool:
        """Уменьшить реферальный баланс"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(DECREASE_REFERRAL_BALANCE, (amount, user_id))
                await db.commit()
                return True
            except Exception as e:
                logger.error(f"Ошибка уменьшения реф. баланса: {e}")
                return False

    # ===== РЕФЕРАЛЬНЫЕ НАЧИСЛЕНИЯ =====

    async def log_referral_earning(self, referrer_id: int, referred_id: int, payment_id: str,
                                    amount: int, commission_percent: int, earnings: int, tokens: int) -> bool:
        """Залогировать заработок реферера"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(CREATE_REFERRAL_EARNING,
                                (referrer_id, referred_id, payment_id, amount, commission_percent, earnings, tokens))
                await db.commit()
                return True
            except Exception as e:
                logger.error(f"Ошибка логирования заработка: {e}")
                return False

    async def get_user_referral_earnings(self, user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """Получить историю заработков"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(GET_USER_REFERRAL_EARNINGS, (user_id, limit)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    # ===== ОБМЕНЫ =====

    async def log_referral_exchange(self, user_id: int, amount: int, tokens: int, exchange_rate: int) -> bool:
        """Залогировать обмен"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(CREATE_REFERRAL_EXCHANGE, (user_id, amount, tokens, exchange_rate))
                await db.commit()
                return True
            except Exception as e:
                logger.error(f"Ошибка логирования обмена: {e}")
                return False

    async def get_user_exchanges(self, user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """Получить историю обменов"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(GET_USER_EXCHANGES, (user_id, limit)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    # ===== ВЫПЛАТЫ =====

    async def create_payout_request(self, user_id: int, amount: int, payment_method: str, payment_details: str) -> int:
        """Создать заявку на выплату"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                cursor = await db.execute(CREATE_PAYOUT_REQUEST, (user_id, amount, payment_method, payment_details))
                await db.commit()
                return cursor.lastrowid
            except Exception as e:
                logger.error(f"Ошибка создания заявки на выплату: {e}")
                return 0

    async def get_user_payouts(self, user_id: int, limit: int = 20) -> List[Dict[str, Any]]:
        """Получить историю выплат"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(GET_USER_PAYOUTS, (user_id, limit)) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_pending_payouts(self) -> List[Dict[str, Any]]:
        """Получить все ожидающие выплаты"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(GET_PENDING_PAYOUTS) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def update_payout_status(self, payout_id: int, status: str, admin_id: int, note: str = None) -> bool:
        """Обновить статус выплаты"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(UPDATE_PAYOUT_STATUS, (status, admin_id, note, payout_id))
                await db.commit()
                return True
            except Exception as e:
                logger.error(f"Ошибка обновления статуса выплаты: {e}")
                return False

    # ===== РЕКВИЗИТЫ =====

    async def set_payment_details(self, user_id: int, method: str, details: str, sbp_bank: str = None) -> bool:
        """Установить реквизиты"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(SET_PAYMENT_DETAILS, (method, details, sbp_bank, user_id))
                await db.commit()
                return True
            except Exception as e:
                logger.error(f"Ошибка установки реквизитов: {e}")
                return False

    async def get_payment_details(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получить реквизиты"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(GET_PAYMENT_DETAILS, (user_id,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
                return None

    # ===== НАСТРОЙКИ =====

    async def get_setting(self, key: str) -> Optional[str]:
        """Получить настройку"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(GET_SETTING, (key,)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None

    async def set_setting(self, key: str, value: str) -> bool:
        """Установить настройку"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                await db.execute(SET_SETTING, (key, value))
                await db.commit()
                return True
            except Exception as e:
                logger.error(f"Ошибка установки настройки: {e}")
                return False

    # ===== СТАТИСТИКА =====

    async def get_total_users_count(self) -> int:
        """Общее количество пользователей"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM users") as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def get_new_users_count(self, days: int = 1) -> int:
        """Количество новых пользователей за период"""
        date_threshold = datetime.now() - timedelta(days=days)
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM users WHERE reg_date >= ?",
                (date_threshold.isoformat(),)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def get_total_revenue(self) -> int:
        """Общая выручка"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT SUM(amount) FROM payments WHERE status = 'succeeded'"
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row and row[0] else 0

    async def get_recent_users(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Последние пользователи"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                "SELECT * FROM users ORDER BY reg_date DESC LIMIT ?",
                (limit,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def search_user(self, query: str) -> Optional[Dict[str, Any]]:
        """
        Поиск пользователя по ID, username или реферальному коду.
        Возвращает полную информацию о пользователе.
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Пробуем поиск по ID (если запрос - цифры)
            if query.isdigit():
                user_id = int(query)
                async with db.execute(GET_USER, (user_id,)) as cursor:
                    row = await cursor.fetchone()
                    if row:
                        return dict(row)
            
            # Поиск по username (убираем @ если есть)
            username_query = query.replace('@', '')
            async with db.execute(
                "SELECT * FROM users WHERE username = ? OR username = ?",
                (username_query, f"@{username_query}")
            ) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
            
            # Поиск по реферальному коду
            async with db.execute(GET_USER_BY_REFERRAL_CODE, (query,)) as cursor:
                row = await cursor.fetchone()
                if row:
                    return dict(row)
            
            return None

    async def get_all_users_paginated(self, page: int = 1, per_page: int = 10) -> Tuple[List[Dict[str, Any]], int]:
        """
        Получить всех пользователей с пагинацией.
        Возвращает ([пользователи], всего_страниц)
        """
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            # Подсчитываем общее количество
            async with db.execute("SELECT COUNT(*) FROM users") as cursor:
                total = (await cursor.fetchone())[0]
            
            total_pages = (total + per_page - 1) // per_page
            offset = (page - 1) * per_page
            
            # Получаем пользователей для страницы
            async with db.execute(
                "SELECT * FROM users ORDER BY reg_date DESC LIMIT ? OFFSET ?",
                (per_page, offset)
            ) as cursor:
                rows = await cursor.fetchall()
                users = [dict(row) for row in rows]
            
            return users, total_pages

    async def get_revenue_by_period(self, days: int = 1) -> int:
        """Выручка за период"""
        date_threshold = datetime.now() - timedelta(days=days)
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT SUM(amount) FROM payments WHERE status = 'succeeded' AND payment_date >= ?",
                (date_threshold.isoformat(),)
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row and row[0] else 0

    async def get_successful_payments_count(self) -> int:
        """Количество успешных платежей"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT COUNT(*) FROM payments WHERE status = 'succeeded'"
            ) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def get_average_payment(self) -> int:
        """Средний чек"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT AVG(amount) FROM payments WHERE status = 'succeeded'"
            ) as cursor:
                row = await cursor.fetchone()
                return int(row[0]) if row and row[0] else 0

    async def get_all_payments(self, limit: int = 20) -> List[Dict[str, Any]]:
        """Получить все платежи"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT p.*, u.username 
                FROM payments p
                LEFT JOIN users u ON p.user_id = u.user_id
                ORDER BY p.payment_date DESC
                LIMIT ?
                """,
                (limit,)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_user_payments_stats(self, user_id: int) -> Dict[str, int]:
        """
        Получить статистику платежей пользователя.
        Возвращает: {
            'count': количество платежей,
            'total_amount': общая сумма
        }
        """
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                """
                SELECT COUNT(*) as count, COALESCE(SUM(amount), 0) as total
                FROM payments
                WHERE user_id = ? AND status = 'succeeded'
                """,
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                return {
                    'count': row[0] if row else 0,
                    'total_amount': row[1] if row else 0
                }

    async def get_user_recent_payments(self, user_id: int, limit: int = 5) -> List[Dict[str, Any]]:
        """Получить последние платежи пользователя"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            async with db.execute(
                """
                SELECT amount, tokens, payment_date, status
                FROM payments
                WHERE user_id = ? AND status = 'succeeded'
                ORDER BY payment_date DESC
                LIMIT ?
                """,
                (user_id, limit)
            ) as cursor:
                rows = await cursor.fetchall()
                return [dict(row) for row in rows]

    async def get_referrer_info(self, user_id: int) -> Optional[Dict[str, Any]]:
        """Получить информацию о рефере (кто пригласил)"""
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            
            async with db.execute("SELECT referred_by FROM users WHERE user_id = ?", (user_id,)) as cursor:
                row = await cursor.fetchone()
                if not row or not row['referred_by']:
                    return None
                
                referrer_id = row['referred_by']
            
            async with db.execute(GET_USER, (referrer_id,)) as cursor:
                referrer_row = await cursor.fetchone()
                if referrer_row:
                    return {
                        'referrer_id': referrer_row['user_id'],
                        'referrer_username': referrer_row['username']
                    }
            
            return None


# Создаем глобальный экземпляр
db = Database()
