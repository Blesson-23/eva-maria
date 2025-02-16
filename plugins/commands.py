import os
import logging
import random
import asyncio
import requests
import traceback
import re
import json
import base64
import sys

from aiohttp import ClientSession
from asyncio import get_running_loop
from io import BytesIO
from googletrans import Translator
from gtts import gTTS
from Script import script
from function import make_carbon
from pyrogram import Client, filters
from pyrogram.errors import ChatAdminRequired, FloodWait
from pyrogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from database.ia_filterdb import Media, get_file_details, unpack_new_file_id
from database.users_chats_db import db
from info import CHANNELS, ADMINS, AUTH_CHANNEL, LOG_CHANNEL, PICS, BATCH_FILE_CAPTION, CUSTOM_FILE_CAPTION, PROTECT_CONTENT
from utils import get_settings, get_size, is_subscribed, save_group_settings, temp
from database.connections_mdb import active_connection

logger = logging.getLogger(__name__)

BATCH_FILES = {}
aiohttpsession = ClientSession()
API = "https://apis.xditya.me/lyrics?song="

Langs ="""**Available Languages**
    `'af': 'afrikaans',
    'sq': 'albanian',
    'am': 'amharic',
    'ar': 'arabic',
    'hy': 'armenian',
    'az': 'azerbaijani',
    'eu': 'basque',
    'be': 'belarusian',
    'bn': 'bengali',
    'bs': 'bosnian',
    'bg': 'bulgarian',
    'ca': 'catalan',
    'ceb': 'cebuano',
    'ny': 'chichewa',
    'zh-cn': 'chinese (simplified)',
    'zh-tw': 'chinese (traditional)',
    'co': 'corsican',
    'hr': 'croatian',
    'cs': 'czech',
    'da': 'danish',
    'nl': 'dutch',
    'en': 'english',
    'eo': 'esperanto',
    'et': 'estonian',
    'tl': 'filipino',
    'fi': 'finnish',
    'fr': 'french',
    'fy': 'frisian',
    'gl': 'galician',
    'ka': 'georgian',
    'de': 'german',
    'el': 'greek',
    'gu': 'gujarati',
    'ht': 'haitian creole',
    'ha': 'hausa',
    'haw': 'hawaiian',
    'iw': 'hebrew',
    'he': 'hebrew',
    'hi': 'hindi',
    'hmn': 'hmong',
    'hu': 'hungarian',
    'is': 'icelandic',
    'ig': 'igbo',
    'id': 'indonesian',
    'ga': 'irish',
    'it': 'italian',
    'ja': 'japanese',
    'jw': 'javanese',
    'kn': 'kannada',
    'kk': 'kazakh',
    'km': 'khmer',
    'ko': 'korean',
    'ku': 'kurdish (kurmanji)',
    'ky': 'kyrgyz',
    'lo': 'lao',
    'la': 'latin',
    'lv': 'latvian',
    'lt': 'lithuanian',
    'lb': 'luxembourgish',
    'mk': 'macedonian',
    'mg': 'malagasy',
    'ms': 'malay',
    'ml': 'malayalam',
    'mt': 'maltese',
    'mi': 'maori',
    'mr': 'marathi',
    'mn': 'mongolian',
    'my': 'myanmar (burmese)',
    'ne': 'nepali',
    'no': 'norwegian',
    'or': 'odia',
    'ps': 'pashto',
    'fa': 'persian',
    'pl': 'polish',
    'pt': 'portuguese',
    'pa': 'punjabi',
    'ro': 'romanian',
    'ru': 'russian',
    'sm': 'samoan',
    'gd': 'scots gaelic',
    'sr': 'serbian',
    'st': 'sesotho',
    'sn': 'shona',
    'sd': 'sindhi',
    'si': 'sinhala',
    'sk': 'slovak',
    'sl': 'slovenian',
    'so': 'somali',
    'es': 'spanish',
    'su': 'sundanese',
    'sw': 'swahili',
    'sv': 'swedish',
    'tg': 'tajik',
    'ta': 'tamil',
    'te': 'telugu',
    'th': 'thai',
    'tr': 'turkish',
    'uk': 'ukrainian',
    'ur': 'urdu',
    'ug': 'uyghur',
    'uz': 'uzbek',
    'vi': 'vietnamese',
    'cy': 'welsh',
    'xh': 'xhosa',
    'yi': 'yiddish',
    'yo': 'yoruba',
    'zu': 'zulu'`"""

