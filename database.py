import aiosqlite
from datetime import datetime
from config import DB_PATH

class Database:
    def __init__(self, db_path: str = DB_PATH):
        self.db_path = db_path

    async def init_db(self):
        """إنشاء الجداول في حالة عدم وجودها"""
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

            # جدول الرسائل والربط بين إشعار المدير ورسالة المستخدم
            await db.execute("""
                CREATE TABLE IF NOT EXISTS messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    user_id INTEGER NOT NULL,
                    user_message_id INTEGER,
                    admin_message_id INTEGER,
                    message_text TEXT,
                    created_at TEXT NOT NULL,
                    FOREIGN KEY (user_id) REFERENCES users (user_id)
                )
            """)
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
                INSERT INTO messages (user_id, user_message_id, admin_message_id, message_text, created_at)
                VALUES (?, ?, ?, ?, ?)
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

db_manager = Database()
