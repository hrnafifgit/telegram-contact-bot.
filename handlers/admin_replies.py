from telegram import Update
from telegram.ext import ContextTypes
from config import ADMIN_IDS, is_admin
from database import db_manager

async def handle_admin_reply(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """معالج ردود المدراء على رسائل المستخدمين"""
    user = update.effective_user
    if not user or not update.message:
        return

    # التأكد من أن المرسل مدير وأن الرسالة رد (Reply)
    if not is_admin(user.id) or not update.message.reply_to_message:
        return

    replied_msg_id = update.message.reply_to_message.message_id
    target_user_id = await db_manager.get_user_id_by_admin_message(replied_msg_id)

    if not target_user_id:
        await update.message.reply_text(
            "⚠️ لم يتم العثور على صاحب هذه الرسالة في قاعدة البيانات. قد تكون الرسالة قديمة أو غير مرتبطة بنظام الإشعارات."
        )
        return

    try:
        # إرسال رد المدير إلى المستخدم الأصلي مجهول الهوية
        if update.message.text:
            await context.bot.send_message(
                chat_id=target_user_id,
                text=f"💬 *رد من الإدارة:*\n\n{update.message.text}",
                parse_mode="Markdown"
            )
        else:
            await context.bot.copy_message(
                chat_id=target_user_id,
                from_chat_id=user.id,
                message_id=update.message.message_id,
                caption=f"💬 *رد من الإدارة:*\n\n{update.message.caption or ''}",
                parse_mode="Markdown"
            )

        # تحديد رسائل المستخدم كمردود عليها ومقروءة
        await db_manager.mark_as_replied(target_user_id)

        await update.message.reply_text("✅ تم إرسال الرد بنجاح إلى المستخدم.")

        # جلب بيانات المستخدم الذي تم الرد عليه
        user_info = await db_manager.get_user_info(target_user_id)
        user_name = user_info["full_name"] if user_info else str(target_user_id)
        replier_name = user.full_name or user.username or str(user.id)

        # محتوى إشعار الرد للمشرفين الآخرين
        reply_text = update.message.text or update.message.caption or "[وسائط]"
        reply_notification = (
            f"↩️ *رد من المشرف:* {replier_name}\n"
            f"👤 *إلى المستخدم:* {user_name} (`{target_user_id}`)\n"
            f"{'─' * 28}\n"
            f"{reply_text}"
        )

        # جلب ملخص الرسائل غير المردود عليها
        unreplied = await db_manager.get_unreplied_summary()
        if unreplied:
            summary_lines = [f"📊 *الرسائل المعلقة بعد الرد:*\n{'─' * 28}"]
            for i, entry in enumerate(unreplied, 1):
                uname = entry["username"] or "بدون يوزر"
                summary_lines.append(
                    f"{i}. {entry['full_name']} (@{uname})\n"
                    f"   🆔 `{entry['user_id']}` — 📬 {entry['unreplied']} رسالة\n"
                    f"   💡 `/history {entry['user_id']}`"
                )
            summary_text = "\n".join(summary_lines)
        else:
            summary_text = "✅ *لا توجد رسائل معلقة — تم الرد على الجميع!* 🎉"

        # إشعار جميع المشرفين (إرسال الرد + الملخص)
        for admin_id in ADMIN_IDS:
            try:
                # إشعار المشرفين الآخرين بأن زميلهم رد (ليس الذي رد نفسه)
                if admin_id != user.id:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=reply_notification,
                        parse_mode="Markdown"
                    )
                # إرسال ملخص المعلقة لجميع المشرفين بما فيهم الذي رد
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=summary_text,
                    parse_mode="Markdown"
                )
            except Exception as e:
                print(f"Error notifying admin {admin_id}: {e}")

    except Exception as e:
        print(f"Error sending reply to user {target_user_id}: {e}")
        await update.message.reply_text(
            f"❌ تعذر إرسال الرد للمستخدم (قد يكون قام بحظر البوت أو حذف حسابه).\nتفاصيل الخطأ: {e}"
        )
