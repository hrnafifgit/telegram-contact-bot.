import os
import sys
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

from config import BOT_TOKEN, ADMIN_IDS, validate_config
from database import db_manager
from handlers.start import start_command
from handlers.user_messages import handle_user_message
from handlers.admin_replies import handle_admin_reply
from handlers.admin_commands import history_command, stats_command

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

# رابط Webhook — يُضبط في متغيرات البيئة على Render
WEBHOOK_URL = os.getenv("WEBHOOK_URL", "").strip().rstrip("/")
PORT = int(os.getenv("PORT", "8080"))

async def post_init(application):
    """تهيئة قاعدة البيانات عند بدء التشغيل"""
    logger.info("⚡ جاري تهيئة قاعدة البيانات...")
    await db_manager.init_db()
    logger.info("✅ تم تهيئة قاعدة البيانات بنجاح.")
    logger.info(f"👥 المدراء المسجلون: {ADMIN_IDS}")
    if WEBHOOK_URL:
        logger.info(f"🔗 وضع التشغيل: Webhook — {WEBHOOK_URL}")
    else:
        logger.info("🔄 وضع التشغيل: Polling (محلي)")

def main():
    try:
        validate_config()
    except ValueError as e:
        logger.error(e)
        print(f"\n{e}\n")
        print("💡 نصيحة: يرجى إنشاء ملف .env وتعبئة البيانات المطلوبة حسب التعليمات في README.md\n")
        sys.exit(1)

    logger.info("🚀 جاري بدء تشغيل البوت...")

    app = ApplicationBuilder().token(BOT_TOKEN).post_init(post_init).build()

    # أوامر عامة
    app.add_handler(CommandHandler("start", start_command))

    # أوامر المدراء
    app.add_handler(CommandHandler("history", history_command))
    app.add_handler(CommandHandler("stats", stats_command))

    # ردود المدراء على رسائل المستخدمين (Reply فقط من المدراء)
    app.add_handler(
        MessageHandler(
            filters.User(user_id=ADMIN_IDS) & filters.REPLY,
            handle_admin_reply
        )
    )

    # رسائل المستخدمين العاديين
    app.add_handler(
        MessageHandler(
            ~filters.COMMAND,
            handle_user_message
        )
    )

    logger.info("🤖 البوت يعمل الآن ويستقبل الرسائل بنجاح!")

    if WEBHOOK_URL:
        # ===== وضع Webhook (الإنتاج على Render) =====
        # تيليجرام يرسل التحديثات فوراً بدون تأخير
        app.run_webhook(
            listen="0.0.0.0",
            port=PORT,
            webhook_url=f"{WEBHOOK_URL}/webhook",
            url_path="/webhook",
            allowed_updates=Update.ALL_TYPES,
        )
    else:
        # ===== وضع Polling (التشغيل المحلي للتطوير) =====
        app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
