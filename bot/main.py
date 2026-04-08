"""
Nova VPN Bot - Main Entry Point
Hiddify Integration - VLESS Reality only
"""

import asyncio
import logging
import os
import sys
from pathlib import Path

from aiogram import Bot, Dispatcher, F
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.fsm.storage.memory import MemoryStorage

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

import bot.config as config
from bot.services.hiddify_manager import HiddifyManager
from bot.services.user_service import UserService
from bot.services.notification_service import NotificationService
from bot.database import Database
from bot.services.xray_config_manager import XrayConfigManager
from bot.handlers import user_handlers, admin_handlers
from bot.services.subscription_server import SubscriptionServer

# Setup logging
logging.basicConfig(
    level=getattr(logging, config.LOG_LEVEL),
    format='%(asctime)s [%(levelname)s] %(name)s: %(message)s',
    datefmt='%Y-%m-%d %H:%M:%S'
)
logger = logging.getLogger(__name__)


async def main():
    logger.info("=" * 60)
    logger.info("Nova VPN Bot - Hiddify Integration")
    logger.info("=" * 60)

    # Initialize database
    logger.info(f"Initializing database: {config.DB_PATH}")
    db = Database(config.DB_PATH)

    # Initialize Hiddify manager
    hiddify = HiddifyManager(config)
    logger.info("Hiddify manager initialized")

    # Initialize Xray config manager (standalone Reality on port 8443 + gRPC bypass on 2053)
    # Also manages Hiddify Reality inbound (dl.google.com on port 443 via HAProxy)
    xray_manager = XrayConfigManager(
        config_path=config.XRAY_CONFIG_PATH,
        service_name=config.XRAY_SERVICE_NAME,
        secondary_config_path=config.HIDDIFY_XRAY_CONFIG_PATH,
        secondary_service_name=config.HIDDIFY_XRAY_SERVICE_NAME
    )
    logger.info(f"Xray config manager initialized, {len(xray_manager.get_client_uuids())} clients")

    # Initialize bot
    bot = Bot(
        token=config.BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.MARKDOWN)
    )

    # Initialize services
    notification_service = NotificationService(bot, config.ADMIN_IDS)
    user_service = UserService(db, hiddify, config, notification_service, xray_manager=xray_manager)

    # Setup dispatcher
    dp = Dispatcher(storage=MemoryStorage())

    # Register handlers
    dp.include_router(user_handlers.router)
    dp.include_router(admin_handlers.router)

    # Dependency injection via workflow_data (aiogram 3.x)
    dp.workflow_data["db"] = db
    dp.workflow_data["user_service"] = user_service
    dp.workflow_data["hiddify"] = hiddify
    dp.workflow_data["notification_service"] = notification_service

    # Start subscription HTTP server
    sub_server = SubscriptionServer(hiddify, xray_manager, config, port=8888)
    await sub_server.start()

    logger.info("Bot is starting...")
    logger.info(f"Admin IDs: {config.ADMIN_IDS}")
    logger.info(f"Max configs per user: {config.MAX_CONFIGS_PER_USER}")
    logger.info(f"Subscription URL: http://0.0.0.0:8888/sub/<uuid>")

    try:
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        await bot.session.close()
        logger.info("Bot stopped")


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        logging.getLogger(__name__).info("Bot stopped by user")
