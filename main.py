import os
import sys
import logging
import asyncio
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters

from config import BOT_TOKEN, ADMIN_ID, validate_config
from database import db_manager
from handlers.start import start_command
from handlers.user_messages import handle_user_message
from handlers.admin_replies import handle_admin_reply

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO
)
logger = logging.getLogger(__name__)

async def start_dummy_health_server():
    """خادم ويب مصغر لاستجابة فحص الصحة (Health Check) للمنصات المجانية مثل Render Web Service"""
    port = int(os.getenv("PORT", "0"))
    if port == 0:
        return

    async def handle_client(reader, writer):
        response = "HTTP/1.1 200 OK\r\nContent-Type: text/plain\r\nContent-Length: 15\r\n\r\nBot is running!"
        writer.write(response.encode("utf-8"))
        await writer.drain()
        writer.close()
        await writer.wait_closed()

    server = await asyncio.start_server(handle_client, "0.0.0.0", port)
    logger.info(f"🌐 خادم الفحص المجاني يعمل على المنفذ: {port}")
    asyncio.create_task(server.serve_forever())

async def post_init(application):
    """تهيئة قاعدة البيانات وبدء خادم الاستجابة عند الحاجة"""
    logger.info("⚡ جاري تهيئة قاعدة البيانات...")
    await db_manager.init_db()
    logger.info("✅ تم تهيئة قاعدة البيانات بنجاح.")
    await start_dummy_health_server()

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

    app.add_handler(CommandHandler("start", start_command))

    app.add_handler(
        MessageHandler(
            filters.User(user_id=ADMIN_ID) & filters.REPLY,
            handle_admin_reply
        )
    )

    app.add_handler(
        MessageHandler(
            ~filters.COMMAND,
            handle_user_message
        )
    )

    logger.info("🤖 البوت يعمل الآن ويستقبل الرسائل بنجاح!")
    app.run_polling(allowed_updates=Update.ALL_TYPES)

if __name__ == "__main__":
    main()
