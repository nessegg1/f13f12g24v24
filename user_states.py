from typing import Dict, Any

class AdminState:
    IDLE = 'idle'
    WAITING_FOR_ROOM_NAME = 'waiting_for_room_name'
    WAITING_FOR_CLIENT_ID = 'waiting_for_client_id'
    WAITING_FOR_CODER_ID = 'waiting_for_coder_id'

user_states = {}
temp_room_data = {}
active_rooms = {}

def get_user_state(user_id: int) -> str:
    return user_states.get(user_id, AdminState.IDLE)

def set_user_state(user_id: int, state: str) -> None:
    user_states[user_id] = state

def get_temp_room_data(user_id: int) -> Dict[str, Any]:
    if user_id not in temp_room_data:
        temp_room_data[user_id] = {}
    return temp_room_data[user_id]

def set_temp_room_data(user_id: int, key: str, value: Any) -> None:
    if user_id not in temp_room_data:
        temp_room_data[user_id] = {}
    temp_room_data[user_id][key] = value

def clear_temp_room_data(user_id: int) -> None:
    if user_id in temp_room_data:
        del temp_room_data[user_id]

def set_active_room(user_id: int, room_id: int) -> None:
    active_rooms[user_id] = room_id

def get_active_room(user_id: int) -> int:
    return active_rooms.get(user_id)

def clear_active_room(user_id: int) -> None:
    if user_id in active_rooms:
        del active_rooms[user_id]

def is_user_in_active_room(user_id: int) -> bool:
    return user_id in active_rooms
