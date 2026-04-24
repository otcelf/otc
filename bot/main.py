import asyncio
import logging
import time

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.client.session.aiohttp import AiohttpSession
from aiogram.exceptions import TelegramNetworkError
import aiohttp

from bot.config import Settings, load_settings
from bot.handlers.admin import router as admin_router
from bot.handlers.deal_create import router as deal_router
from bot.handlers.requisites import router as requisites_router
from bot.handlers.start import router as start_router
from bot.services.storage import Storage

logger = logging.getLogger(__name__)


async def main() -> None:
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    settings: Settings = load_settings()
    storage = Storage(settings.db_path)
    await storage.init()

    # Создаём сессию с поддержкой прокси если указан
    if settings.proxy_url:
        logger.info(f"Using proxy: {settings.proxy_url}")
        session = AiohttpSession(proxy=settings.proxy_url)
    else:
        session = AiohttpSession()
    
    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode="HTML"),
        session=session
    )
    dp = Dispatcher()

    dp["settings"] = settings
    dp["storage"] = storage

    dp.include_router(start_router)
    dp.include_router(admin_router)
    dp.include_router(requisites_router)
    dp.include_router(deal_router)

    # await bot.delete_webhook(drop_pending_updates=False)
    logger.info("Starting bot polling...")
    retry_count = 0
    max_retries = 5
    
    while True:
        try:
            await dp.start_polling(bot)
        except TelegramNetworkError as e:
            retry_count += 1
            wait_time = min(30, 2 ** retry_count)
            logger.error(f"Network error (attempt {retry_count}/{max_retries}): {e}")
            logger.info(f"Retrying in {wait_time} seconds...")
            await asyncio.sleep(wait_time)
            if retry_count >= max_retries:
                logger.critical("Max retries exceeded. Exiting.")
                raise
        except Exception as e:
            logger.exception(f"Unexpected error: {e}")
            await asyncio.sleep(5)


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.exception("Unhandled exception during bot execution")
