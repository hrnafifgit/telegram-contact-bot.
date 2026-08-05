from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_IDS, is_admin
from database import db_manager

async def handle_user_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج استقبال رسائل المستخدمين وتوجيهها لجميع المدراء"""
    user = update.effective_user
    if not user or not update.message:
        return

    # استثناء المدراء (إذا أرسلوا رسالة ليست ردًا)
    if is_admin(user.id) and not update.message.reply_to_message:
        await update.message.reply_text(
            "💡 ملاحظة: أنت مدير. للرد على مستخدم، يرجى القيام بعمل (Reply) على رسالة الإشعار الخاصة به."
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

    # جلب عدد الرسائل غير المقروءة لهذا المستخدم (قبل الرسالة الحالية)
    unread_count = await db_manager.get_unread_count(user_id) + 1
    unread_label = f"📬 رسائل غير مقروءة: {unread_count}" if unread_count > 0 else "✅ لا توجد رسائل سابقة غير مقروءة"

    # بناء نص الإشعار بالتنسيق المطلوب
    notification_text = (
        "📩 رسالة جديدة\n\n"
        f"👤 الاسم: {full_name}\n"
        f"🔗 Username: {username_display}\n"
        f"🆔 ID: `{user_id}`\n"
        f"🕒 الوقت: {msg_date}\n"
        f"{unread_label}\n\n"
        f"💬 الرسالة:\n{msg_text}\n\n"
        f"💡 _للاطلاع على كامل محادثته:_ `/history {user_id}`"
    )

    # إرسال الإشعار لكل مدير في القائمة
    for admin_id in ADMIN_IDS:
        admin_msg = None
        try:
            if update.message.text:
                admin_msg = await context.bot.send_message(
                    chat_id=admin_id,
                    text=notification_text,
                    parse_mode="Markdown"
                )
            else:
                admin_msg = await context.bot.copy_message(
                    chat_id=admin_id,
                    from_chat_id=user_id,
                    message_id=update.message.message_id,
                    caption=notification_text,
                    parse_mode="Markdown"
                )

            # حفظ بيانات الرسالة لكل مدير لتمكين الرد منه
            if admin_msg:
                await db_manager.save_message(
                    user_id=user_id,
                    user_message_id=update.message.message_id,
                    admin_message_id=admin_msg.message_id,
                    message_text=msg_text
                )

        except Exception as e:
            print(f"Error forwarding message to admin {admin_id}: {e}")

    # إشعار المستخدم بتأكيد الاستلام
    await update.message.reply_text("✅ تم إرسال رسالتك بنجاح إلى الإدارة. سيصلك الرد هنا قريبًا.")
