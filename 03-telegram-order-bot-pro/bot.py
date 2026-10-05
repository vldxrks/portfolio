"""Entry point. Wires up storage, middlewares and routers, then starts polling.
Run: python bot.py (after filling .env — see README.md)
"""
import asyncio
import logging
from logging.handlers import RotatingFileHandler

from aiogram import Bot, Dispatcher

import database as db
from config import config
from handlers import admin, common, order
from middlewares import ThrottlingMiddleware


def setup_logging() -> None:
    handler = RotatingFileHandler("bot.log", maxBytes=1_000_000, backupCount=2, encoding="utf-8")
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s",
        handlers=[handler, logging.StreamHandler()],
    )


async def main() -> None:
    setup_logging()
    db.init_db()

    bot = Bot(config.BOT_TOKEN)
    dp = Dispatcher()

    dp.message.middleware(ThrottlingMiddleware())
    dp.callback_query.middleware(ThrottlingMiddleware())

    dp.include_router(admin.router)   # admin router first: its filters narrow to ADMIN_IDS only
    dp.include_router(order.router)
    dp.include_router(common.router)

    logging.getLogger(__name__).info("Bot starting...")
    await bot.delete_webhook(drop_pending_updates=True)
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
