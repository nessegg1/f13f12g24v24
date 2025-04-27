import sqlite3
import logging
from typing import Dict, List, Optional

logger = logging.getLogger(__name__)

def init_db():
    conn = sqlite3.connect('room_bot.db')
    cursor = conn.cursor()
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS users (
        user_id INTEGER PRIMARY KEY,
        username TEXT,
        role TEXT,
        registration_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS rooms (
        room_id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS room_members (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_id INTEGER,
        user_id INTEGER,
        role TEXT,
        FOREIGN KEY (room_id) REFERENCES rooms (room_id),
        FOREIGN KEY (user_id) REFERENCES users (user_id),
        UNIQUE(room_id, user_id)
    )
    ''')
    
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        message_id INTEGER PRIMARY KEY AUTOINCREMENT,
        room_id INTEGER,
        user_id INTEGER,
        text TEXT,
        sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (room_id) REFERENCES rooms (room_id),
        FOREIGN KEY (user_id) REFERENCES users (user_id)
    )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")

def get_db_connection():
    conn = sqlite3.connect('room_bot.db')
    conn.row_factory = sqlite3.Row
    return conn

async def add_user(user_id: int, username: str, role: str = None):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT OR IGNORE INTO users (user_id, username, role) VALUES (?, ?, ?)",
        (user_id, username, role)
    )
    
    conn.commit()
    conn.close()

async def create_room(name: str) -> int:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("INSERT INTO rooms (name) VALUES (?)", (name,))
    room_id = cursor.lastrowid
    
    conn.commit()
    conn.close()
    
    return room_id

async def add_member_to_room(room_id: int, user_id: int, role: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT OR IGNORE INTO room_members (room_id, user_id, role) VALUES (?, ?, ?)",
        (room_id, user_id, role)
    )
    
    conn.commit()
    conn.close()

async def get_user_rooms(user_id: int) -> List[Dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT r.room_id, r.name 
        FROM rooms r 
        JOIN room_members rm ON r.room_id = rm.room_id 
        WHERE rm.user_id = ?
    """, (user_id,))
    
    rooms = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return rooms

async def get_room_members(room_id: int) -> List[Dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT u.user_id, u.username, rm.role 
        FROM users u 
        JOIN room_members rm ON u.user_id = rm.user_id 
        WHERE rm.room_id = ?
    """, (room_id,))
    
    members = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return members

async def save_message(room_id: int, user_id: int, text: str):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "INSERT INTO messages (room_id, user_id, text) VALUES (?, ?, ?)",
        (room_id, user_id, text)
    )
    
    conn.commit()
    conn.close()

async def get_room_by_id(room_id: int) -> Optional[Dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM rooms WHERE room_id = ?", (room_id,))
    room = cursor.fetchone()
    
    conn.close()
    return dict(room) if room else None

async def is_user_in_room(user_id: int, room_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT 1 FROM room_members WHERE user_id = ? AND room_id = ?",
        (user_id, room_id)
    )
    
    result = cursor.fetchone() is not None
    
    conn.close()
    return result

async def get_all_rooms() -> List[Dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT room_id, name FROM rooms")
    rooms = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return rooms

async def get_user_role_in_room(user_id: int, room_id: int) -> Optional[str]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute(
        "SELECT role FROM room_members WHERE user_id = ? AND room_id = ?",
        (user_id, room_id)
    )
    
    result = cursor.fetchone()
    
    conn.close()
    return result['role'] if result else None

async def get_other_room_members(room_id: int, user_id: int) -> List[Dict]:
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT u.user_id, u.role, rm.role as room_role
        FROM users u
        JOIN room_members rm ON u.user_id = rm.user_id
        WHERE rm.room_id = ? AND u.user_id != ?
    """, (room_id, user_id))
    
    members = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    return members

async def delete_room(room_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute(
        "DELETE FROM messages WHERE room_id = ?",
        (room_id,)
    )

    cursor.execute(
        "DELETE FROM room_members WHERE room_id = ?",
        (room_id,)
    )

    cursor.execute(
        "DELETE FROM rooms WHERE room_id = ?",
        (room_id,)
    )

    conn.commit()
    conn.close()