@Client.on_message(filters.command("start") & filters.incoming & ~filters.edited)
async def start(client, message):
    try:
        if message.chat.type in ['group', 'supergroup']:
            buttons = [
                [
                    InlineKeyboardButton('♦️Updates', url='https://t.me/xdsupport')
                ],
                [
                    InlineKeyboardButton('🔆 Help', url=f"https://t.me/{temp.U_NAME}?start=help"),
                ]
                ]
            reply_markup = InlineKeyboardMarkup(buttons)
            await message.reply(script.START_TXT.format(message.from_user.mention if message.from_user else message.chat.title, temp.U_NAME, temp.B_NAME), reply_markup=reply_markup)
            await asyncio.sleep(2) # 😢 https://github.com/EvamariaTG/EvaMaria/blob/master/plugins/p_ttishow.py#L17 😬 wait a bit, before checking.
            if not await db.get_chat(message.chat.id):
                total=await client.get_chat_members_count(message.chat.id)
                await client.send_message(LOG_CHANNEL, script.LOG_TEXT_G.format(message.chat.title, message.chat.id, total, "Unknown"))       
                await db.add_chat(message.chat.id, message.chat.title)
            return 
        if not await db.is_user_exist(message.from_user.id):
            await db.add_user(message.from_user.id, message.from_user.first_name)
            await client.send_message(LOG_CHANNEL, script.LOG_TEXT_P.format(message.from_user.id, message.from_user.mention))
        if len(message.command) != 2:
            buttons = [[
                InlineKeyboardButton('⬛️𝘈𝘋𝘋 𝘔𝘌 𝘛𝘖 𝘠𝘖𝘜𝘙 𝘎𝘙𝘖𝘜𝘗', url=f'http://t.me/{temp.U_NAME}?startgroup=true')
                ],[
                InlineKeyboardButton('🔎 Search', switch_inline_query_current_chat='')
                ],[
                InlineKeyboardButton('🌈Help', callback_data='help'),
                InlineKeyboardButton('📣about', callback_data='about')
            ]]
            reply_markup = InlineKeyboardMarkup(buttons)
            await message.reply_sticker(
                sticker="CAACAgUAAxkBAAEER65i3VOkR5v5cKMvXF7MhrxDRnEc1gAC-AYAAnly6VZVNMIwo-_zvh4E",
               # caption=script.START_TXT.format(message.from_user.mention, temp.U_NAME, temp.B_NAME),
                reply_markup=reply_markup
                #parse_mode='html'
            )
            return
        if AUTH_CHANNEL and not await is_subscribed(client, message):
            try:
                invite_link = await client.create_chat_invite_link(int(AUTH_CHANNEL))
            except ChatAdminRequired:
                logger.error("Make sure Bot is admin in Forcesub channel")
                return
            btn = [
                [
                    InlineKeyboardButton(
                        "🤖 Join Updates Channel", url=invite_link.invite_link
                    )
                ]
            ]

            if message.command[1] != "subscribe":
                kk, file_id = message.command[1].split("_", 1)
                pre = 'checksubp' if kk == 'filep' else 'checksub' 
                btn.append([InlineKeyboardButton("ഒന്നുടെ try ചെയ്യു 🥺", callback_data=f"{pre}#{file_id}")])
            await client.send_message(
                chat_id=message.from_user.id,
                text="**Please Join My Updates Channel to use this Bot!**",
                reply_markup=InlineKeyboardMarkup(btn),
                parse_mode="markdown"
                )
            return
        if len(message.command) == 2 and message.command[1] in ["subscribe", "error", "okay", "help"]:
            buttons = [[
                InlineKeyboardButton(' 🟥𝘈𝘋𝘋 𝘔𝘌 𝘛𝘖 𝘠𝘖𝘜𝘙 𝘎𝘙𝘖𝘜𝘗 ➕', url=f'http://t.me/{temp.U_NAME}?startgroup=true')
                ],[
                InlineKeyboardButton('🔎 Search', switch_inline_query_current_chat='')
                ],[
                InlineKeyboardButton('🌈Help', callback_data='help'),
                InlineKeyboardButton('📣about', callback_data='about')
            ]]
            reply_markup = InlineKeyboardMarkup(buttons)
            await message.reply_sticker(
                sticker="CAACAgUAAxkBAAEER65i3VOkR5v5cKMvXF7MhrxDRnEc1gAC-AYAAnly6VZVNMIwo-_zvh4E",
              #  caption=script.START_TXT.format(message.from_user.mention, temp.U_NAME, temp.B_NAME),
                reply_markup=reply_markup
                #parse_mode='html'
            )
            return
        data = message.command[1]
        try:
            pre, file_id = data.split('_', 1)
        except:
            file_id = data
            pre = ""
        if data.split("-", 1)[0] == "BATCH":
            sts = await message.reply("Please wait")
            file_id = data.split("-", 1)[1]
            msgs = BATCH_FILES.get(file_id)
            if not msgs:
                file = await client.download_media(file_id)
                try: 
                    with open(file) as file_data:
                        msgs=json.loads(file_data.read())
                except:
                    await sts.edit("FAILED")
                    return await client.send_message(LOG_CHANNEL, "UNABLE TO OPEN FILE.")
                os.remove(file)
                BATCH_FILES[file_id] = msgs
            for msg in msgs:
                title = msg.get("title")
                size=get_size(int(msg.get("size", 0)))
                f_caption=msg.get("caption", "")
                if BATCH_FILE_CAPTION:
                    try:
                        f_caption=BATCH_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
                    except Exception as e:
                        logger.exception(e)
                        f_caption=f_caption
                if f_caption is None:
                    f_caption = f"{title}"
                try:
                    await client.send_cached_media(
                        chat_id=message.from_user.id,
                        file_id=msg.get("file_id"),
                        caption=f_caption,
                        protect_content=msg.get('protect', False),
                        )
                except FloodWait as e:
                    await asyncio.sleep(e.x)
                    logger.warning(f"Floodwait of {e.x} sec.")
                    await client.send_cached_media(
                        chat_id=message.from_user.id,
                        file_id=msg.get("file_id"),
                        caption=f_caption,
                        protect_content=msg.get('protect', False),
                        )
                except Exception as e:
                    logger.warning(e, exc_info=True)
                    continue
                await asyncio.sleep(1) 
            await sts.delete()
            return
        elif data.split("-", 1)[0] == "DSTORE":
            sts = await message.reply("Please wait")
            b_string = data.split("-", 1)[1]
            decoded = (base64.urlsafe_b64decode(b_string + "=" * (-len(b_string) % 4))).decode("ascii")
            try:
                f_msg_id, l_msg_id, f_chat_id, protect = decoded.split("_", 3)
            except:
                f_msg_id, l_msg_id, f_chat_id = decoded.split("_", 2)
                protect = "/pbatch" if PROTECT_CONTENT else "batch"
            diff = int(l_msg_id) - int(f_msg_id)
            async for msg in client.iter_messages(int(f_chat_id), int(l_msg_id), int(f_msg_id)):
                if msg.media:
                    media = getattr(msg, msg.media)
                    if BATCH_FILE_CAPTION:
                        try:
                            f_caption=BATCH_FILE_CAPTION.format(file_name=getattr(media, 'file_name', ''), file_size=getattr(media, 'file_size', ''), file_caption=getattr(msg, 'caption', ''))
                        except Exception as e:
                            logger.exception(e)
                            f_caption = getattr(msg, 'caption', '')
                    else:
                        media = getattr(msg, msg.media)
                        file_name = getattr(media, 'file_name', '')
                        f_caption = getattr(msg, 'caption', file_name)
                    try:
                        await msg.copy(message.chat.id, caption=f_caption, protect_content=True if protect == "/pbatch" else False)
                    except FloodWait as e:
                        await asyncio.sleep(e.x)
                        await msg.copy(message.chat.id, caption=f_caption, protect_content=True if protect == "/pbatch" else False)
                    except Exception as e:
                        logger.exception(e)
                        continue
                elif msg.empty:
                    continue
                else:
                    try:
                        await msg.copy(message.chat.id, protect_content=True if protect == "/pbatch" else False)
                    except FloodWait as e:
                        await asyncio.sleep(e.x)
                        await msg.copy(message.chat.id, protect_content=True if protect == "/pbatch" else False)
                    except Exception as e:
                        logger.exception(e)
                        continue
                await asyncio.sleep(1) 
            return await sts.delete()        

        files_ = await get_file_details(file_id)           
        if not files_:
            pre, file_id = ((base64.urlsafe_b64decode(data + "=" * (-len(data) % 4))).decode("ascii")).split("_", 1)
            try:
                msg = await client.send_cached_media(
                    chat_id=message.from_user.id,
                    file_id=file_id,
                    protect_content=True if pre == 'filep' else False,
                    )
                filetype = msg.media
                file = getattr(msg, filetype)
                title = file.file_name
                size=get_size(file.file_size)
                f_caption = f"<code>{title}</code>"
                if CUSTOM_FILE_CAPTION:
                    try:
                        f_caption=CUSTOM_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='')
                    except:
                        return
                await msg.edit_caption(f_caption)
                return
            except:
                pass
            return await message.reply('No such file exist.')
        files = files_[0]
        title = files.file_name
        size=get_size(files.file_size)
        f_caption=files.caption
        if CUSTOM_FILE_CAPTION:
            try:
                f_caption=CUSTOM_FILE_CAPTION.format(file_name= '' if title is None else title, file_size='' if size is None else size, file_caption='' if f_caption is None else f_caption)
            except Exception as e:
                logger.exception(e)
                f_caption=f_caption
        if f_caption is None:
            f_caption = f"{files.file_name}"
        await client.send_cached_media(
            chat_id=message.from_user.id,
            file_id=file_id,
            caption=f_caption,
            protect_content=True if pre == 'filep' else False,
            )
    except Exception as e:
        print(e)
                    

