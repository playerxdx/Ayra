# admin status module by Luke (@itsLuuke - t.me/itsLuuke)
# written for OdinRobot
# copyright 2022
# this module contains various helper functions/classes to help with the admin status module
import json
from enum import Enum
from typing import List, Any, Dict

from cachetools import TTLCache

from telegram import CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, ParseMode, Message, Update, message, \
	ChatMember
from telegram.utils.types import JSONDict

from tg_bot import OWNER_ID, SYS_ADMIN, DEV_USERS, MOD_USERS, SUDO_USERS, SUPPORT_USERS, WHITELIST_USERS, redis, \
	dispatcher

# stores admin in memory for 10 min.
ADMINS_CACHE = TTLCache(maxsize = 512, ttl = 60 * 30)

# stores bot admin status in memory for 10 min.
BOT_ADMIN_CACHE = TTLCache(maxsize = 512, ttl = 60 * 30)

DEV_USERS = DEV_USERS

SUDO_USERS = SUDO_USERS + DEV_USERS

WHITELIST_USERS = WHITELIST_USERS + SUDO_USERS

SUPPORT_USERS = SUPPORT_USERS + SUDO_USERS

MOD_USERS = MOD_USERS + SUDO_USERS


class AdminPerms(Enum):
	CAN_RESTRICT_MEMBERS = 'can_restrict_members'
	CAN_PROMOTE_MEMBERS = 'can_promote_members'
	CAN_INVITE_USERS = 'can_invite_users'
	CAN_DELETE_MESSAGES = 'can_delete_messages'
	CAN_CHANGE_INFO = 'can_change_info'
	CAN_PIN_MESSAGES = 'can_pin_messages'
	IS_ANONYMOUS = 'is_anonymous'


class ChatStatus(Enum):
	CREATOR = "creator"
	ADMIN = "administrator"


# class SuperUsers(Enum):
# 	Owner = [OWNER_ID]
# 	SysAdmin = [OWNER_ID, SYS_ADMIN]
# 	Devs = DEV_USERS
# 	Sudos = SUDO_USERS
# 	Supports = SUPPORT_USERS
# 	Whitelist = WHITELIST_USERS
# 	Mods = MOD_USERS


def anon_reply_markup(cb_id: str) -> InlineKeyboardMarkup:
	return InlineKeyboardMarkup(
			[
				[
					InlineKeyboardButton(
							text = 'Prove identity',
							callback_data = cb_id
					)
				]
			]
	)


anon_reply_text = "Seems like you're anonymous, click the button below to prove your identity"


def edit_anon_msg(msg: Message, text: str):
	"""
	edit anon check message and remove the button
	"""
	msg.edit_text(text, parse_mode = ParseMode.MARKDOWN, reply_markup = None)


def user_is_not_admin_errmsg(msg: Message, permission: AdminPerms = None, cb: CallbackQuery = None):
	if permission.value:
		errmsg = f"You lack the following permission for this command:\n`{permission.value}`!"
	else:
		errmsg = f"You lack the necessary permission needed for this command!"
	if cb:
		return cb.answer(errmsg, show_alert = True)
	return msg.reply_text(errmsg, parse_mode = ParseMode.MARKDOWN)


def button_expired_error(u: Update):
	errmsg = f"This button has expired!"
	if u.callback_query:
		u.callback_query.answer(errmsg, show_alert = True)
		u.effective_message.delete()
		return
	return u.effective_message.edit_text(errmsg, parse_mode = ParseMode.MARKDOWN)


def get_admin_item(chat_id: int) -> Dict[int, JSONDict]:
	data = redis.get(f"admin{chat_id}")
	if data:
		return json.loads(data)
	else:
		raise KeyError


def get_bot_admin_item(chat_id: int) -> ChatMember:
	data = redis.get(f"bot_admin{chat_id}")
	if data:
		return ChatMember.de_json(data=json.loads(data), bot=dispatcher.bot)
	else:
		raise KeyError


def set_admin_item(chat_id: int, data: Dict[int, ChatMember]) -> None:
	redis.set(f"admin{chat_id}", json.dumps(data))


def set_bot_admin_item(chat_id: int, data: ChatMember) -> None:
	redis.set(f"bot_admin{chat_id}", data.to_json())


def get_callback(chat_id: int, message_id: int):
	return json.loads(redis.get(f"cb{message_id}{chat_id}"))


def set_callback(chat_id: int, message_id: int, data) -> None:
	redis.set(f"cb{message_id}{chat_id}", json.dumps(data))


anon_callbacks = {}
