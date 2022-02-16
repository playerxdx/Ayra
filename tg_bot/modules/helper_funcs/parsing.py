import re
from enum import IntEnum, unique
from typing import Optional, Union

from telegram import Message
from telegram.inline.inlinekeyboardmarkup import InlineKeyboardMarkup

from tg_bot.modules.sql.notes_sql import Buttons


BTN_LINK_REGEX = re.compile(
        r"(?<!\\)\[(.+?)\]\(((?!b(?:utto|t)nurl:).+?)\)|(?m)^(\n?\[(.+?)\]\(b(?:utto|t)nurl:(?:/*)?(.+?)(:same)?\))$"
)


@unique
class Types(IntEnum):
    TEXT = 0
    BUTTON_TEXT = 1
    STICKER = 2
    DOCUMENT = 3
    PHOTO = 4
    AUDIO = 5
    VOICE = 6
    VIDEO = 7
    VIDEO_NOTE = 8


def get_data(
        msg: Message, welcome: bool = False
             ) -> tuple[str, str, Types, Optional[str], Union[str, list[Optional[tuple[str, Optional[str], bool]]]]]:
    data_type: Types = Types.TEXT
    content: Optional[str] = None
    text: str = ""
    raw_text: str = msg.text_html or msg.caption_html
    args: list[str] = raw_text.split(None, 2 if not welcome else 1)  # use python's maxsplit to separate cmd and args
    note_name: str = args[1] if not welcome else ""

    buttons: Union[str, list[Optional[tuple[str, Optional[str], bool]]]] = []
    # determine what the contents of the filter are - text, image, sticker, etc
    if len(args) >= 3:
        text, buttons = parser(args[2])

    elif len(args) >= 2 and welcome:
        text, buttons = parser(args[1])

        data_type = Types.BUTTON_TEXT if buttons else Types.TEXT

    elif msg.reply_to_message:
        msgtext = msg.reply_to_message.text_html or msg.reply_to_message.caption_html
        if len(args) >= 2 and msg.reply_to_message.text_html:  # not caption, text
            text, buttons = parser(msgtext, reply_markup=msg.reply_to_message.reply_markup)
            data_type = Types.BUTTON_TEXT if buttons else Types.TEXT
        elif msg.reply_to_message.sticker:
            content = msg.reply_to_message.sticker.file_id
            data_type = Types.STICKER

        elif msg.reply_to_message.document:
            content = msg.reply_to_message.document.file_id
            text, buttons = parser(msgtext)
            data_type = Types.DOCUMENT

        elif msg.reply_to_message.photo:
            content = msg.reply_to_message.photo[-1].file_id  # last elem = best quality
            text, buttons = parser(msgtext)
            data_type = Types.PHOTO

        elif msg.reply_to_message.audio:
            content = msg.reply_to_message.audio.file_id
            text, buttons = parser(msgtext)
            data_type = Types.AUDIO

        elif msg.reply_to_message.voice:
            content = msg.reply_to_message.voice.file_id
            text, buttons = parser(msgtext)
            data_type = Types.VOICE

        elif msg.reply_to_message.video:
            content = msg.reply_to_message.video.file_id
            text, buttons = parser(msgtext)
            data_type = Types.VIDEO

    if buttons and not text:
        text = note_name

    return note_name, text, data_type, content, buttons


def parser(
        txt: str, reply_markup: InlineKeyboardMarkup = None
) -> tuple[str, Union[str, list[Optional[tuple[str, Optional[str], bool]]]]]:
    markdown_note = txt
    buttons: Union[str, list[Optional[tuple[str, Optional[str], bool]]]] = []
    prev = 0
    note_data = ""
    if reply_markup:
        for btn in reply_markup.inline_keyboard:
            buttons.append((btn[0].text, btn[0].url, False))
            if len(btn) >= 2:
                buttons.extend((a.text, a.url, True) for a in btn[1:])

    for match in BTN_LINK_REGEX.finditer(markdown_note):
        if match.group(1):
            note_data += markdown_note[prev:match.start(1) - 1]
            note_data += f"<a href=\"{match.group(2)}\">{match.group(1)}</a>"
            prev = match.end(2) + 1
        else:
            buttons.append((match.group(4), match.group(5), bool(match.group(5))))
            note_data += markdown_note[prev: match.start(3)].rstrip()
            prev = match.end(3)

    note_data += markdown_note[prev:]
    final_text = Md2HTML(note_data)

    return final_text, buttons


