# from AstrakoBot
from asyncio import sleep

from .helper_funcs.decorators import register
from .sql.clear_cmd_sql import get_clearcmd
from .helper_funcs.telethn.chatstatus import user_is_admin, user_can_ban
from .helper_funcs.misc import delete


@register(pattern='zombies', groups_only=True)

async def zombies(event):
    chat = await event.get_chat()
    chat_id = event.chat_id
    admin = chat.admin_rights
    creator = chat.creator

    if not await user_is_admin(
            user_id=event.sender_id, message=event):
        await event.reply("Only Admins are allowed to use this command")
        return

    if not await user_can_ban(user_id=event.sender_id, message=event):
        await event.reply("You don't have the permission to remove users")
        return

    elif not admin and not creator:
        delmsg = "I am not an admin here!"

    else:

        count = 0
        arg = event.pattern_match.group(2)

        if not arg:
                msg = "**Searching for zombies...**\n"
                msg = await event.reply(msg)
                async for user in event.client.iter_participants(event.chat):
                    if user.deleted:
                        count += 1

                if count == 0:
                    delmsg = await msg.edit("No deleted accounts found. Group is clean")
                else:
                    delmsg = await msg.edit(f"Found **{count}** zombies in this group\nClean them by using - `/zombies clean`")
        
        elif arg == "clean":
            msg = "**Cleaning zombies...**\n"
            msg = await event.reply(msg)
            async for user in event.client.iter_participants(event.chat):
                if user.deleted and not await user_is_admin(user_id = user, message = event):
                    count += 1
                    await event.client.kick_participant(chat, user)

            if count == 0:
                delmsg = await msg.edit("No deleted accounts found. Group is clean")
            else:
                delmsg = await msg.edit(f"Cleaned `{count}` zombies")
      
        else:
            delmsg = await event.reply("Wrong parameter. You can use only `/zombies clean`")


    cleartime = get_clearcmd(chat_id, "zombies")

    if cleartime:
        await sleep(cleartime.time)
        await delmsg.delete()

