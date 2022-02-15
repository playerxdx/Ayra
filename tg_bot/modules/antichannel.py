from typing import Optional

from telegram.ext.filters import Filters
from telegram.utils.helpers import mention_html

from tg_bot.modules.helper_funcs.decorators import kigcmd, kigmsg
from telegram import TelegramError, Update
from telegram.ext import CallbackContext

from .helper_funcs.chat_status import connection_status
from .log_channel import loggable
from ..modules.helper_funcs.admin_status import user_admin_check, bot_admin_check, AdminPerms, UserClass, bot_is_admin
import html
from ..modules.sql.antichannel_sql import antichannel_status, disable_antichannel, enable_antichannel

@kigcmd(command="antichannel", group=100)
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS, UserClass.MOD)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, UserClass.MOD)
@loggable
def set_antichannel(update: Update, context: CallbackContext) -> Optional[str]:
    message = update.effective_message
    chat = update.effective_chat
    args = context.args
    user = update.effective_user

    if len(args) > 0:
        s = args[0].lower()

        if s in ["yes", "on", "true"]:
            enable_antichannel(chat.id)
            message.reply_html("Enabled antichannel in {}".format(html.escape(chat.title)))
            log_message = (
                f"#ANTICHANNEL\n"
                f"Enabled\n"
                f"<b>Admin:</b> {mention_html(user.id, user.first_name)}"
            )
            return log_message

        elif s in ["off", "no", "false"]:
            disable_antichannel(chat.id)
            message.reply_html("Disabled antichannel in {}".format(html.escape(chat.title)))
            log_message = (
                f"#ANTICHANNEL\n"
                f"Disabled\n"
                f"<b>Admin:</b> {mention_html(user.id, user.first_name)}"
            )
            return log_message

        else:
            message.reply_text("Unrecognized arguments {}".format(s))
            return

    message.reply_html(
        "Antichannel setting is currently {} in {}".format(antichannel_status(chat.id), html.escape(chat.title)))
    return


@kigmsg(Filters.chat_type.groups & Filters.sender_chat.channel & ~Filters.is_automatic_forward, group=110)
def eliminate_channel(update: Update, context: CallbackContext):
    message = update.effective_message
    chat = update.effective_chat
    bot = context.bot
    if not antichannel_status(chat.id):
        return
    message.delete()
    sender_chat = message.sender_chat
    try:
        bot.ban_chat_sender_chat(sender_chat_id=sender_chat.id, chat_id=chat.id)
    except TelegramError:
        if not bot_is_admin(chat, AdminPerms.CAN_RESTRICT_MEMBERS):
            disable_antichannel(chat.id)
            message.reply_text("I can't restrict users here, so I disabled antichannel for now.")
