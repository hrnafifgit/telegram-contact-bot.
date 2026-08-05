import aiosqlite
from datetime import datetime
from config import DB_PATH

class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    async def init_db(self):
        """إنشاء الجداول في حالة عدم وجودها وإضافة الأعمدة الجديدة"""
        async with aiosqlite.connect(self.db_path) as db:
            # جدول المستخدمين
            await db.execute("""
                CREATE TABLE IF NOT EXISTS users (
                    user_id INTEGER PRIMARY KEY,
                    full_name TEXT NOT NULL,
                    username TEXT,
                    created_at TEXT NOT NULL
                )
            """)

            # جدول الرسائل مع حقلي is_read و is_replied للتتبع
            await db.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    user_message_id INTEGER,
                    admin_message_id INTEGER,
                    message_text TEXT,
                    is_read INTEGER NOT NULL DEFAULT 0,
                    is_replied INTEGER NOT NULL DEFAULT 0,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)

            # ترقية آمنة للجدول القديم — إضافة الأعمدة الجديدة إن لم تكن موجودة
            for col_sql in [
                "ALTER TABLE messages ADD COLUMN is_read INTEGER NOT NULL DEFAULT 0",
                "ALTER TABLE messages ADD COLUMN is_replied INTEGER NOT NULL DEFAULT 0",
            ]:
                try:
                    await db.execute(col_sql)
                except Exception:
                    pass  # العمود موجود مسبقاً

            await db.commit()

    async def save_or_update_user(self, user_id: int, full_name: str, username: str = None):
        """حفظ أو تحديث بيانات المستخدم"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO users (user_id, full_name, username, created_at)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(user_id) DO UPDATE SET
                    full_name = excluded.full_name,
                    username = excluded.username
            """, (user_id, full_name, username, now))
            await db.commit()

    async def save_message(self, user_id: int, user_message_id: int, admin_message_id: int, message_text: str):
        """حفظ سجل الرسالة للربط بين رد المدير والمستخدم"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                INSERT INTO messages (user_id, user_message_id, admin_message_id, message_text, is_read, is_replied, created_at)
                VALUES (?, ?, ?, ?, 0, 0, ?)
            """, (user_id, user_message_id, admin_message_id, message_text, now))
            await db.commit()

    async def get_user_id_by_admin_message(self, admin_message_id: int) -> int | None:
        """جلب معرف المستخدم الأصلي بناءً على معرف رسالة الإشعار عند المدير"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT user_id FROM messages WHERE admin_message_id = ? ORDER BY id DESC LIMIT 1
            """, (admin_message_id,)) as cursor:
                row = await cursor.fetchone()
                return row[0] if row else None

    async def get_unread_count(self, user_id: int = None) -> int:
        """
        عدد الرسائل غير المقروءة.
        إذا تم تمرير user_id يُرجع العدد لمستخدم محدد، وإلا يُرجع إجمالي غير المقروء.
        """
        async with aiosqlite.connect(self.db_path) as db:
            if user_id is not None:
                async with db.execute(
                    "SELECT COUNT(*) FROM messages WHERE user_id = ? AND is_read = 0",
                    (user_id,)
                ) as cursor:
                    row = await cursor.fetchone()
            else:
                async with db.execute(
                    "SELECT COUNT(*) FROM messages WHERE is_read = 0"
                ) as cursor:
                    row = await cursor.fetchone()
            return row[0] if row else 0

    async def get_all_messages(self, user_id: int) -> list[dict]:
        """جلب كل رسائل مستخدم معين مرتبة من الأقدم للأحدث"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT message_text, is_read, created_at
                FROM messages
                WHERE user_id = ?
                ORDER BY id ASC
            """, (user_id,)) as cursor:
                rows = await cursor.fetchall()
                return [
                    {"text": r[0], "is_read": bool(r[1]), "created_at": r[2]}
                    for r in rows
                ]

    async def mark_as_read(self, user_id: int):
        """تحديد جميع رسائل مستخدم معين كمقروءة"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE messages SET is_read = 1 WHERE user_id = ? AND is_read = 0",
                (user_id,)
            )
            await db.commit()

    async def mark_as_replied(self, user_id: int):
        """تحديد جميع رسائل مستخدم معين كمردود عليها"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE messages SET is_replied = 1, is_read = 1 WHERE user_id = ? AND is_replied = 0",
                (user_id,)
            )
            await db.commit()

    async def get_unreplied_summary(self) -> list[dict]:
        """
        جلب ملخص الأشخاص الذين لم يُرد عليهم بعد.
        يُرجع قائمة بالمستخدمين الذين لديهم رسائل غير مردود عليها.
        """
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("""
                SELECT u.user_id, u.full_name, u.username, COUNT(m.id) as unreplied
                FROM messages m
                JOIN users u ON m.user_id = u.user_id
                WHERE m.is_replied = 0
                GROUP BY m.user_id
                ORDER BY unreplied DESC
            """) as cursor:
                rows = await cursor.fetchall()
                return [
                    {
                        "user_id": r[0],
                        "full_name": r[1],
                        "username": r[2],
                        "unreplied": r[3],
                    }
                    for r in rows
                ]

    async def get_user_info(self, user_id: int) -> dict | None:
        """جلب بيانات مستخدم واحد"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute(
                "SELECT user_id, full_name, username, created_at FROM users WHERE user_id = ?",
                (user_id,)
            ) as cursor:
                row = await cursor.fetchone()
                if not row:
                    return None
                return {
                    "user_id": row[0],
                    "full_name": row[1],
                    "username": row[2],
                    "created_at": row[3],
                }

    async def get_total_users(self) -> int:
        """إجمالي عدد المستخدمين المسجلين"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM users") as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

    async def get_total_messages(self) -> int:
        """إجمالي عدد الرسائل"""
        async with aiosqlite.connect(self.db_path) as db:
            async with db.execute("SELECT COUNT(*) FROM messages") as cursor:
                row = await cursor.fetchone()
                return row[0] if row else 0

db_manager = Database()
