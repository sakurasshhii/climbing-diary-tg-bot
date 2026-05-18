import aiosqlite
import logging

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.fsm.storage.memory import MemoryStorage

from app.bot.handlers import routers
from app.bot.middlewares import ServicesMiddleware
from app.config.config import Config
from app.infrastructure.database import Database, create_tables
from app.bot.keyboards.set_menu import set_main_menu

logger = logging.getLogger(__name__)


async def main(config: Config) -> None:
    '''
    Запуск бота
    '''
    logger.info('Starting bot...')

    session = AiohttpSession(
        proxy=config.proxy.proxy_url
    )
    bot = Bot(
        token=config.tg_bot.bot_token,
        session=session,
        default=DefaultBotProperties()
    )
    storage = MemoryStorage()
    dp = Dispatcher(storage=storage)

    await set_main_menu(bot)

    logger.info('Database connection...')
    db = await aiosqlite.connect(config.db.path)
    db.row_factory = aiosqlite.Row
    my_db = Database(db)
    await create_tables(db=my_db)

    logger.info('Include routers...')
    dp.include_routers(*routers)

    logger.info('Including middlewares...')
    dp.update.middleware(ServicesMiddleware(my_db))

    logger.info('Start polling...')
    await bot.delete_webhook(drop_pending_updates=True)
    
    try:
        await dp.start_polling(bot)
    except Exception as e:
        logger.exception(e)
    finally:
        await bot.session.close()
        await db.close()
