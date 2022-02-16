import logging
from enum import Enum
from typing import Optional

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import CallbackContext
from telegram.ext.filters import Filters
from telegram.error import BadRequest, TelegramError
from telegram.utils import helpers
from telegram.parsemode import ParseMode

from SibylSystem import GeneralException

from ..import dispatcher, sibylClient as Client

from .log_channel import loggable
from .sql.users_sql import get_user_com_chats

from .sql.sibylsystem_sql import (
    SIBYLBAN_SETTINGS,
    does_chat_sibylban,
    enable_sibyl,
    disable_sibyl,
    toggle_sibyl_log,
    toggle_sibyl_mode,
)

from .helper_funcs.chat_status import connection_status
from .helper_funcs.admin_status import user_admin_check, bot_admin_check, AdminPerms, user_is_admin
from .helper_funcs.decorators import kigcmd, kigmsg, kigcallback as kigcb

logger = logging.getLogger('[Enterprise]')

logger.info("Drag and drop Sibyl System Plugin by Sayan Biswas [github.com/Dank-del // t.me/dank_as_fuck] @Kaizoku")
logger.info("Sibyl System Plugin updated by Luke [github.com/itsLuuke // t.me/itsLuuke]")


def get_sibyl_setting(chat_id):
    try:
        log_stat = SIBYLBAN_SETTINGS[f'{chat_id}'][0]
        act = SIBYLBAN_SETTINGS[f'{chat_id}'][1]
    except KeyError:  # set default
        log_stat = True
        act = 1
    return log_stat, act


@kigmsg(Filters.chat_type.groups, group=101)
@loggable
def sibyl_ban(update: Update, context: CallbackContext) -> Optional[str]:
    message = update.effective_message
    chat = update.effective_chat
    user = update.effective_user
    if not user:
        return
    bot = context.bot
    if not does_chat_sibylban(chat.id):
        return

    mem = chat.get_member(user.id)
    if mem.status not in ["member", "left"]:
        return

    if Client:
        log_stat, act = get_sibyl_setting(chat.id)
        try:
            data = Client.get_info(user.id)
        except GeneralException:
            return

        except BaseException as e:
            logger.error(e)
            return

        if data.banned and act in {1, 2}:
            try:
                bot.ban_chat_member(chat_id=chat.id, user_id=user.id)
            except BadRequest:
                return
            except BaseException as e:
                logger.error("Failed to ban {} in {} due to {}".format(user.id, chat.id, e))

            txt = '''{} has a <a href="https://t.me/SibylSystem/3">Crime Coefficient</a> of {}\n'''.format(
                    user.mention_html(), data.crime_coefficient)
            txt += "<b>Enforcement Mode:</b> {}".format(
                    "Lethal Eliminator" if not data.is_bot else "Destroy Decomposer")

            log_msg = "#SIBYL_BAN #{}".format(", #".join(data.ban_flags)) if data.ban_flags else "#SIBYL_BAN"
            log_msg += "\n • <b>User:</b> {}\n".format(user.mention_html())
            log_msg += " • <b>Reason:</b> <code>{}</code>\n".format(data.reason) if data.reason else ""
            log_msg += " • <b>Ban time:</b> <code>{}</code>\n\n".format(data.date) if data.date else ""

            if act == 1:
                message.reply_html(text=txt, disable_web_page_preview=True)

            if log_stat:
                return log_msg

            handle_sibyl_banned(user.id, data)