@Client.on_message(filters.command('channel') & filters.user(ADMINS))
async def channel_info(bot, message):
           
    """Send basic information of channel"""
    if isinstance(CHANNELS, (int, str)):
        channels = [CHANNELS]
    elif isinstance(CHANNELS, list):
        channels = CHANNELS
    else:
        raise ValueError("Unexpected type of CHANNELS")

    text = '📑 **Indexed channels/groups**\n'
    for channel in channels:
        chat = await bot.get_chat(channel)
        if chat.username:
            text += '\n@' + chat.username
        else:
            text += '\n' + chat.title or chat.first_name

    text += f'\n\n**Total:** {len(CHANNELS)}'

    if len(text) < 4096:
        await message.reply(text)
    else:
        file = 'Indexed channels.txt'
        with open(file, 'w') as f:
            f.write(text)
        await message.reply_document(file)
        os.remove(file)


@Client.on_message(filters.command('logs') & filters.user(ADMINS))
async def log_file(bot, message):
    """Send log file"""
    try:
        await message.reply_document('TelegramBot.log')
    except Exception as e:
        await message.reply(str(e))

@Client.on_message(filters.command('delete') & filters.user(ADMINS))
async def delete(bot, message):
    """Delete file from database"""
    reply = message.reply_to_message
    if reply and reply.media:
        msg = await message.reply("Processing...⏳", quote=True)
    else:
        await message.reply('Reply to file with /delete which you want to delete', quote=True)
        return

    for file_type in ("document", "video", "audio"):
        media = getattr(reply, file_type, None)
        if media is not None:
            break
    else:
        await msg.edit('This is not supported file format')
        return
    
    file_id, file_ref = unpack_new_file_id(media.file_id)

    result = await Media.collection.delete_one({
        '_id': file_id,
    })
    if result.deleted_count:
        await msg.edit('File is successfully deleted from database')
    else:
        file_name = re.sub(r"(_|\-|\.|\+)", " ", str(media.file_name))
        result = await Media.collection.delete_many({
            'file_name': file_name,
            'file_size': media.file_size,
            'mime_type': media.mime_type
            })
        if result.deleted_count:
            await msg.edit('File is successfully deleted from database')
        else:
            # files indexed before https://github.com/EvamariaTG/EvaMaria/commit/f3d2a1bcb155faf44178e5d7a685a1b533e714bf#diff-86b613edf1748372103e94cacff3b578b36b698ef9c16817bb98fe9ef22fb669R39 
            # have original file name.
            result = await Media.collection.delete_many({
                'file_name': media.file_name,
                'file_size': media.file_size,
                'mime_type': media.mime_type
            })
            if result.deleted_count:
                await msg.edit('File is successfully deleted from database')
            else:
                await msg.edit('File not found in database')


