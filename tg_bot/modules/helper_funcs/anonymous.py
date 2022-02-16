# admin status module by Luke (@itsLuuke - t.me/itsLuuke)
# written for OdinRobot
# copyright 2022

from telegram import Update
from telegram.ext import CallbackContext as Ctx

from ..helper_funcs.decorators import kigcallback as kigCb

from .admin_status_helpers import anon_callbacks as a_cb, edit_anon_msg as eam
from .admin_status import user_is_admin


@kigCb(pattern = "AnonCB")
def perm_callback_check(upd: Update, _: Ctx):
	callback = upd.callback_query
	chat_id = int(callback.data.split('/')[1])
	message_id = int(callback.data.split('/')[2])
	perm = callback.data.split('/')[3]
	user_id = callback.from_user.id
	msg = upd.effective_message

	mem = user_is_admin(upd, user_id, perm = perm if perm != 'None' else None)

	if not mem:  # not admin or doesn't have the required perm
		eam(msg,
			"You need to be an admin to perform this action!"
			if not perm == 'None'
			else f"You lack the permission: `{perm}`!")
		return

	try:
		cb = a_cb.pop((chat_id, message_id), None)
	except KeyError:
		eam(msg, "This message is no longer valid.")
		return

	msg.delete()

	# update the `Update` and `CallbackContext` attributes by the correct values, so they can be used properly
	setattr(cb[0][0], "_effective_user", upd.effective_user)
	setattr(cb[0][0], "_effective_message", cb[2][0])

	return cb[1](cb[0][0], cb[0][1])  # return func(update, context)