@kigmsg(Filters.status_update.new_chat_members, group=102)
@loggable
def sibyl_ban_alert(update: Update, context: CallbackContext) -> Optional[str]:
    message = update.effective_message
    chat = update.effective_chat
    users = update.effective_message.new_chat_members
    bot = context.bot
    if not users:
        return

    if not does_chat_sibylban(chat.id):
        return

    if Client:
        log_stat, act = get_sibyl_setting(chat.id)
        if act != 3:  # just for alert mode
            return

        for user in users:
            try:
                data = Client.get_info(user.id)
            except GeneralException:
                return
            except BaseException as e:
                logger.error(e)
                return

            if data.banned:
                txt = '''{} has a <a href="https://t.me/SibylSystem/3">Crime Coefficient</a> of {}\n'''.format(
                        user.mention_html(), data.crime_coefficient)
                txt += "<b>Enforcement Mode:</b> None"
                url = helpers.create_deep_linked_url(bot.username, "sibyl_banned-{}".format(user.id))

                keyboard = [[InlineKeyboardButton(text="More Info", url=url)]]

                reply_markup = InlineKeyboardMarkup(keyboard)
                log_msg = "#SIBYL_BAN #{}".format(", #".join(data.ban_flags)) if data.ban_flags else "#SIBYL_BAN"
                log_msg += "\n • <b>User:</b> {}\n".format(user.mention_html())
                log_msg += " • <b>Reason:</b> <code>{}</code>\n".format(data.reason) if data.reason else ""
                log_msg += " • <b>Ban time:</b> <code>{}</code>\n".format(data.date) if data.date else ""
                log_msg += " • <b>Enforcement Mode:</b> None\n\n"
                message.reply_html(text=txt, disable_web_page_preview=True, reply_markup=reply_markup)

                if log_stat:
                    return log_msg

                handle_sibyl_banned(user.id, data)


@loggable
def handle_sibyl_banned(user, data):
    bot = dispatcher.bot
    chat = get_user_com_chats(user.id)
    keyboard = [[InlineKeyboardButton("Appeal", url="https://t.me/SibylRobot",)]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        bot.send_message(user.id, "You have been banned in sibyl", parse_mode=ParseMode.HTML, reply_markup=reply_markup)
    except TelegramError:
        pass

    for c in chat:
        if does_chat_sibylban(c):
            log_stat, act = get_sibyl_setting(chat.id)

            if act in {1, 2}:
                # ban user without spamming chat even if its interactive
                bot.ban_chat_member(chat_id=c, user_id=user.id)

            if log_stat:
                log_msg = "#SIBYL_BAN #{}".format(", #".join(data.ban_flags)) if data.ban_flags else "#SIBYL_BAN"
                log_msg += " • <b>User</b> {}\n".format(user.mention_html())
                log_msg += " • <b>Reason:</b> <code>{}</code>\n".format(data.reason) if data.reason else ""
                log_msg += " • <b>Ban time:</b> <code>{}</code>\n".format(data.date) if data.date else ""
                log_msg += " • <b>Enforcement Mode:</b> None\n\n"


modes_txt = '''
Sibyl System Mode control:
 • <b>Interactive</b> - Anti spam with alerts in group
 • <b>Silent</b> - No alerts and silenced anti-spam actions
 • <b>Alerts Only</b> - No actions, only warnings on user join

Additional Configuration:
 • <b>Log Channel</b> - Creates a log channel entry (if you have a log channel) for all sibyl moderations

Current Settings:'''

connection_txt = '''
Connection to <a href="https://t.me/SibylSystem/2">Sibyl System</a> can be turned off and on using the panel buttons below.
'''


@kigcb(pattern="sibyl_connect", run_async=True)
@kigcmd(command="sibyl", group=110, run_async = True)
@connection_status
@bot_admin_check(AdminPerms.CAN_RESTRICT_MEMBERS)
@user_admin_check(AdminPerms.CAN_CHANGE_INFO)
def sibylmain(update: Update, _: CallbackContext):
    chat = update.effective_chat
    message = update.effective_message
    stat = does_chat_sibylban(chat.id)
    user = update.effective_user
    if update.callback_query:
        if update.callback_query.data == "sibyl_connect=toggle":
            if not user_is_admin(update, user.id, perm = AdminPerms.CAN_CHANGE_INFO):
                update.callback_query.answer()
                return

            if stat:
                disable_sibyl(chat.id)
                stat = False
            else:
                enable_sibyl(chat.id)
                stat = True
            update.callback_query.answer(f'Sibyl System has been {"Enabled!" if stat else "Disabled!"}')

        elif update.callback_query.data == "sibyl_connect=close":
            if not user_is_admin(update, user.id, perm = AdminPerms.CAN_CHANGE_INFO):
                update.callback_query.answer()
            message.delete()
            return

    text = f'{connection_txt}\n • <b>Current Status:</b> <code>{"Enabled" if stat else "Disabled"}</code>'
    keyboard = [
        [
            InlineKeyboardButton(
                "✤ Disconnect" if stat else "✤ Connect",
                callback_data="sibyl_connect=toggle",
            ),
            InlineKeyboardButton(
                "♡ Modes",
                callback_data='sibyl_toggle=main'
            )
        ],
        [
            InlineKeyboardButton(
                "❖ API",
                url="https://t.me/PsychoPass/4",
            ),
            InlineKeyboardButton(
                "？What is Sibyl",
                url="https://t.me/SibylSystem/2",
            ),
        ]]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        message.edit_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except BadRequest:
        message.reply_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML, disable_web_page_preview=True)