@Client.on_message(filters.command('deleteall') & filters.user(ADMINS))
async def delete_all_index(bot, message):
    await message.reply_text(
        'This will delete all indexed files.\nDo you want to continue??',
        reply_markup=InlineKeyboardMarkup(
            [
                [
                    InlineKeyboardButton(
                        text="YES", callback_data="autofilter_delete"
                    )
                ],
                [
                    InlineKeyboardButton(
                        text="CANCEL", callback_data="close_data"
                    )
                ],
            ]
        ),
        quote=True,
    )


@Client.on_callback_query(filters.regex(r'^autofilter_delete'))
async def delete_all_index_confirm(bot, message):
    await Media.collection.drop()
    await message.answer('Piracy Is Crime')
    await message.message.edit('Succesfully Deleted All The Indexed Files.')


@Client.on_message(filters.command('settings'))
async def settings(client, message):
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply(f"You are anonymous admin. Use /connect {message.chat.id} in PM")
    chat_type = message.chat.type

    if chat_type == "private":
        grpid = await active_connection(str(userid))
        if grpid is not None:
            grp_id = grpid
            try:
                chat = await client.get_chat(grpid)
                title = chat.title
            except:
                await message.reply_text("Make sure I'm present in your group!!", quote=True)
                return
        else:
            await message.reply_text("I'm not connected to any groups!", quote=True)
            return

    elif chat_type in ["group", "supergroup"]:
        grp_id = message.chat.id
        title = message.chat.title

    else:
        return

    st = await client.get_chat_member(grp_id, userid)
    if (
            st.status != "administrator"
            and st.status != "creator"
            and str(userid) not in ADMINS
    ):
        return

    settings = await get_settings(grp_id)

    if settings is not None:
        buttons = [
            [
                InlineKeyboardButton(
                    'Filter Button',
                    callback_data=f'setgs#button#{settings["button"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    'Single' if settings["button"] else 'Double',
                    callback_data=f'setgs#button#{settings["button"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'Bot PM',
                    callback_data=f'setgs#botpm#{settings["botpm"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    '✅ Yes' if settings["botpm"] else '❌ No',
                    callback_data=f'setgs#botpm#{settings["botpm"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'File Secure',
                    callback_data=f'setgs#file_secure#{settings["file_secure"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    '✅ Yes' if settings["file_secure"] else '❌ No',
                    callback_data=f'setgs#file_secure#{settings["file_secure"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'IMDB',
                    callback_data=f'setgs#imdb#{settings["imdb"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    '✅ Yes' if settings["imdb"] else '❌ No',
                    callback_data=f'setgs#imdb#{settings["imdb"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'Spell Check',
                    callback_data=f'setgs#spell_check#{settings["spell_check"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    '✅ Yes' if settings["spell_check"] else '❌ No',
                    callback_data=f'setgs#spell_check#{settings["spell_check"]}#{grp_id}',
                ),
            ],
            [
                InlineKeyboardButton(
                    'Welcome',
                    callback_data=f'setgs#welcome#{settings["welcome"]}#{grp_id}',
                ),
                InlineKeyboardButton(
                    '✅ Yes' if settings["welcome"] else '❌ No',
                    callback_data=f'setgs#welcome#{settings["welcome"]}#{grp_id}',
                ),
            ],
        ]

        reply_markup = InlineKeyboardMarkup(buttons)

        await message.reply_text(
            text=f"<b>Change Your Settings for {title} As Your Wish ⚙</b>",
            reply_markup=reply_markup,
            disable_web_page_preview=True,
            parse_mode="html",
            reply_to_message_id=message.message_id
        )



