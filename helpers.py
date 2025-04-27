import config
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton

def is_admin(user_id: int) -> bool:
    return user_id in config.ADMIN_IDS

def get_main_menu_markup(user_id: int) -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(InlineKeyboardButton("Мои комнаты", callback_data="view_rooms"))
    
    if is_admin(user_id):
        markup.add(InlineKeyboardButton("Панель администратора", callback_data="admin_panel"))
    
    return markup

def get_admin_panel_markup() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup(row_width=1)
    markup.add(
        InlineKeyboardButton("Создать комнату", callback_data="create_room"),
        InlineKeyboardButton("Список комнат", callback_data="list_rooms"),
        InlineKeyboardButton("Главное меню", callback_data="main_menu")
    )
    return markup

def get_room_exit_markup() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Выйти из комнаты", callback_data="exit_room"))
    return markup

def get_back_to_main_menu_markup() -> InlineKeyboardMarkup:
    markup = InlineKeyboardMarkup()
    markup.add(InlineKeyboardButton("Главное меню", callback_data="main_menu"))
    return markup

def get_sender_title(is_admin: bool, role: str) -> str:
    if is_admin:
        return "Администратор"
    elif role == "client":
        return "Клиент"
    elif role == "coder":
        return "Программист"
    else:
        return "Пользователь"
