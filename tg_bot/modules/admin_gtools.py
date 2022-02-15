import html

from telegram import ParseMode, Update
from telegram.error import BadRequest
from telegram.ext import CallbackContext
from telegram.utils.helpers import mention_html
from telegram.vendor.ptb_urllib3.urllib3.packages.six import BytesIO

from .. import spamcheck
from .log_channel import loggable
from .helper_funcs.decorators import kigcmd
from .helper_funcs.chat_status import connection_status
from .helper_funcs.admin_status import user_admin_check, user_is_admin, bot_admin_check, bot_is_admin, AdminPerms, UserClass



@kigcmd(command='setgpic', run_async=True, can_disable=False)
@spamcheck
@connection_status
@bot_admin_check(AdminPerms.CAN_CHANGE_INFO)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, UserClass.MOD)
@loggable
def setpic(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user

    if (
        not msg.reply_to_message
        and not msg.reply_to_message.document
        and not msg.reply_to_message.photo
    ):
        msg.reply_text("Please send a photo or a document to set it as the group photo!")
        return ""

    if msg.reply_to_message.photo:
        file_id = msg.reply_to_message.photo[-1].file_id
    elif msg.reply_to_message.document:
        file_id = msg.reply_to_message.document.file_id

    try:
        image_file = context.bot.get_file(file_id)  # kanged from stickers
        image_data = image_file.download(out=BytesIO())
        image_data.seek(0)

        bot.set_chat_photo(chat.id, image_data)
        msg.reply_text(
                f"<b>{user.first_name}</b> changed the group photo."
                if not msg.sender_chat else "Group photo has been changed.",
                parse_mode=ParseMode.HTML)
        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#ADMIN\nChat photo changed\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}"
        )
        return log_message

    except BadRequest as e:
        msg.reply_text("An Error occurred:\n" + str(e))
        return ''



@kigcmd(command='delgpic', run_async=True, can_disable=False)
@spamcheck
@connection_status
@bot_admin_check(AdminPerms.CAN_CHANGE_INFO)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, UserClass.MOD)
@loggable
def delpic(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user

    try:
        bot.delete_chat_photo(chat.id)
        msg.reply_text(
                f"<b>{user.first_name}</b> deleted the group photo."
                if not msg.sender_chat else "Group photo has been deleted.",
                parse_mode=ParseMode.HTML)
        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#ADMIN\nChat photo removed\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}"
        )
        return log_message

    except BadRequest as e:
        msg.reply_text("An Error occurred:\n" + str(e))
        return ''


@kigcmd(command='setgtitle', run_async=True, can_disable=False)
@spamcheck
@connection_status
@bot_admin_check(AdminPerms.CAN_CHANGE_INFO)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, UserClass.MOD)
@loggable
def set_title(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user

    args = context.args

    if args:
        title = "  ".join(args)

    if msg.reply_to_message:
        title = msg.reply_to_message.text

    if not title:
        msg.reply_text("No title given!")
        return ""

    try:
        bot.set_chat_title(chat.id, title)
        if len(title) > 255:  # telegram limits the title/description to 255 characters
            msg.reply_text("Title longer than 255 characters, Truncating it to 255 characters!")
        msg.reply_text(
                f"<b>{user.first_name}</b> changed the group title.to:\n<b>{title[:255]}</b>"
                if not msg.sender_chat else f"Group title has been changed.to:\n<b>{title[:255]}</b>",
                parse_mode=ParseMode.HTML)

        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#ADMIN\nChat title changed\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}"
        )
        return log_message

    except BadRequest as e:
        msg.reply_text("An Error occurred:\n" + str(e))
        return ''

@kigcmd(command='setgdesc', run_async=True, can_disable=False)
@spamcheck
@connection_status
@bot_admin_check(AdminPerms.CAN_CHANGE_INFO)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, UserClass.MOD)
@loggable
def set_desc(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user

    args = context.args

    if args:
        title = "  ".join(args)

    if msg.reply_to_message:
        title = msg.reply_to_message.text

    if not title:
        msg.reply_text("No title given!")
        return ""

    try:
        bot.set_chat_description(chat.id, title)
        if len(title) > 255: # telegram limits the title/description to 255 characters
            msg.reply_text("Description longer than 255 characters, Truncating it to 255 characters!")
        msg.reply_text(
                f"<b>{user.first_name}</b> changed the group description.to:\n<b>{title[:255]}</b>"
                if not msg.sender_chat else f"Group description has been changed.to:\n<b>{title[:255]}</b>",
                parse_mode=ParseMode.HTML)

        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#ADMIN\nChat description changed\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}"
        )
        return log_message

    except BadRequest as e:
        msg.reply_text("An Error occurred:\n" + str(e))
        return ''


@kigcmd(command=['setgstickers', 'setgsticker'], run_async=True, can_disable=False)
@spamcheck
@connection_status
@bot_admin_check(AdminPerms.CAN_CHANGE_INFO)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO, UserClass.MOD)
@loggable
def set_stk_set(update: Update, context: CallbackContext) -> str:
    bot = context.bot
    chat = update.effective_chat
    msg = update.effective_message
    user = update.effective_user

    if not msg.reply_to_message:
        if not msg.reply_to_message.sticker:
            msg.reply_text("Reply to a sticker to set its pack as the group pack!")
            return ""
        msg.reply_text("Reply to a sticker to set its pack as the group pack!")
        return ""

    try:
        stk_set = msg.reply_to_message.sticker.set_name
        bot.set_chat_sticker_set(chat.id, stk_set)
        msg.reply_text(
                f"<b>{user.first_name}</b> changed the group stickers set."
                if not msg.sender_chat else "Group stickers set has been changed.",
                parse_mode=ParseMode.HTML)

        log_message = (
            f"<b>{html.escape(chat.title)}:</b>\n"
            f"#ADMIN\nChat sticker set changed\n"
            f"<b>Admin:</b> {mention_html(user.id, user.first_name)}"
        )
        return log_message
    
    except BadRequest as e:
        # https://github.com/el0xren/tgbot/blob/773220202ea0b20137ccdd833dd97f10d0e54b83/tg_bot/modules/admin.py#L297
        if e.message == 'Participants_too_few':
             errmsg = "Sorry, due to telegram restrictions, the chat needs to have"\
                      " a minimum of 100 members before they can have group stickers!"
        else:
            errmsg = f"An Error occurred:\n{str(e)}"
        msg.reply_text(errmsg)
        return ''
