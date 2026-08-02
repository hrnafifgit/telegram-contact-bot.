from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_ID
from database import db_manager

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج استقبال رسائل المستخدمين وتوجيهها للمدير"""
    user = update.effective_user
    if not user or not update.message:
        return

    # استثناء المدير (إذا أرسل رسالة ليست ردًا)
    if user.id == ADMIN_ID and not update.message.reply_to_message:
        await update.message.reply_text(
            "💡 ملاحظة: أنت المدير. للرد على مستخدم، يرجى القيام بعمل (Reply) على رسالة الإشعار الخاصة به."
        )
        return

    # استخراج البيانات المطلوبة
    full_name = user.full_name or "غير متوفر"
    username_display = f"@{user.username}" if user.username else "غير متوفر"
    user_id = user.id
    msg_date = update.message.date.strftime("%Y-%m-%d %H:%M:%S")
    msg_text = update.message.text or update.message.caption or "[محتوى وسائط/ملف]"

    # حفظ/تحديث بيانات المستخدم في قاعدة البيانات
    await db_manager.save_or_update_user(user_id, full_name, user.username)

    # بناء نص الإشعار بالتنسيق المطلوب تماماً
    notification_text = (
        "📩 رسالة جديدة\n\n"
        f"👤 الاسم: {full_name}\n"
        f"🔗 Username: {username_display}\n"
        f"🆔 ID: {user_id}\n"
        f"🕒 الوقت: {msg_date}\n\n"
        f"💬 الرسالة:\n{msg_text}"
    )

    admin_msg = None
    try:
        # إذا كانت الرسالة نصية فقط
        if update.message.text:
            admin_msg = await context.bot.send_message(
                chat_id=ADMIN_ID,
                text=notification_text
            )
        else:
            # إذا كانت الرسالة تتضمن وسائط (صورة، صوت، فيديو، مستند... إلخ)
            admin_msg = await context.bot.copy_message(
                chat_id=ADMIN_ID,
                from_chat_id=user_id,
                message_id=update.message.message_id,
                caption=notification_text
            )

        # حفظ بيانات الرسالة في قاعدة البيانات لربطها بالرد
        if admin_msg:
            await db_manager.save_message(
                user_id=user_id,
                user_message_id=update.message.message_id,
                admin_message_id=admin_msg.message_id,
                message_text=msg_text
            )

        # إشعار المستخدم بتأكيد الاستلام
        await update.message.reply_text("✅ تم إرسال رسالتك بنجاح إلى الإدارة. سيصلك الرد هنا قريبًا.")

    except Exception as e:
        print(f"Error forwarding message to admin: {e}")
        await update.message.reply_text("❌ حدث خطأ أثناء إرسال رسالتك، يرجى المحاولة لاحقاً.")
