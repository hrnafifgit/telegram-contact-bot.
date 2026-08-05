import os
from pathlib import Path
from dotenv import load_dotenv

# تحميل متغيرات البيئة من ملف .env أو .env.example
base_dir = Path(__file__).parent
env_path = base_dir / ".env"
env_example_path = base_dir / ".env.example"

if env_path.exists():
    load_dotenv(dotenv_path=env_path)
if env_example_path.exists():
    load_dotenv(dotenv_path=env_example_path)

BOT_TOKEN = os.getenv("BOT_TOKEN", "").strip()

# يدعم مدير واحد أو عدة مدراء مفصولين بفاصلة — مثال: 111111,222222
ADMIN_ID_RAW = os.getenv("ADMIN_ID", "0").strip()
ADMIN_IDS: list[int] = []
for _id in ADMIN_ID_RAW.split(","):
    _id = _id.strip()
    if _id.isdigit():
        ADMIN_IDS.append(int(_id))

# أول مدير في القائمة يُعتبر المدير الرئيسي (للتوافق مع الكود القديم)
ADMIN_ID: int = ADMIN_IDS[0] if ADMIN_IDS else 0

DB_PATH = os.getenv("DB_PATH", "bot_database.db").strip()

def validate_config():
    """التحقق من صحة الإعدادات قبل تشغيل البوت"""
    if not BOT_TOKEN or BOT_TOKEN == "your_bot_token_here":
        raise ValueError("❌ خطأ: يرجى ضبط BOT_TOKEN في ملف .env")
    if not ADMIN_IDS or ADMIN_ID <= 0:
        raise ValueError("❌ خطأ: يرجى ضبط ADMIN_ID الصحيح في ملف .env")

def is_admin(user_id: int) -> bool:
    """التحقق مما إذا كان المستخدم مديراً"""
    return user_id in ADMIN_IDS