@Client.on_message(filters.command('set_template'))
async def save_template(client, message):
    sts = await message.reply("Checking template")
    userid = message.from_user.id if message.from_user else None
    if not userid:
        return await message.reply(f"You are anonymous admin. Use /connect {message.chat.id} in PM")
    chat_type = message.chat.type

    if chat_type == "private":
        grpid = await active_connection(str(userid))
        if grpid is not None:
            grp_id = grpid
            try:
                chat = await client.get_chat(grpid)
                title = chat.title
            except:
                await message.reply_text("Make sure I'm present in your group!!", quote=True)
                return
        else:
            await message.reply_text("I'm not connected to any groups!", quote=True)
            return

    elif chat_type in ["group", "supergroup"]:
        grp_id = message.chat.id
        title = message.chat.title

    else:
        return

    st = await client.get_chat_member(grp_id, userid)
    if (
            st.status != "administrator"
            and st.status != "creator"
            and str(userid) not in ADMINS
    ):
        return

    if len(message.command) < 2:
        return await sts.edit("No Input!!")
    template = message.text.split(" ", 1)[1]
    await save_group_settings(grp_id, 'template', template)
    await sts.edit(f"Successfully changed template for {title} to\n\n{template}")

# New Commands

def convert(text):
    audio = BytesIO()
    i = Translator().translate(text, dest="en")
    lang = i.src
    tts = gTTS(text, lang=lang)
    audio.name = lang + ".mp3"
    tts.write_to_fp(audio)
    return audio

