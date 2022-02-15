import html
from typing import Optional

from telegram import ParseMode, Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext
from telegram.utils.helpers import mention_html

from .. import spamcheck
from .helper_funcs.chat_status import connection_status
from .helper_funcs.extraction import extract_user, extract_user_and_text
from .helper_funcs.decorators import kigcmd
from .log_channel import loggable
from .helper_funcs.admin_status import (
    user_is_admin as admin,
    user_admin_check,
    bot_admin_check,
    bot_is_admin as b_admin,
    AdminPerms,
    UserClass,
    get_bot_member,
)

@kigcmd(command="setanon", can_disable=False)
@spamcheck
@connection_status
@bot_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@user_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@loggable
def promoteanon(update: Update, context: CallbackContext) -> Optional[str]:
    bot = context.bot
    args = context.args

    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == "private":
        message.reply_text("This command is meant to be used in groups not PM!")

    user_id, title = extract_user_and_text(message, args)

    if not user_id:
        user_id = user.id
        title = " ".join(args)

    try:
        user_member = chat.get_member(user_id)
    except Exception as e:
        message.reply_text("Error:\n`{}`".format(e))
        return

    if user_member.status == "creator":
        message.reply_text("This user is the chat creator, he can manage his own stuff!")
        return

    if getattr(user_member, "is_anonymous") is True:
        message.reply_text("This user is already anonymous!")
        return

    if user_id == bot.id:
        message.reply_text("Yeah, I wish I could promote myself...")
        return

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = get_bot_member(chat.id)
    # set same perms as user -  to keep the other perms untouched!
    u_member = chat.get_member(user_id)
    # the perms may be not same as old ones if the bot doesn't have the rights to change them but can't do anything about it

    try:
        if title:
            bot.setChatAdministratorCustomTitle(chat.id, user_id, title)
        bot.promoteChatMember(
            chat.id,
            user_id,
            is_anonymous=True,

            can_change_info=bool(bot_member.can_change_info and u_member.can_change_info),
            can_post_messages=bool(bot_member.can_post_messages and u_member.can_post_messages),
            can_edit_messages=bool(bot_member.can_edit_messages and u_member.can_edit_messages),
            can_delete_messages=bool(bot_member.can_delete_messages and u_member.can_delete_messages),
            can_invite_users=bool(bot_member.can_invite_users and u_member.can_invite_users),
            can_promote_members=bool(bot_member.can_promote_members and u_member.can_promote_members),
            can_restrict_members=bool(bot_member.can_restrict_members and u_member.can_restrict_members),
            can_pin_messages=bool(bot_member.can_pin_messages and u_member.can_pin_messages),
            can_manage_voice_chats=bool(bot_member.can_manage_voice_chats and u_member.can_manage_voice_chats),

        )

        rmsg = f"<b>{user_member.user.first_name or user_id}</b> is now anonymous"
        if title:
            rmsg += f" with title <code>{html.escape(title)}</code>"
        bot.sendMessage(
            chat.id,
            rmsg,
            parse_mode=ParseMode.HTML,
        ) 
    except BadRequest as err:
        if err.message == "User_not_mutual_contact":
            message.reply_text("How am I mean to promote someone who isn't in the group?")
        else:
            message.reply_text("An error occurred while promoting.")
        return

    log_message = (
        f"<b>{html.escape(chat.title)}:</b>\n"
        f"#PROMOTED\n"
        f"Anonymous\n"
        f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
        f"<b>User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
    )

    return log_message

@kigcmd(command="unsetanon", can_disable=False)
@spamcheck
@connection_status
@bot_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@user_admin_check(AdminPerms.CAN_PROMOTE_MEMBERS)
@loggable
def demoteanon(update: Update, context: CallbackContext) -> Optional[str]:
    bot = context.bot
    args = context.args

    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user

    if chat.type == "private":
        message.reply_text("This command is meant to be used in groups not PM!")

    user_id = extract_user(message, args)

    if not user_id:
        user_id = user.id

    try:
        user_member = chat.get_member(user_id)
    except Exception as e:
        message.reply_text("Error:\n`{}`".format(e))
        return

    if user_member.status == "creator" and user_id == user.id:
        message.reply_text("meh")
        return

    if user_member.status == "creator":
        message.reply_text("This person is the chat CREATOR, find someone else to play with.")
        return

    if user_member.status != "administrator":
        message.reply_text("This user isn't an admin!")
        return

    if getattr(user_member, "is_anonymous") is False:
        message.reply_text("This user isn't anonymous!")
        return

    if user_id == bot.id:
        message.reply_text("I can't demote myself! Get an admin to do it for me.")
        return

    # set same perms as bot - bot can't assign higher perms than itself!
    bot_member = get_bot_member(bot.id)
    # set same perms as user -  to keep the other perms untouched!
    u_member = chat.get_member(user_id)
    # the perms may be not same as old ones if the bot doesn't have the rights to change them but can't do anything about it

    try:
        bot.promoteChatMember(
            chat.id,
            user_id,
            is_anonymous=False,

            can_change_info=bool(bot_member.can_change_info and u_member.can_change_info),
            can_post_messages=bool(bot_member.can_post_messages and u_member.can_post_messages),
            can_edit_messages=bool(bot_member.can_edit_messages and u_member.can_edit_messages),
            can_delete_messages=bool(bot_member.can_delete_messages and u_member.can_delete_messages),
            can_invite_users=bool(bot_member.can_invite_users and u_member.can_invite_users),
            can_promote_members=bool(bot_member.can_promote_members and u_member.can_promote_members),
            can_restrict_members=bool(bot_member.can_restrict_members and u_member.can_restrict_members),
            can_pin_messages=bool(bot_member.can_pin_messages and u_member.can_pin_messages),
            can_manage_voice_chats=bool(bot_member.can_manage_voice_chats and u_member.can_manage_voice_chats),
        )

        rmsg = f"<b>{user_member.user.first_name or user_id}</b> is no longer anonymous"
        bot.sendMessage(
            chat.id,
            rmsg,
            parse_mode=ParseMode.HTML,
        )  

        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#DEMOTED\n"
            f"Non anonymous\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}\n"
            f"<b>User:</b> {mention_html(user_member.user.id, user_member.user.first_name)}"
        )

        return log_message

    except BadRequest as e:
        message.reply_text(
            f"Could not demote!\n{str(e)}"
        )
        return
