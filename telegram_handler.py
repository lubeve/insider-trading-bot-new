"""
Telegram Handler module for the Insider Trading Bot.

This module handles all Telegram bot interactions, including command processing,
message handling, and user communication.
"""

import logging
from typing import Optional
from telegram import Update, Bot
from telegram.ext import ContextTypes
from telegram.constants import ParseMode

from database import DatabaseManager, User
from degiro_client import DegiroClient
from notifications import NotificationSystem

logger = logging.getLogger(__name__)


class TelegramHandler:
    """
    Handles all Telegram bot interactions and commands.
    """
    
    def __init__(self, bot_instance):
        """
        Initialize the Telegram handler.
        
        Args:
            bot_instance: Main bot instance for accessing other components
        """
        self.bot = bot_instance
        self.database = bot_instance.database
        self.degiro_client = bot_instance.degiro_client
        self.notification_system = bot_instance.notification_system
        self.logger = logging.getLogger(__name__)
        
    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle the /start command.
        
        Args:
            update: Telegram update object
            context: Telegram context object
        """
        try:
            user = update.effective_user
            chat_id = update.effective_chat.id
            
            # Add or update user in database
            db_user = await self.database.get_user(user.id)
            if not db_user:
                db_user = await self.database.create_user(
                    telegram_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name
                )
                is_new_user = True
            else:
                # Update user information
                await self.database.update_user(
                    telegram_id=user.id,
                    username=user.username,
                    first_name=user.first_name,
                    last_name=user.last_name,
                    is_active=True
                )
                is_new_user = False
                
            # Send welcome message
            welcome_message = f"""
🎉 <b>Welcome{' back' if not is_new_user else ''} to the Insider Trading Bot!</b> 🎉

I monitor insider trading activities and send you notifications when significant transactions occur.

<b>Commands:</b>
/start - Start the bot and subscribe to alerts
/help - Show help information
/status - Check bot status and recent trades
/portfolio - View your Degiro portfolio (if connected)
/settings - Configure notification settings
/disconnect - Disconnect your Degiro account

You're now{' re' if not is_new_user else ' '}subscribed to receive insider trading alerts!
            """
            
            await context.bot.send_message(
                chat_id=chat_id,
                text=welcome_message.strip(),
                parse_mode=ParseMode.HTML
            )
            
            self.logger.info(f"User {user.username or user.id} started the bot")
            
        except Exception as e:
            self.logger.error(f"Error in start command: {e}")
            await self._send_error_message(update, context, "Failed to process start command")
            
    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle the /help command.
        
        Args:
            update: Telegram update object
            context: Telegram context object
        """
        try:
            help_message = """
<b>🤖 Insider Trading Bot Help</b>

I monitor insider trading activities and send you notifications when significant transactions occur.

<b>Available Commands:</b>
/start - Start the bot and subscribe to alerts
/help - Show this help message
/status - Check the bot's current status and recent trades
/portfolio - View your Degiro portfolio (requires connection)
/settings - Configure notification settings
/disconnect - Disconnect your Degiro account

<b>How it works:</b>
1. I check for new insider trading transactions periodically
2. I notify you when significant transactions occur
3. You can connect your Degiro account to view portfolio and funds
4. Future updates will support automated trading based on signals

For any issues, contact the bot administrator.
            """
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=help_message.strip(),
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            self.logger.error(f"Error in help command: {e}")
            await self._send_error_message(update, context, "Failed to process help command")
            
    async def status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle the /status command.
        
        Args:
            update: Telegram update object
            context: Telegram context object
        """
        try:
            # Get database statistics
            users = await self.database.get_all_users(active_only=True)
            user_count = len(users)
            
            # Get system state
            system_state = await self.database.get_system_state()
            last_analysis = system_state.last_analysis_run if system_state else None
            
            # Format status message
            status_message = f"""
<b>📊 Bot Status</b>

Active Users: {user_count}
Check Interval: {self.bot.config.CHECK_INTERVAL_MINUTES} minutes
Last Analysis Run: {last_analysis.strftime('%Y-%m-%d %H:%M:%S') if last_analysis else 'Never'}

