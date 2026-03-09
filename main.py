import logging
import asyncio

from aiogram import Bot, Dispatcher
from config.config import Config, load_config
from handlers import start_help, schedule, other
from keyboards.set_menu import set_main_menu

from services.scheduler import start_scheduler


async def main() -> None:
    config: Config = load_config()

    logging.basicConfig(
        level=logging.getLevelName(level=config.log.level),
        format=config.log.format,
        style="{",
    )

    bot = Bot(token=config.bot.token)
    dp = Dispatcher()

    await start_scheduler()

    dp.include_router(start_help.router)
    dp.include_router(schedule.router)
    dp.include_router(other.router)

    await set_main_menu(bot)

    await dp.start_polling(bot)


asyncio.run(main())
