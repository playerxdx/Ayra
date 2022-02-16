# ported from ProjectFizilion

import asyncio

from telethon import events
from tg_bot import OWNER_ID, SYS_ADMIN, telethn
from .helper_funcs.decorators import register

@register(pattern="(log|log@OdinRobot)(?: |$)(.*)", from_users=[SYS_ADMIN, OWNER_ID], raw=True)
# @telethn.on(events.NewMessage(pattern=f"^[!/>]log(?: |$)([\s\S]*)", from_users=OWNER_ID))
async def log(event):
    if event.reply_to_msg_id:
        reply_msg = await event.get_reply_message()
        await reply_msg.forward_to(OWNER_ID)
    elif event.pattern_match.group(2):
        user = f"#LOG / From: {event.chat_id}\n\n"
        textx = user + event.pattern_match.group(1)
        await telethn.send_message(OWNER_ID, textx)
    else:
        aaa = await event.edit("`What am I supposed to log?`")
        await asyncio.sleep(2)
        await aaa.delete()
        return 
    aaa = await event.reply("`Logged Successfully`")

    await asyncio.sleep(2)
    try:
        await aaa.delete()
    except:
        pass

