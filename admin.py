import logging
from telebot.async_telebot import AsyncTeleBot
from telebot.types import Message, CallbackQuery, InlineKeyboardMarkup, InlineKeyboardButton, InputFile

from database import db
from states import user_states
from states.user_states import AdminState
from utils import helpers
import config

logger = logging.getLogger(__name__)

def register_admin_handlers(bot: AsyncTeleBot): 
    @bot.callback_query_handler(func=lambda call: call.data == "admin_panel")
    async def admin_panel_callback(call: CallbackQuery):
        user_id = call.from_user.id
        
        if not helpers.is_admin(user_id):
            await bot.answer_callback_query(call.id, "🙈 У вас нет доступа к этой функции.")
            return
        
        markup = helpers.get_admin_panel_markup()
        
        await bot.answer_callback_query(call.id)
        await bot.send_message(
            user_id,
            "*🐵 Панель администратора:*",
            reply_markup=markup,
            parse_mode="Markdown"
        )
    
    @bot.callback_query_handler(func=lambda call: call.data == "create_room")
    async def create_room_callback(call: CallbackQuery):
        user_id = call.from_user.id
        
        if not helpers.is_admin(user_id):
            await bot.answer_callback_query(call.id, "🙈 У вас нет доступа к этой функции.")
            return
        
        user_states.set_user_state(user_id, AdminState.WAITING_FOR_ROOM_NAME)
        user_states.clear_temp_room_data(user_id)
        
        await bot.answer_callback_query(call.id)
        await bot.send_message(
            user_id,
            "🐒 *Введите название комнаты:*",
            parse_mode="Markdown"
        )
    
    @bot.callback_query_handler(func=lambda call: call.data == "list_rooms")
    async def list_rooms_callback(call: CallbackQuery):
        user_id = call.from_user.id
        
        if not helpers.is_admin(user_id):
            await bot.answer_callback_query(call.id, "🙈 У вас нет доступа к этой функции.")
            return
        
        rooms = await db.get_all_rooms()
        
        if not rooms:
            await bot.answer_callback_query(call.id)
            await bot.send_message(
                user_id,
                "🙉 Комнаты еще не созданы.",
                parse_mode="Markdown"
            )
            return
        
        markup = InlineKeyboardMarkup(row_width=1)
        for room in rooms:
            markup.add(InlineKeyboardButton(
                f"{room['name']} (ID: {room['room_id']})", 
                callback_data=f"room_info_{room['room_id']}"
            ))
        markup.add(InlineKeyboardButton("Назад", callback_data="admin_panel"))
        
        await bot.answer_callback_query(call.id)
        await bot.send_message(
            user_id,
            "*📜 Список всех комнат:*",
            reply_markup=markup,
            parse_mode="Markdown"
        )
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith("room_info_"))
    async def room_info_callback(call: CallbackQuery):
        user_id = call.from_user.id
        
        if not helpers.is_admin(user_id):
            await bot.answer_callback_query(call.id, "🙈 У вас нет доступа к этой функции.")
            return
        
        room_id = int(call.data.split("_")[2])
        room = await db.get_room_by_id(room_id)
        
        if not room:
            await bot.answer_callback_query(call.id, "🙊 Комната не найдена.")
            return
        
        members = await db.get_room_members(room_id)
        members_text = "\n".join([
            f"- {member['username']} (ID: {member['user_id']}, Роль: {member['role']})"
            for member in members
        ])
        
        markup = InlineKeyboardMarkup(row_width=1)
        markup.add(
            InlineKeyboardButton("▶️ Войти в комнату", callback_data=f"admin_enter_room_{room_id}"),
            InlineKeyboardButton("📤 Экспорт истории", callback_data=f"export_history_{room_id}"),
            InlineKeyboardButton("🗑️ Удалить комнату", callback_data=f"delete_room_{room_id}"),
            InlineKeyboardButton("◀️ Назад к списку", callback_data="list_rooms"),
            InlineKeyboardButton("🏠 Главное меню", callback_data="main_menu")
        )
        
        await bot.answer_callback_query(call.id)
        await bot.send_message(
            user_id,
            f"*ℹ️ Информация о комнате:*  \n"
            f"• *ID:* `{room['room_id']}`  \n"
            f"• *Название:* _{room['name']}_  \n"
            f"• *Создана:* _{room['created_at']}_  \n\n"
            f"*👥 Участники:*  \n{members_text}",
            reply_markup=markup,
            parse_mode="Markdown"
        )

    @bot.callback_query_handler(func=lambda call: call.data.startswith("delete_room_"))
    async def delete_room_callback(call: CallbackQuery):
        user_id = call.from_user.id

        if not helpers.is_admin(user_id):
            await bot.answer_callback_query(call.id, "🙈 У вас нет доступа к этой функции.")
            return

        room_id = int(call.data.split("_")[2])
        room = await db.get_room_by_id(room_id)

        if not room:
            await bot.answer_callback_query(call.id, "🙊 Комната не найдена.")
            return

        await db.delete_room(room_id)

        await bot.answer_callback_query(call.id, f"✅ Комната *{room['name']}* (ID: `{room_id}`) удалена.", parse_mode="Markdown")
        markup = helpers.get_admin_panel_markup()
        await bot.send_message(
            user_id,
            "*🐵 Панель администратора:*",
            reply_markup=markup,
            parse_mode="Markdown"
        )
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith("export_history_"))
    async def export_history_callback(call: CallbackQuery):
        user_id = call.from_user.id
        if not helpers.is_admin(user_id):
            await bot.answer_callback_query(call.id, "🙈 У вас нет доступа.")
            return

        room_id = int(call.data.split("_")[2])
        buf = await db.export_room_history(room_id)
        await bot.answer_callback_query(call.id, "📤 Экспорт истории...")
        await bot.send_document(user_id, InputFile(buf))
    
    @bot.callback_query_handler(func=lambda call: call.data.startswith("admin_enter_room_"))
    async def admin_enter_room_callback(call: CallbackQuery):
        user_id = call.from_user.id
        
        if not helpers.is_admin(user_id):
            await bot.answer_callback_query(call.id, "🙈 У вас нет доступа к этой функции.")
            return
        
        room_id = int(call.data.split("_")[3])
        room = await db.get_room_by_id(room_id)
        
        if not room:
            await bot.answer_callback_query(call.id, "🙊 Комната не найдена.")
            return
        
        is_member = await db.is_user_in_room(user_id, room_id)
        
        if not is_member:
            await db.add_member_to_room(room_id, user_id, "admin")
        
        user_states.set_active_room(user_id, room_id)
        
        markup = helpers.get_room_exit_markup()
        
        await bot.answer_callback_query(call.id)
        await bot.send_message(
            user_id,
            f"*🐵 Вы вошли в комнату:* _{room['name']}_ (как администратор)  \n"
            "Все сообщения будут отправлены другим участникам комнаты.  \n"
            "Нажмите кнопку ниже, чтобы выйти.",
            reply_markup=markup,
            parse_mode="Markdown"
        )
    
    @bot.message_handler(func=lambda message: user_states.get_user_state(message.from_user.id) == AdminState.WAITING_FOR_ROOM_NAME)
    async def process_room_name(message: Message):
        user_id = message.from_user.id
        room_name = message.text.strip()
        
        if not room_name:
            await bot.send_message(user_id, "🙉 Название комнаты не может быть пустым. Попробуйте ещё раз:", parse_mode="Markdown")
            return
        
        user_states.set_temp_room_data(user_id, 'name', room_name)
        user_states.set_user_state(user_id, AdminState.WAITING_FOR_CLIENT_ID)
        
        await bot.send_message(user_id, "🐵 *Введите ID клиента:*", parse_mode="Markdown")
    
    @bot.message_handler(func=lambda message: user_states.get_user_state(message.from_user.id) == AdminState.WAITING_FOR_CLIENT_ID)
    async def process_client_id(message: Message):
        user_id = message.from_user.id
        
        try:
            client_id = int(message.text.strip())
        except ValueError:
            await bot.send_message(user_id, "🙈 ID должен быть числом. Попробуйте ещё раз:", parse_mode="Markdown")
            return
        
        user_states.set_temp_room_data(user_id, 'client_id', client_id)
        user_states.set_user_state(user_id, AdminState.WAITING_FOR_CODER_ID)
        
        await bot.send_message(user_id, "🐵 *Введите ID программиста:*", parse_mode="Markdown")
    
    @bot.message_handler(func=lambda message: user_states.get_user_state(message.from_user.id) == AdminState.WAITING_FOR_CODER_ID)
    async def process_coder_id(message: Message):
        user_id = message.from_user.id
        
        try:
            coder_id = int(message.text.strip())
        except ValueError:
            await bot.send_message(user_id, "🙈 ID должен быть числом. Попробуйте ещё раз:", parse_mode="Markdown")
            return
        
        temp_data = user_states.get_temp_room_data(user_id)
        temp_data['coder_id'] = coder_id
        
        room_name = temp_data['name']
        client_id = temp_data['client_id']
        
        conn = db.get_db_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (client_id,))
        client_exists = cursor.fetchone() is not None
        cursor.execute("SELECT 1 FROM users WHERE user_id = ?", (coder_id,))
        coder_exists = cursor.fetchone() is not None
        conn.close()
        
        if not client_exists:
            await db.add_user(client_id, f"client_{client_id}", "client")
        if not coder_exists:
            await db.add_user(coder_id, f"coder_{coder_id}", "coder")
        
        room_id = await db.create_room(room_name)
        await db.add_member_to_room(room_id, client_id, "client")
        await db.add_member_to_room(room_id, coder_id, "coder")
        
        user_states.clear_temp_room_data(user_id)
        user_states.set_user_state(user_id, AdminState.IDLE)
        
        await bot.send_message(
            user_id,
            f"✅ *Комната '{room_name}' успешно создана!* 🐵\n"
            f"• *ID комнаты:* `{room_id}`\n"
            f"• *Клиент:* `{client_id}`\n"
            f"• *Программист:* `{coder_id}`",
            parse_mode="Markdown"
        )
        
        try:
            await bot.send_message(
                client_id,
                f"🐵 Вы были добавлены в комнату '*{room_name}*'. Используйте /start для входа.",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Не удалось отправить уведомление клиенту: {e}")
        
        try:
            await bot.send_message(
                coder_id,
                f"🐵 Вы были добавлены в комнату '*{room_name}*'. Используйте /start для входа.",
                parse_mode="Markdown"
            )
        except Exception as e:
            logger.error(f"Не удалось отправить уведомление программисту: {e}")
