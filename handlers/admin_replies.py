from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_ID
from database import db_manager

async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج ردود المدير على رسائل المستخدمين"""
    user = update.effective_user
    if not user or not update.message:
        return

    # التأكد من أن المنسق هو المدير وأن الرسالة عبارة عن رد (Reply)
    if user.id != ADMIN_ID or not update.message.reply_to_message:
        return

    replied_msg_id = update.message.reply_to_message.message_id
    target_user_id = await db_manager.get_user_id_by_admin_message(replied_msg_id)

    if not target_user_id:
        await update.message.reply_text(
            "⚠️ لم يتم العثور على صاحب هذه الرسالة في قاعدة البيانات. قد تكون الرسالة قديمة أو غير مرتبطة بنظام الإشعارات."
        )
        return

    try:
        # إرسال رد المدير إلى المستخدم الأصلي مجهول الهوية (بدون إظهار حساب المدير)
        if update.message.text:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"💬 **رد من الإدارة:**\n\n{update.message.text}",
                parse_mode="Markdown"
            )
        else:
            # نقل الصور أو الوسائط إذا أرسلها المدير
            await context.bot.copy_message(
                chat_id=target_user_id,
                from_chat_id=ADMIN_ID,
                message_id=update.message.message_id,
                caption=f"💬 **رد من الإدارة:**\n\n{update.message.caption or ''}",
                parse_mode="Markdown"
            )

        await update.message.reply_text("✅ تم إرسال الرد بنجاح إلى المستخدم.")

    except Exception as e:
        print(f"Error sending reply to user {target_user_id}: {e}")
        await update.message.reply_text(
            f"❌ تعذر إرسال الرد للمستخدم (قد يكون قام بحظر البوت أو حذف حسابه).\nتفاصيل الخطأ: {e}"
        )
