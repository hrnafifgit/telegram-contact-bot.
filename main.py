import sys
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

from config import BOT_TOKEN, ADMIN_ID, validate_config
from database import db_manager
from handlers.start import start_command
from handlers.user_messages import handle_user_message
from handlers.admin_replies import handle_admin_reply

# إعداد التسجيل (Logging) لمتابعة أحداث البوت
logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def post_init(application):
    """تهيئة قاعدة البيانات عند بدء تشغيل التطبيق"""
    logger.info("⚡ جاري تهيئة قاعدة البيانات...")
    await db_manager.init_db()
    logger.info("✅ تم تهيئة قاعدة البيانات بنجاح.")

def main():
    # التحقق من الإعدادات
    try:
        validate_config()
    except ValueError as e:
        logger.error(e)
        print(f"\n{e}\n")
        print("💡 نصيحة: يرجى إنشاء ملف .env وتعبئة البيانات المطلوبة حسب التعليمات في README.md\n")
        sys.exit(1)

    logger.info("🚀 جاري بدء تشغيل البوت...")

    # بناء تطبيق البوت
    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()

    # تسجيل معالج الأوامر
    app.add_handler(CommandHandler("start", start_command))

    # تسجيل معالجات الرسائل
    # 1. معالج ردود المدير (عندما يقوم المدير بعمل Reply على رسالة إشعار)
    app.add_handler(
        MessageHandler(
            filters.User(user_id=ADMIN_ID) & filters.REPLY,
            handle_admin_reply
        )
    )

    # 2. معالج رسائل المستخدمين العامة (غير الأوامر)
    app.add_handler(
        MessageHandler(
            ~filters.COMMAND,
            handle_user_message
        )
    )

    # تشغيل البوت بواسطة Polling
    logger.info("🤖 البوت يعمل الآن ويستقبل الرسائل بنجاح!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
