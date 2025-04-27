import logging
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton

from database import db
from states import user_states
from utils import helpers

logger = logging.getLogger(__name__)

def register_common_handlers(bot: AsyncTeleBot):
    @bot.message_handler(commands=['start'])
    async def start_command(message: Message):
        user_id = message.from_user.id
        username = message.from_user.username or f"user_{user_id}"
        
        await db.add_user(user_id, username)
        
        if helpers.is_admin(user_id):
            markup = helpers.get_main_menu_markup(user_id)
            
            await bot.send_message(
                user_id,
                "*🐵 Добро пожаловать в бот!*  \nВы вошли как администратор.",
                reply_markup=markup,
                parse_mode="Markdown"
            )
        else:
            rooms = await db.get_user_rooms(user_id)
            
            if not rooms:
                markup = helpers.get_main_menu_markup(user_id)
                
                await bot.send_message(
                    user_id,
                    "*🙈 Доброго времени суток!*  \n"
                    "У вас пока нет доступных комнат. Ожидайте, когда администратор добавит вас в комнату.",
                    reply_markup=markup,
                    parse_mode="Markdown"
                )
            elif len(rooms) == 1:
                room = rooms[0]
                room_id = room['room_id']
                
                user_states.set_active_room(user_id, room_id)
                
                markup = helpers.get_room_exit_markup()
                
                await bot.send_message(
                    user_id,
                    f"*🐵 Доброго времени суток!*  \n\n"
                    f"Вы автоматически вошли в комнату: {room['name']}  \n"
                    f"Все сообщения будут отправлены другим участникам комнаты.  \n"
                    f"Нажмите кнопку ниже, чтобы выйти из комнаты.",
                    reply_markup=markup,
                    parse_mode="Markdown"
                )
            else:
                markup = InlineKeyboardMarkup(row_width=1)
                for room in rooms:
                    markup.add(InlineKeyboardButton(
                        room['name'], 
                        callback_data=f"enter_room_{room['room_id']}"
                    ))
                    
                await bot.send_message(
                    user_id,
                    "*🙈 Добро пожаловать в бот Monkey Studio!*  \n\n"
                    "У вас есть несколько доступных комнат. Выберите комнату для входа:",
                    reply_markup=markup,
                    parse_mode="Markdown"
                )
    
    @bot.callback_query_handler(func=lambda call: call.data == "view_rooms")
    async def view_rooms_callback(call: CallbackQuery):
        user_id = call.from_user.id
        rooms = await db.get_user_rooms(user_id)
        
        if not rooms:
            await bot.answer_callback_query(call.id)
            
            markup = helpers.get_back_to_main_menu_markup()
            
            await bot.send_message(
                user_id, 
                "У вас пока нет доступных комнат.",
                reply_markup=markup
            )
            return
        
        markup = InlineKeyboardMarkup(row_width=1)
        for room in rooms:
            markup.add(InlineKeyboardButton(
                room['name'], 
                callback_data=f"enter_room_{room['room_id']}"
            ))
        markup.add(InlineKeyboardButton("Главное меню", callback_data="main_menu"))
        
        await bot.answer_callback_query(call.id)
        await bot.send_message(
            user_id,
            "Ваши доступные комнаты:",
            reply_markup=markup
        )
    
    @bot.callback_query_handler(func=lambda call: call.data == "main_menu")
    async def main_menu_callback(call: CallbackQuery):
        user_id = call.from_user.id
        
        markup = helpers.get_main_menu_markup(user_id)
        
        await bot.answer_callback_query(call.id)
        await bot.send_message(
            user_id,
            "Главное меню:",
            reply_markup=markup
        )
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith("enter_room_"))
    async def enter_room_callback(call: CallbackQuery):
        user_id = call.from_user.id
        room_id = int(call.data.split("_")[2])
        
        if not await db.is_user_in_room(user_id, room_id):
            await bot.answer_callback_query(call.id, "У вас нет доступа к этой комнате.")
            return
        
        room = await db.get_room_by_id(room_id)
        if not room:
            await bot.answer_callback_query(call.id, "Комната не найдена.")
            return
        
        user_states.set_active_room(user_id, room_id)
        
        markup = helpers.get_room_exit_markup()
        
        await bot.answer_callback_query(call.id)
        await bot.send_message(
            user_id,
            f"Вы вошли в комнату: {room['name']}\n"
            f"Все сообщения будут отправлены другим участникам комнаты.\n"
            f"Нажмите кнопку ниже, чтобы выйти из комнаты.",
            reply_markup=markup
        )
    
    @bot.callback_query_handler(func=lambda call: call.data == "exit_room")
    async def exit_room_callback(call: CallbackQuery):
        user_id = call.from_user.id
        
        if not user_states.is_user_in_active_room(user_id):
            await bot.answer_callback_query(call.id, "Вы не находитесь ни в одной комнате.")
            return
        
        user_states.clear_active_room(user_id)
        
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("Мои комнаты", callback_data="view_rooms"),
            InlineKeyboardButton("Главное меню", callback_data="main_menu")
        )
        
        await bot.answer_callback_query(call.id)
        await bot.send_message(
            user_id,
            "Вы вышли из комнаты.",
            reply_markup=markup
        )