<b>Connection Status:</b>
Degiro Integration: {'Enabled' if self.bot.config.is_degiro_enabled() else 'Disabled'}
            """
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=status_message.strip(),
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            self.logger.error(f"Error in status command: {e}")
            await self._send_error_message(update, context, "Failed to retrieve status information")
            
    async def settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle the /settings command.
        
        Args:
            update: Telegram update object
            context: Telegram context object
        """
        try:
            settings_message = """
<b>⚙️ Notification Settings</b>

Notification preferences are currently managed globally. 
Future updates will allow individual configuration.

<b>Current Settings:</b>
- Check Interval: Every {check_interval} minutes
- Log Level: {log_level}
            """.format(
                check_interval=self.bot.config.CHECK_INTERVAL_MINUTES,
                log_level=self.bot.config.LOG_LEVEL
            )
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=settings_message.strip(),
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            self.logger.error(f"Error in settings command: {e}")
            await self._send_error_message(update, context, "Failed to retrieve settings")
            
    async def portfolio(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle the /portfolio command.
        
        Args:
            update: Telegram update object
            context: Telegram context object
        """
        try:
            user = update.effective_user
            
            # Check if Degiro integration is enabled
            if not self.bot.config.is_degiro_enabled():
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ Degiro integration is not enabled. Please configure your credentials.",
                    parse_mode=ParseMode.HTML
                )
                return
                
            # Get user from database
            db_user = await self.database.get_user(user.id)
            if not db_user:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ User not found. Please start the bot with /start",
                    parse_mode=ParseMode.HTML
                )
                return
                
            # Try to get portfolio
            portfolio = await self.degiro_client.get_portfolio()
            
            if portfolio is None:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ Unable to retrieve portfolio. Please check your Degiro connection.",
                    parse_mode=ParseMode.HTML
                )
                return
                
            # Format portfolio message
            if not portfolio:
                portfolio_message = "📊 <b>Your Portfolio</b>\n\nNo positions found in your portfolio."
            else:
                portfolio_message = "📊 <b>Your Portfolio</b>\n\n"
                total_value = 0.0
                
                for position in portfolio:
                    portfolio_message += (
                        f"<b>{position['name']} ({position['symbol']})</b>\n"
                        f"Quantity: {position['quantity']}\n"
                        f"Price: €{position['price']:.2f}\n"
                        f"Value: €{position['total_value']:.2f}\n\n"
                    )
                    total_value += position['total_value']
                    
                portfolio_message += f"<b>Total Portfolio Value: €{total_value:.2f}</b>"
                
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=portfolio_message.strip(),
                parse_mode=ParseMode.HTML
            )
            
        except Exception as e:
            self.logger.error(f"Error in portfolio command: {e}")
            await self._send_error_message(update, context, "Failed to retrieve portfolio")
            
    async def disconnect(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle the /disconnect command.
        
        Args:
            update: Telegram update object
            context: Telegram context object
        """
        try:
            user = update.effective_user
            
            # Get user from database
            db_user = await self.database.get_user(user.id)
            if not db_user:
                await context.bot.send_message(
                    chat_id=update.effective_chat.id,
                    text="❌ User not found. Please start the bot with /start",
                    parse_mode=ParseMode.HTML
                )
                return
                
            # Clear user session
            success = await self.bot.state_manager.clear_user_session(db_user.id)
            
            if success:
                # Logout from Degiro
                self.degiro_client.logout()
                
                message = "✅ Successfully disconnected your Degiro account."
            else:
                message = "⚠️ No active Degiro session found to disconnect."
                
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=message,
                parse_mode=ParseMode.HTML
            )
            
            self.logger.info(f"User {user.username or user.id} disconnected Degiro account")
            
        except Exception as e:
            self.logger.error(f"Error in disconnect command: {e}")
            await self._send_error_message(update, context, "Failed to disconnect account")
            
    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """
        Handle incoming text messages.
        
        Args:
            update: Telegram update object
            context: Telegram context object
        """
        try:
            user = update.effective_user
            message_text = update.message.text
            
            self.logger.info(f"Received message from {user.username or user.id}: {message_text}")
            
            # For now, just echo the message with a bot response
            # In a real implementation, you might add natural language processing
            response = f".echo: {message_text}"
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=response
            )
            
        except Exception as e:
            self.logger.error(f"Error handling message: {e}")
            # Don't send error message for regular messages to avoid spam
            
    async def _send_error_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE, 
                                 message: str):
        """
        Send an error message to the user.
        
        Args:
            update: Telegram update object
            context: Telegram context object
            message: Error message to send
        """
        try:
            error_message = f"❌ <b>Error</b>: {message}\n\nPlease try again or contact support."
            
            await context.bot.send_message(
                chat_id=update.effective_chat.id,
                text=error_message,
                parse_mode=ParseMode.HTML
            )
        except Exception as e:
            self.logger.error(f"Failed to send error message: {e}")