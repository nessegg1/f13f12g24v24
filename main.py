import asyncio
import platform
import logging
from telebot.async_telebot import AsyncTeleBot

import config
from database import db
from handlers import common, admin, messaging
from logger import setup_logger

logger = setup_logger()

bot = AsyncTeleBot(config.BOT_TOKEN)

if platform.system() == 'Windows':
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())

def register_all_handlers():
    common.register_common_handlers(bot)
    admin.register_admin_handlers(bot)
    messaging.register_messaging_handlers(bot)
    
    logger.info("All handlers registered")

async def main():
    try:
        db.init_db()
        logger.info("Database initialized")
        
        register_all_handlers()
        
        logger.info("Bot started")
        await bot.polling(non_stop=True, timeout=60)
    except Exception as e:
        logger.error(f"Error starting bot: {e}", exc_info=True)

if __name__ == "__main__":
    asyncio.run(main())