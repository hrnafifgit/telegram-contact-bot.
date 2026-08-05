from telegram import Update
from telegram.ext import ContextTypes
from config import is_admin
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

    if is_admin(user.id):
        unread_total = await db_manager.get_unread_count()
        unread_text = f"📬 لديك {unread_total} رسالة غير مقروءة." if unread_total > 0 else "✅ لا توجد رسائل غير مقروءة."
        await update.message.reply_text(
            f"مرحباً بك يا مدير! 👋\n"
            f"البوت جاهز لاستقبال الرسائل من المستخدمين وتوجيهها إليك.\n"
            f"للرد على أي مستخدم، قم بعمل (Reply) مباشر على رسالة الإشعار الخاصة به.\n\n"
            f"{unread_text}\n\n"
            f"📋 *الأوامر المتاحة:*\n"
            f"• `/history [user_id]` — عرض كامل رسائل مستخدم\n"
            f"• `/stats` — إحصائيات البوت",
            parse_mode="Markdown"
        )
    else:
        await update.message.reply_text(
            f"أهلاً بك {full_name}! 👋\n\n"
            "يمكنك إرسال رسالتك الآن وسأقوم بتوصيلها مباشرة إلى الإدارة.\n"
            "سيصلك الرد هنا فور قراءة الرسالة."
        )
