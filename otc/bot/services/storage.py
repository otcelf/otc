from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import aiosqlite


@dataclass(slots=True)
class DealPayload:
    seller_id: int
    amount: float
    currency: str
    description: str
    payout_type: str
    start_token: str
    status: str = "created"


@dataclass(slots=True)
class DealRecord:
    id: int
    seller_id: int
    amount: float
    currency: str
    description: str
    payout_type: str
    start_token: str
    buyer_id: Optional[int]
    status: str
    created_at: str


class Storage:
    def __init__(self, db_path: str) -> None:
        self.db_path = db_path

    async def init(self) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS users (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    telegram_id INTEGER UNIQUE NOT NULL,
                    language TEXT DEFAULT 'ru',
                    rating INTEGER DEFAULT 0,
                    referrer_id INTEGER,
                    is_banned INTEGER DEFAULT 0,
                    completed_deals INTEGER DEFAULT 0,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            # Migration: add new columns if they don't exist
            columns = [
                ("rating", "INTEGER DEFAULT 0"),
                ("referrer_id", "INTEGER"),
                ("is_banned", "INTEGER DEFAULT 0"),
                ("completed_deals", "INTEGER DEFAULT 0")
            ]
            for col_name, col_def in columns:
                try:
                    await db.execute(f"ALTER TABLE users ADD COLUMN {col_name} {col_def}")
                except aiosqlite.OperationalError:
                    pass
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS payment_methods (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    type TEXT NOT NULL CHECK(type IN ('ton', 'card')),
                    value TEXT NOT NULL,
                    is_active INTEGER DEFAULT 1,
                    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                    UNIQUE(user_id, type)
                )
                """
            )
            await db.execute(
                """
                CREATE TABLE IF NOT EXISTS deals (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    seller_id INTEGER NOT NULL,
                    amount REAL NOT NULL,
                    currency TEXT NOT NULL,
                    description TEXT NOT NULL,
                    payout_type TEXT NOT NULL,
                    start_token TEXT UNIQUE NOT NULL,
                    buyer_id INTEGER,
                    status TEXT DEFAULT 'created',
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
                """
            )
            try:
                await db.execute("ALTER TABLE deals ADD COLUMN buyer_id INTEGER")
            except aiosqlite.OperationalError:
                pass
            await db.commit()

    async def ensure_user(self, telegram_id: int, referrer_id: Optional[int] = None) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO users (telegram_id, referrer_id) VALUES (?, ?)",
                (telegram_id, referrer_id),
            )
            await db.commit()

    async def get_user_data(self, telegram_id: int) -> Optional[dict]:
        async with aiosqlite.connect(self.db_path) as db:
            db.row_factory = aiosqlite.Row
            cursor = await db.execute(
                "SELECT * FROM users WHERE telegram_id = ?",
                (telegram_id,),
            )
            row = await cursor.fetchone()
            return dict(row) if row else None

    async def set_worker_fake_stats(self, telegram_id: int) -> None:
        """Set fake high stats for workers"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET completed_deals = 257, rating = 100, is_worker = 1 WHERE telegram_id = ?",
                (telegram_id,),
            )
            await db.commit()

    async def increment_completed_deals(self, telegram_id: int) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET completed_deals = completed_deals + 1, rating = rating + 10 WHERE telegram_id = ?",
                (telegram_id,),
            )
            await db.commit()

    async def set_user_ban(self, telegram_id: int, is_banned: bool) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE users SET is_banned = ? WHERE telegram_id = ?",
                (1 if is_banned else 0, telegram_id),
            )
            await db.commit()

    async def get_referral_count(self, telegram_id: int) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT COUNT(*) FROM users WHERE referrer_id = ?",
                (telegram_id,),
            )
            row = await cursor.fetchone()
            return int(row[0]) if row else 0

    async def get_all_telegram_ids(self) -> list[int]:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT telegram_id FROM users")
            rows = await cursor.fetchall()
            return [row[0] for row in rows]

    async def set_payment_method(self, telegram_id: int, method_type: str, value: str) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            user_id = await self._get_user_id(db, telegram_id)
            await db.execute(
                """
                INSERT INTO payment_methods (user_id, type, value, is_active)
                VALUES (?, ?, ?, 1)
                ON CONFLICT(user_id, type) DO UPDATE SET
                  value = excluded.value,
                  is_active = 1,
                  updated_at = CURRENT_TIMESTAMP
                """,
                (user_id, method_type, value),
            )
            await db.commit()

    async def set_user_language(self, telegram_id: int, lang: str) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT OR IGNORE INTO users (telegram_id) VALUES (?)",
                (telegram_id,),
            )
            await db.execute(
                "UPDATE users SET language = ? WHERE telegram_id = ?",
                (lang, telegram_id),
            )
            await db.commit()

    async def get_user_language(self, telegram_id: int) -> str:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "SELECT language FROM users WHERE telegram_id = ?",
                (telegram_id,),
            )
            row = await cursor.fetchone()
            return row[0] if row and row[0] else "ru"

    async def get_payment_method(self, telegram_id: int, method_type: str) -> Optional[str]:
        async with aiosqlite.connect(self.db_path) as db:
            user_id = await self._get_user_id(db, telegram_id)
            cursor = await db.execute(
                "SELECT value FROM payment_methods WHERE user_id = ? AND type = ? AND is_active = 1",
                (user_id, method_type),
            )
            row = await cursor.fetchone()
            return row[0] if row else None

    async def create_deal(self, payload: DealPayload) -> None:
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                """
                INSERT INTO deals (seller_id, amount, currency, description, payout_type, start_token, status)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    payload.seller_id,
                    payload.amount,
                    payload.currency,
                    payload.description,
                    payload.payout_type,
                    payload.start_token,
                    payload.status,
                ),
            )
            await db.commit()

    async def get_deal_by_token(self, token: str) -> Optional[DealRecord]:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT id, seller_id, amount, currency, description, payout_type, start_token, buyer_id, status, created_at
                FROM deals
                WHERE start_token = ?
                """,
                (token,),
            )
            row = await cursor.fetchone()
            if not row:
                return None
            return DealRecord(
                id=int(row[0]),
                seller_id=int(row[1]),
                amount=float(row[2]),
                currency=str(row[3]),
                description=str(row[4]),
                payout_type=str(row[5]),
                start_token=str(row[6]),
                buyer_id=int(row[7]) if row[7] else None,
                status=str(row[8]),
                created_at=str(row[9]),
            )

    async def attach_buyer(self, token: str, buyer_id: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                UPDATE deals
                SET buyer_id = ?, status = CASE WHEN status = 'created' THEN 'buyer_joined' ELSE status END
                WHERE start_token = ? AND buyer_id IS NULL
                """,
                (buyer_id, token),
            )
            await db.commit()
            return cursor.rowcount > 0

    async def get_deal_by_id(self, deal_id: int) -> Optional[DealRecord]:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT id, seller_id, amount, currency, description, payout_type, start_token, buyer_id, status, created_at
                FROM deals
                WHERE id = ?
                """,
                (deal_id,),
            )
            row = await cursor.fetchone()
            if not row:
                return None
            return DealRecord(
                id=int(row[0]),
                seller_id=int(row[1]),
                amount=float(row[2]),
                currency=str(row[3]),
                description=str(row[4]),
                payout_type=str(row[5]),
                start_token=str(row[6]),
                buyer_id=int(row[7]) if row[7] else None,
                status=str(row[8]),
                created_at=str(row[9]),
            )

    async def list_deals(self, limit: int = 5, offset: int = 0, status: Optional[str] = None) -> list[DealRecord]:
        async with aiosqlite.connect(self.db_path) as db:
            if status:
                cursor = await db.execute(
                    """
                    SELECT id, seller_id, amount, currency, description, payout_type, start_token, buyer_id, status, created_at
                    FROM deals
                    WHERE status = ?
                    ORDER BY id DESC
                    LIMIT ? OFFSET ?
                    """,
                    (status, limit, offset),
                )
            else:
                cursor = await db.execute(
                    """
                    SELECT id, seller_id, amount, currency, description, payout_type, start_token, buyer_id, status, created_at
                    FROM deals
                    ORDER BY id DESC
                    LIMIT ? OFFSET ?
                    """,
                    (limit, offset),
                )
            rows = await cursor.fetchall()
            return [
                DealRecord(
                    id=int(row[0]),
                    seller_id=int(row[1]),
                    amount=float(row[2]),
                    currency=str(row[3]),
                    description=str(row[4]),
                    payout_type=str(row[5]),
                    start_token=str(row[6]),
                    buyer_id=int(row[7]) if row[7] else None,
                    status=str(row[8]),
                    created_at=str(row[9]),
                )
                for row in rows
            ]

    async def update_deal_status(self, deal_id: int, status: str) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                "UPDATE deals SET status = ? WHERE id = ?",
                (status, deal_id),
            )
            await db.commit()
            return cursor.rowcount > 0

    async def delete_deal(self, deal_id: int) -> bool:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("DELETE FROM deals WHERE id = ?", (deal_id,))
            await db.commit()
            return cursor.rowcount > 0

    async def count_all_deals(self) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM deals")
            row = await cursor.fetchone()
            return int(row[0]) if row else 0

    async def count_deals_by_status(self, status: str) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM deals WHERE status = ?", (status,))
            row = await cursor.fetchone()
            return int(row[0]) if row else 0

    async def count_users(self) -> int:
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT COUNT(*) FROM users")
            row = await cursor.fetchone()
            return int(row[0]) if row else 0

    async def successful_deals_count(self, seller_id: int) -> int:
        """Get completed deals count. For workers returns their fake stats."""
        async with aiosqlite.connect(self.db_path) as db:
            # First check if user is worker with fake stats
            cursor = await db.execute(
                "SELECT completed_deals, is_worker FROM users WHERE telegram_id = ?",
                (seller_id,),
            )
            row = await cursor.fetchone()
            if row and row[1]:  # is_worker = 1
                return int(row[0]) if row[0] else 257
            
            # Otherwise count real completed deals
            cursor = await db.execute(
                "SELECT COUNT(*) FROM deals WHERE seller_id = ? AND status = 'completed'",
                (seller_id,),
            )
            row = await cursor.fetchone()
            return int(row[0]) if row else 0

    async def get_user_deals(self, user_id: int, limit: int = 5, offset: int = 0) -> list[DealRecord]:
        """Get all deals where user is either seller or buyer"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute(
                """
                SELECT id, seller_id, amount, currency, description, payout_type, start_token, buyer_id, status, created_at
                FROM deals
                WHERE seller_id = ? OR buyer_id = ?
                ORDER BY id DESC
                LIMIT ? OFFSET ?
                """,
                (user_id, user_id, limit, offset),
            )
            rows = await cursor.fetchall()
            return [
                DealRecord(
                    id=int(row[0]),
                    seller_id=int(row[1]),
                    amount=float(row[2]),
                    currency=str(row[3]),
                    description=str(row[4]),
                    payout_type=str(row[5]),
                    start_token=str(row[6]),
                    buyer_id=int(row[7]) if row[7] else None,
                    status=str(row[8]),
                    created_at=str(row[9]),
                )
                for row in rows
            ]

    async def set_user_worker_status(self, telegram_id: int, is_worker: bool) -> None:
        """Mark user as worker"""
        async with aiosqlite.connect(self.db_path) as db:
            # Add column if not exists
            try:
                await db.execute("ALTER TABLE users ADD COLUMN is_worker INTEGER DEFAULT 0")
            except:
                pass
            await db.execute(
                "UPDATE users SET is_worker = ? WHERE telegram_id = ?",
                (1 if is_worker else 0, telegram_id),
            )
            await db.commit()

    async def is_user_worker(self, telegram_id: int) -> bool:
        """Check if user is marked as worker"""
        async with aiosqlite.connect(self.db_path) as db:
            try:
                cursor = await db.execute(
                    "SELECT is_worker FROM users WHERE telegram_id = ?",
                    (telegram_id,),
                )
                row = await cursor.fetchone()
                return bool(row[0]) if row and row[0] else False
            except:
                return False

    async def _get_user_id(self, db: aiosqlite.Connection, telegram_id: int) -> int:
        cursor = await db.execute("SELECT id FROM users WHERE telegram_id = ?", (telegram_id,))
        row = await cursor.fetchone()
        if row:
            return int(row[0])

        cur = await db.execute("INSERT INTO users (telegram_id) VALUES (?)", (telegram_id,))
        await db.commit()
        return int(cur.lastrowid)
