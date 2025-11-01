#!/usr/bin/env python3
"""
Telegram Insider Trading Bot

This bot monitors insider trading activities and sends notifications to users
via Telegram. It includes features for persistent user sessions, automatic
reconnection, and integration with Degiro API for trading capabilities.

Author: Lucas Benac
License: MIT
"""

import os
import sys
import logging
from typing import Dict, Any
import asyncio
from telegram import Update
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    ContextTypes,
    filters,
    CallbackContext,
)


# Import project modules
from config import Config
from state_manager import StateManager
from degiro_client import DegiroClient
from telegram_handler import TelegramHandler
from scheduler import Scheduler
from database import DatabaseManager
from notifications import NotificationSystem


# Configure logging
logging.basicConfig(
    level=getattr(logging, Config.LOG_LEVEL),
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[
        logging.FileHandler("logs/bot.log"),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)


class InsiderTradingBot:
    """
    Main bot class that orchestrates all components of the insider trading bot.
    """

    def __init__(self):
        """
        Initialize the bot with all required components.
        """
        self.config = Config()
        self.database = DatabaseManager()
        self.state_manager = StateManager(self.database)
        self.degiro_client = DegiroClient()
        self.notification_system = NotificationSystem()
        self.scheduler = Scheduler(self)
        self.telegram_handler = TelegramHandler(self)
        
        # Initialize Telegram application
        self.application = Application.builder().token(self.config.TELEGRAM_TOKEN).build()
        
        # Register command handlers
        self._register_handlers()
        
        logger.info("Insider Trading Bot initialized successfully")

    def _register_handlers(self):
        """
        Register all Telegram command and message handlers.
        """
        # Command handlers
        self.application.add_handler(CommandHandler("start", self.telegram_handler.start))
        self.application.add_handler(CommandHandler("help", self.telegram_handler.help_command))
        self.application.add_handler(CommandHandler("status", self.telegram_handler.status))
        self.application.add_handler(CommandHandler("settings", self.telegram_handler.settings))
        self.application.add_handler(CommandHandler("portfolio", self.telegram_handler.portfolio))
        self.application.add_handler(CommandHandler("disconnect", self.telegram_handler.disconnect))
        
        # Message handlers
        self.application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.telegram_handler.handle_message))
        
        logger.info("Telegram handlers registered")

    async def initialize_system(self):
        """
        Perform system initialization including database setup and state recovery.
        """
        try:
            # Initialize database
            await self.database.initialize()
            
            # Recover system state
            await self.state_manager.recover_state()
            
            # Initialize scheduler
            self.scheduler.initialize()
            
            # Send startup notification to admin users
            await self.notification_system.send_admin_notification(
                "Bot system initialized and ready"
            )
            
            logger.info("System initialization completed")
        except Exception as e:
            logger.error(f"System initialization failed: {e}")
            raise

    async def start_bot(self):
        """
        Start the Telegram bot and all background tasks.
        """
        try:
            # Initialize the system
            await self.initialize_system()
            
            # Start the scheduler
            self.scheduler.start()
            
            # Start the Telegram bot
            logger.info("Starting Telegram bot...")
            await self.application.run_polling()
            
        except Exception as e:
            logger.error(f"Bot startup failed: {e}")
            raise

    def shutdown(self):
        """
        Gracefully shutdown the bot and all components.
        """
        logger.info("Shutting down bot...")
        
        # Shutdown scheduler
        self.scheduler.shutdown()
        
        # Close database connections
        self.database.close()
        
        logger.info("Bot shutdown completed")


async def main():
    """
    Main entry point for the bot.
    """
    bot = None
    try:
        bot = InsiderTradingBot()
        await bot.start_bot()
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
    except Exception as e:
        logger.error(f"Bot encountered an error: {e}")
    finally:
        if bot:
            bot.shutdown()


if __name__ == "__main__":
    # Create required directories
    os.makedirs("data", exist_ok=True)
    os.makedirs("logs", exist_ok=True)
    
    # Run the bot
    asyncio.run(main())