def Md2HTML(text: str) -> str:
    _pre_re = re.compile(r'`{3}(.*?[^\s].*?)`{3}', re.DOTALL)
    _code_re = re.compile(r'`(.*?[^\s].*?)`')
    _bold_re = re.compile(r'\*(.*?[^\s].*?)\*')
    _underline_re = re.compile(r'__(.*?[^\s].*?)__')
    _italic_re = re.compile(r'_(.*?[^\s].*?)_')
    _strike_re = re.compile(r'~(.*?[^\s].*?)~')
    _spoiler_re = re.compile(r'\|\|(.*?[^\s].*?)\|\|')

    def _pre_repl(match):
        return f'<pre>{match.group(1)}</pre>'

    def _code_repl(match):
        return f'<code>{match.group(1)}</code>'

    def _bold_repl(match):
        return f'<b>{match.group(1)}</b>'

    def _underline_repl(match):
        return f'<u>{match.group(1)}</u>'

    def _italic_repl(match):
        return f'<i>{match.group(1)}</i>'

    def _strike_repl(match):
        return f'<s>{match.group(1)}</s>'

    def _spoiler_repl(match):
        return f'<span class="tg-spoiler">{match.group(1)}</span>'

    text = _pre_re.sub(_pre_repl, text)
    text = _code_re.sub(_code_repl, text)
    text = _bold_re.sub(_bold_repl, text)
    text = _underline_re.sub(_underline_repl, text)
    text = _italic_re.sub(_italic_repl, text)
    text = _strike_re.sub(_strike_repl, text)
    text = _spoiler_re.sub(_spoiler_repl, text)

    return text


def revertMd2HTML(text: str, buttons: Buttons) -> str:
    _pre_re = re.compile(r'<pre>(.*?[^\s].*?)</pre>', re.DOTALL)
    _code_re = re.compile(r'<code>(.*?[^\s].*?)</code>')
    _bold_re = re.compile(r'<b>(.*?[^\s].*?)</b>')
    _underline_re = re.compile(r'<u>(.*?[^\s].*?)</u>')
    _italic_re = re.compile(r'<i>(.*?[^\s].*?)</i>')
    _strike_re = re.compile(r'<s>(.*?[^\s].*?)</s>')
    _spoiler_re = re.compile(r'<span class="tg-spoiler">(.*?[^\s].*?)</span>')
    _link_re = re.compile(r'<a href="(.*?[^\s].*?)">(.*?[^\s].*?)</a>')

    def _pre_repl(match):
        return f'```{match.group(1)}```'

    def _code_repl(match):
        return f'`{match.group(1)}`'

    def _bold_repl(match):
        return f'*{match.group(1)}*'

    def _underline_repl(match):
        return f'__{match.group(1)}__'

    def _italic_repl(match):
        return f'_{match.group(1)}_'

    def _strike_repl(match):
        return f'~{match.group(1)}~'

    def _spoiler_repl(match):
        return f'||{match.group(1)}||'

    def _link_repl(match):
        return f"[{match.group(2)}]({match.group(1)})"

    def _buttons_repl(txt, btns):
        return txt + "".join(f"\n[{i.name}](buttonurl://{i.url}{':same' if i.same_line else ''})" for i in btns)

    text = _pre_re.sub(_pre_repl, text)
    text = _code_re.sub(_code_repl, text)
    text = _bold_re.sub(_bold_repl, text)
    text = _underline_re.sub(_underline_repl, text)
    text = _italic_re.sub(_italic_repl, text)
    text = _strike_re.sub(_strike_repl, text)
    text = _spoiler_re.sub(_spoiler_repl, text)
    text = _link_re.sub(_link_repl, text)

    if buttons:
        text = _buttons_repl(text, buttons)

    return text