class SibylMode(Enum):
    Interactive = 1
    Silent = 2
    Alerts = 3


@kigcb(pattern="sibyl_toggle", run_async=True)
@connection_status
def sibyltoggle(update: Update, _: CallbackContext):
    chat = update.effective_chat
    message = update.effective_message
    user = update.effective_user
    if not user_is_admin(update, user.id, perm = AdminPerms.CAN_CHANGE_INFO):
        update.callback_query.answer("This is for admins only!")
        return

    log_stat, act = get_sibyl_setting(chat.id)
    todo = update.callback_query.data.replace("sibyl_toggle=", "")

    if todo.startswith("log"):
        toggle_sibyl_log(chat.id)
        log_stat = not log_stat

    elif not todo.startswith("main"):
        toggle_sibyl_mode(chat.id, int(todo))
        act = int(todo)

    text = (f'{modes_txt}\n • <b>Mode:</b> <code>{SibylMode(act).name}</code>\n'
            f' • <b>Logs:</b> <code>{"Enabled" if log_stat else "Disabled"}</code>')
    keyboard = [
        [
            InlineKeyboardButton(
                SibylMode(2).name if act != 2 else SibylMode(1).name,
                callback_data=f"sibyl_toggle={int(2 if not act==2 else 1)}",
            ),
            InlineKeyboardButton(
                SibylMode(3).name + " Only" if act != 3 else SibylMode(1).name,
                callback_data=f'sibyl_toggle={int(3 if act != 3 else 1)}',
            ),
        ],
        [
            InlineKeyboardButton(
                "🔙",
                callback_data="sibyl_connect",
            ),
            InlineKeyboardButton(
                "Disable Log" if log_stat else "Enable Log",
                callback_data="sibyl_toggle=log",
            ),
            InlineKeyboardButton(
                "✖️",
                callback_data="sibyl_connect=close",
            ),
        ],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    try:
        message.edit_text(text, reply_markup=reply_markup, parse_mode=ParseMode.HTML, disable_web_page_preview=True)
    except BadRequest:
        pass


@kigcmd(command="start", group=113, run_async = True)
def sibyl_banned(update: Update, ctx: CallbackContext):
    chat = update.effective_chat
    args = ctx.args
    reply_markup = None

    if not(chat.type == "private" and args):
        return

    if not args[0].startswith("sibyl_banned-"):
        return

    user = args[0].split("-")[1]

    if not Client:
        return

    try:
        data = Client.get_info(int(user))
    except GeneralException:
        return
    except BaseException as e:
        logger.error(e)
        return

    txt = "<b>Cymatic Scan Results</b>"
    txt += f"\n • <b>Banned:</b> <code>{'No' if not data.banned else 'Yes'}</code>"
    if data.ban_flags:
        txt += f"\n • <b>Ban Flags:</b> <code>{', '.join(data.ban_flags)}</code>"
    if data.crime_coefficient:
        txt += f"\n • <b>Crime Coefficient:</b> <code>{data.crime_coefficient}</code>"
    if data.hue_color:
        txt += f"\n • <b>Hue Color:</b> <code>{data.hue_color}</code>"
    if data.reason:
        txt += f"\n • <b>Ban Reason:</b> <code>{data.reason}</code>"
    if data.ban_source_url:
        txt += f"\n • <b>Ban Source:</b> <a href='{data.ban_source_url}'>link</a> "
    if data.source_group:
        txt += f"\n • <b>Ban Source:</b> <code>{data.source_group}</code>"
    if data.message:
        txt += f"\n • <b>Ban Message:</b> {data.message}"

    txt += "\n\nPowered by @SibylSystem | @Kaizoku"

    if data.banned:
        keyboard = [[InlineKeyboardButton("Appeal your ban", url="https://t.me/SibylRobot",)]]
        reply_markup = InlineKeyboardMarkup(keyboard)

    update.effective_message.reply_text(
            txt, parse_mode=ParseMode.HTML, reply_markup=reply_markup, disable_web_page_preview=True)
