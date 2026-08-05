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
            "لم يتم العثور على صاحب هذه الرسالة في قاعدة البيانات. قد تكون الرسالة قديمة."
        )
        return

    try:
        # ارسال رد المدير للمستخدم - نص عادي بدون parse_mode لتفادي مشاكل الرموز الخاصة
        if update.message.text:
            await context.bot.send_message(
                chat_id=target_user_id,
                text="رد من الادارة:\n\n" + update.message.text,
            )
        else:
            await context.bot.copy_message(
                chat_id=target_user_id,
                from_chat_id=user.id,
                message_id=update.message.message_id,
            )

        # تحديد رسائل المستخدم كمردود عليها ومقروءة
        await db_manager.mark_as_replied(target_user_id)

        await update.message.reply_text("تم ارسال الرد بنجاح للمستخدم.")

        # جلب بيانات المستخدم الذي تم الرد عليه
        user_info = await db_manager.get_user_info(target_user_id)
        user_name = user_info["full_name"] if user_info else str(target_user_id)
        replier_name = user.full_name or user.username or str(user.id)

        # نص الاشعار - بدون Markdown تماما لضمان الوصول عند وجود اي رموز خاصة
        reply_text = update.message.text or update.message.caption or "[وسائط]"
        separator = "-" * 30
        reply_notification = (
            "رد من المشرف: " + replier_name + "\n"
            "الى المستخدم: " + user_name + " (" + str(target_user_id) + ")\n"
            + separator + "\n"
            + reply_text
        )

        # ملخص الرسائل المعلقة - نص عادي
        unreplied = await db_manager.get_unreplied_summary()
        if unreplied:
            lines = ["الرسائل المعلقة بعد الرد:\n" + separator]
            for i, entry in enumerate(unreplied, 1):
                uname = "@" + entry["username"] if entry["username"] else "بدون يوزر"
                lines.append(
                    str(i) + ". " + entry["full_name"] + " (" + uname + ")\n"
                    "   ID: " + str(entry["user_id"]) + " - " + str(entry["unreplied"]) + " رسالة معلقة\n"
                    "   /history " + str(entry["user_id"])
                )
            summary_text = "\n".join(lines)
        else:
            summary_text = "لا توجد رسائل معلقة - تم الرد على الجميع!"

        # ارسال الاشعار لكل المشرفين - بدون parse_mode لضمان وصول الرسالة دائما
        for admin_id in ADMIN_IDS:
            try:
                if admin_id != user.id:
                    await context.bot.send_message(
                        chat_id=admin_id,
                        text=reply_notification,
                    )
                await context.bot.send_message(
                    chat_id=admin_id,
                    text=summary_text,
                )
            except Exception as e:
                print(f"Error notifying admin {admin_id}: {e}")

    except Exception as e:
        print(f"Error sending reply to user {target_user_id}: {e}")
        await update.message.reply_text(
            "تعذر ارسال الرد للمستخدم. تفاصيل الخطأ: " + str(e)
        )
