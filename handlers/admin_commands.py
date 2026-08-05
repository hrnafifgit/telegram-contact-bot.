from telegram import Update
from telegram.ext import ContextTypes
from config import is_admin
from database import db_manager

async def history_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /history [user_id]
    يعرض كل رسائل مستخدم معين مرتبة من الأقدم للأحدث.
    يمكن الوصول إليه أيضاً عبر الضغط على الـ ID في رسالة الإشعار.
    """
    user = update.effective_user
    if not user or not is_admin(user.id):
        return

    # استخراج الـ user_id من الأمر
    if not context.args or not context.args[0].isdigit():
        await update.message.reply_text(
            "⚠️ يرجى تحديد معرف المستخدم.\n"
            "مثال: `/history 123456789`",
            parse_mode="Markdown"
        )
        return

    target_id = int(context.args[0])

    # جلب بيانات المستخدم
    user_info = await db_manager.get_user_info(target_id)
    if not user_info:
        await update.message.reply_text(
            f"❌ لم يتم العثور على مستخدم بالمعرف: `{target_id}`",
            parse_mode="Markdown"
        )
        return

    # جلب كل الرسائل
    messages = await db_manager.get_all_messages(target_id)
    if not messages:
        await update.message.reply_text(
            f"📭 لا توجد رسائل محفوظة للمستخدم `{target_id}`.",
            parse_mode="Markdown"
        )
        return

    # بناء رأس المحادثة
    username_display = user_info["username"] or "غير متوفر"
    unread = await db_manager.get_unread_count(target_id)
    header = (
        f"📋 *سجل رسائل المستخدم*\n"
        f"{'─' * 30}\n"
        f"👤 الاسم: {user_info['full_name']}\n"
        f"🔗 Username: {username_display}\n"
        f"🆔 ID: `{target_id}`\n"
        f"📅 تاريخ التسجيل: {user_info['created_at']}\n"
        f"📨 إجمالي الرسائل: {len(messages)}\n"
        f"📬 غير مقروء: {unread}\n"
        f"{'─' * 30}"
    )

    await update.message.reply_text(header, parse_mode="Markdown")

    # إرسال الرسائل على شكل دفعات لتجنب تجاوز حد تيليجرام
    BATCH_SIZE = 10
    for i in range(0, len(messages), BATCH_SIZE):
        batch = messages[i:i + BATCH_SIZE]
        batch_text = ""
        for idx, msg in enumerate(batch, start=i + 1):
            status_icon = "✅" if msg["is_read"] else "🔵"
            batch_text += (
                f"{status_icon} *رسالة #{idx}*  |  {msg['created_at']}\n"
                f"{msg['text']}\n"
                f"{'─' * 25}\n"
            )
        await update.message.reply_text(batch_text, parse_mode="Markdown")

    # تحديد الرسائل كمقروءة بعد الاطلاع عليها
    await db_manager.mark_as_read(target_id)
    if unread > 0:
        await update.message.reply_text(f"✅ تم تحديد {unread} رسالة كمقروءة.")


async def stats_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    /stats
    إحصائيات عامة للبوت.
    """
    user = update.effective_user
    if not user or not is_admin(user.id):
        return

    total_users = await db_manager.get_total_users()
    total_messages = await db_manager.get_total_messages()
    total_unread = await db_manager.get_unread_count()

    stats_text = (
        "📊 *إحصائيات البوت*\n"
        f"{'─' * 30}\n"
        f"👥 إجمالي المستخدمين: *{total_users}*\n"
        f"📨 إجمالي الرسائل: *{total_messages}*\n"
        f"📬 رسائل غير مقروءة: *{total_unread}*\n"
        f"{'─' * 30}\n"
        f"💡 اكتب `/history [user_id]` لعرض رسائل أي مستخدم."
    )

    await update.message.reply_text(stats_text, parse_mode="Markdown")
