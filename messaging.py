import logging
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from database import db
from states import user_states
from utils import helpers
import config

logger = logging.getLogger(__name__)

import logging
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message

from database import db
from states import user_states
from utils import helpers
import config

logger = logging.getLogger(__name__)

def register_messaging_handlers(bot: AsyncTeleBot):
    @bot.message_handler(
        func=lambda message: user_states.is_user_in_active_room(message.from_user.id) and message.content_type == 'text'
    )
    async def handle_text(message: Message):
        user_id = message.from_user.id
        room_id = user_states.get_active_room(user_id)

        await db.save_message(room_id, user_id, message.text)

        is_admin = helpers.is_admin(user_id)
        room_role = await db.get_user_role_in_room(user_id, room_id)
        sender_title = helpers.get_sender_title(is_admin, "admin" if is_admin else room_role)

        other_members = await db.get_other_room_members(room_id, user_id)
        if not other_members:
            await bot.send_message(user_id, "В комнате нет других участников.")
            return

        for member in other_members:
            try:
                await bot.send_message(member['user_id'], f"{sender_title}:\n{message.text}")
            except Exception as e:
                logger.error(f"Не удалось переслать текст участнику {member['user_id']}: {e}")

    @bot.message_handler(
        func=lambda m: user_states.is_user_in_active_room(m.from_user.id),
        content_types=[
            'text', 'photo', 'video', 'audio', 'voice', 'document',
            'sticker', 'animation', 'video_note', 'location', 'contact', 'venue'
        ]
    )
    async def relay_room_message(message: Message):
        user_id = message.from_user.id
        room_id = user_states.get_active_room(user_id)

        is_admin = helpers.is_admin(user_id)
        room_role = await db.get_user_role_in_room(user_id, room_id)
        sender_title = helpers.get_sender_title(
            is_admin, "admin" if is_admin else room_role
        )

        other_members = await db.get_other_room_members(room_id, user_id)
        if not other_members:
            await bot.send_message(user_id, "В комнате нет других участников.")
            return

        ctype = message.content_type
        if ctype == 'text':
            db_text = message.text
        elif ctype in ('photo', 'video', 'audio', 'voice', 'document', 'animation'):
            caption = message.caption or ''
            db_text = f"[{ctype.upper()}] {caption}"
        elif ctype == 'sticker':
            db_text = "[STICKER]"
        elif ctype == 'video_note':
            db_text = "[VIDEO_NOTE]"
        elif ctype in ('location', 'contact', 'venue'):
            db_text = f"[{ctype.upper()}]"
        else:
            db_text = f"[{ctype.upper()}]"

        await db.save_message(room_id, user_id, db_text)

        for member in other_members:
            to_id = member['user_id']
            try:
                if ctype == 'text':
                    await bot.send_message(to_id, f"{sender_title}:\n{message.text}")
                elif ctype == 'photo':
                    file_id = message.photo[-1].file_id
                    await bot.send_photo(to_id, file_id, caption=f"{sender_title}:\n{message.caption or ''}")
                elif ctype == 'video':
                    await bot.send_video(to_id, message.video.file_id,
                                        caption=f"{sender_title}:\n{message.caption or ''}")
                elif ctype == 'animation':
                    await bot.send_animation(to_id, message.animation.file_id,
                                            caption=f"{sender_title}:\n{message.caption or ''}")
                elif ctype == 'audio':
                    await bot.send_audio(to_id, message.audio.file_id,
                                        caption=f"{sender_title}:\n{message.caption or ''}")
                elif ctype == 'voice':
                    await bot.send_voice(to_id, message.voice.file_id,
                                        caption=f"{sender_title}:\n")
                elif ctype == 'document':
                    await bot.send_document(to_id, message.document.file_id,
                                           caption=f"{sender_title}:\n{message.caption or ''}")
                elif ctype == 'sticker':
                    await bot.send_sticker(to_id, message.sticker.file_id)
                elif ctype == 'video_note':
                    await bot.send_video_note(to_id, message.video_note.file_id)
                elif ctype == 'location':
                    await bot.send_location(to_id,
                                            latitude=message.location.latitude,
                                            longitude=message.location.longitude)
                elif ctype == 'contact':
                    await bot.send_contact(to_id,
                                          phone_number=message.contact.phone_number,
                                          first_name=message.contact.first_name,
                                          last_name=message.contact.last_name)
                elif ctype == 'venue':
                    await bot.send_venue(to_id,
                                        latitude=message.venue.location.latitude,
                                        longitude=message.venue.location.longitude,
                                        title=message.venue.title,
                                        address=message.venue.address)
                else:
                    await bot.forward_message(to_id, user_id, message.message_id)
            except Exception as e:
                logger.error(f"Не удалось отправить {ctype} участнику {to_id}: {e}")
    
    @bot.message_handler(func=lambda message: True)
    async def default_handler(message: Message):
        user_id = message.from_user.id

        if (not user_states.is_user_in_active_room(user_id) and 
            user_states.get_user_state(user_id) == user_states.AdminState.IDLE):

            commands = [
                "/start - Начать работу с ботом"
            ]
            markup = helpers.get_main_menu_markup(user_id)

            await bot.send_message(
                user_id,
                "Доступные команды:\n" + "\n".join(commands),
                reply_markup=markup
            )