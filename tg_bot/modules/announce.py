import html

from telegram import Update
from telegram.utils.helpers import mention_html

from telegram.ext import CallbackContext
from telegram.utils.helpers import mention_html

from .. import spamcheck
from .log_channel import loggable
from .helper_funcs.decorators import kigcmd
from .helper_funcs.admin_status import user_admin_check, AdminPerms
from .helper_funcs.chat_status import connection_status
import tg_bot.modules.sql.logger_sql as sql


@kigcmd(command="announce", pass_args=True)
@spamcheck
@connection_status
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
@loggable
def announcestat(update: Update, context: CallbackContext) -> str:
    args = context.args
    if len(args) > 0:
        user = update.effective_user
        chat = update.effective_chat

        if args[0].lower() in ["on", "yes", "true"]:
            sql.enable_chat_log(update.effective_chat.id)
            update.effective_message.reply_text(
                "I've enabled announcements in this group. Now any admin actions in your group will be announced."
            )
            logmsg = (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#ANNOUNCE_TOGGLED\n"
                f"Admin actions announcement has been <b>enabled</b>\n"
                f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n "
            )
            return logmsg

        elif args[0].lower() in ["off", "no", "false"]:
            sql.disable_chat_log(update.effective_chat.id)
            update.effective_message.reply_text(
                "I've disabled announcements in this group. Now admin actions in your group will not be announced."
            )
            logmsg = (
                f"<b>{html.escape(chat.title)}:</b>\n"
                f"#ANNOUNCE_TOGGLED\n"
                f"Admin actions announcement has been <b>disabled</b>\n"
                f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n "
            )
            return logmsg
    else:
        update.effective_message.reply_text(
            "Give me some arguments to choose a setting! on/off, yes/no!\n\n"
            "Your current setting is: {}\n"
            "When True, any admin actions in your group will be announced."
            "When False, admin actions in your group will not be announced.".format(
                sql.does_chat_log(update.effective_chat.id))
        )
        return ''


def __migrate__(old_chat_id, new_chat_id):
    sql.migrate_chat(old_chat_id, new_chat_id)