@Client.on_message(filters.private & filters.command("tts"))
async def tts(bot, message):
    if not message.reply_to_message:
        return await message.reply_text("Reply to some text")
    if not message.reply_to_message.text:
        return await message.reply_text("Reply to some text")
    m = await message.reply_text("`Processing...`")
    text = message.reply_to_message.text
    try:
        loop = get_running_loop()
        audio = await loop.run_in_executor(None, convert, text)
        await message.reply_audio(audio)
        await m.delete()
        audio.close()
    except Exception as e:
        await m.edit(e)
        e = traceback.format_exc()
        print(e)

@Client.on_message(filters.private & filters.command("carbon"))
async def carbon_func(_, message):
    if not message.reply_to_message:
        return await message.reply_text(
            "Reply to some text"
        )
    if not message.reply_to_message.text:
        return await message.reply_text(
            "Reply to some text"
        )
    user_id = message.from_user.id
    m = await message.reply_text("ᴘʀᴏᴄᴇssɪɴɢ...")
    carbon = await make_carbon(message.reply_to_message.text)
    await m.edit("ᴜᴘʟᴏᴀᴅɪɴɢ..")
    await message.reply_photo(
        photo=carbon)
    await m.delete()
    carbon.close()

@Client.on_message(filters.text & filters.command(["lyrics"]))
async def sng(bot, message):
        if not message.reply_to_message:
          await message.reply_text("Please reply to a message")
        else:          
          mee = await message.reply_text("```Searching 🔎```")
          song = message.reply_to_message.text
          chat_id = message.from_user.id
          rpl = lyrics(song)
          await mee.delete()
          try:
            await mee.delete()
            await bot.send_message(chat_id, text = rpl, reply_to_message_id = message.message_id)
          except Exception as e:                            
             await message.reply_text(f"I Can't Find A Song With ```{song}```", quote = True)

def search(song):
        r = requests.get(API + song)
        find = r.json()
        return find
       
def lyrics(song):
        fin = search(song)
        text = f'🎶 Successfully Extracted Lyrics Of {song} 🎶\n\n'
        text += f'`{fin["lyrics"]}`'
        return text

# Translation

@Client.on_message(filters.command("tr"))
async def tr(_, message):
    if len(message.command) != 2:
        await message.reply_text(
            "__Reply to a message with /tr [language code]__"
            + "\n" + Langs
            + "\n\n__Eg:__ `/tr ml`"
        )
        return
    lang = message.text.split(None, 1)[1]
    if not message.reply_to_message or not lang:
        await message.reply_text(
            "__Reply to a message with /tr [language code]__"
            + "\n" + Langs
            + "\n\n__Eg:__ `/tr ml`"
        )
        return
    if message.reply_to_message.text:
        text = message.reply_to_message.text
        msg = await message.reply("__Processing...__")
        try:
            i = Translator().translate(text, dest=lang)
        except ValueError:
            await msg.edit_text("[ERROR]: LANGUAGE NOT FOUND")
            return
        await msg.edit_text(i.text)
    elif message.reply_to_message.caption:
        text = message.reply_to_message.caption
        msg = await message.reply("__Processing...__")
        i = Translator().translate(text, dest=lang)
        await msg.edit_text(i.text)

