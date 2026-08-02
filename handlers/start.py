from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_ID
from database import db_manager

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج الأمر /start"""
    user = update.effective_user
    if not user:
        return

    # حفظ/تحديث بيانات المستخدم في قاعدة البيانات
    full_name = user.full_name or "بدون اسم"
    username = f"@{user.username}" if user.username else None
    await db_manager.save_or_update_user(user.id, full_name, username)

    if user.id == ADMIN_ID:
        await update.message.reply_text(
            "مرحباً بك يا مدير! 👋\n"
            "البوت جاهز لاستقبال الرسائل من المستخدمين وتوجيهها إليك.\n"
            "للرد على أي مستخدم، قم بعمل (Reply) مباشر على رسالة الإشعار الخاصة به."
        )
    else:
        await update.message.reply_text(
            f"أهلاً بك {full_name}! 👋\n\n"
            "يمكنك إرسال رسالتك الآن وسأقوم بتوصيلها مباشرة إلى الإدارة.\n"
            "سيصلك الرد هنا فور قراءة الرسالة."
        )
