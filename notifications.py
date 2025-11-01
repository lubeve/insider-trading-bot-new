"""
Notifications module for the Insider Trading Bot.

This module handles sending notifications to users via Telegram,
including trade alerts, system status updates, and error notifications.
"""

import logging
import asyncio
from typing import List, Optional, Dict, Any
from datetime import datetime
from telegram import Bot
from telegram.constants import ParseMode

from config import Config
from database import DatabaseManager

logger = logging.getLogger(__name__)


class NotificationSystem:
    """
    Manages all notification sending for the bot, including trade alerts
    and system messages.
    """
    
    def __init__(self):
        """
        Initialize the notification system.
        """
        self.config = Config()
        self.bot = None
        self.database = DatabaseManager()
        self.logger = logging.getLogger(__name__)
        
    async def initialize(self, bot_instance):
        """
        Initialize with bot instance for sending messages.
        
        Args:
            bot_instance: Telegram bot instance
        """
        self.bot = bot_instance
        self.logger.info("Notification system initialized")
        
    async def send_trade_alert(self, trade_data: Dict[str, Any], user_ids: List[int]) -> Dict[int, bool]:
        """
        Send insider trading alert to specified users.
        
        Args:
            trade_data: Dictionary containing trade information
            user_ids: List of user Telegram IDs to notify
            
        Returns:
            Dict mapping user IDs to success status
        """
        if not self.bot:
            raise RuntimeError("Notification system not initialized with bot instance")
            
        results = {}
        
        # Format the trade alert message
        message = self._format_trade_alert_message(trade_data)
        
        # Send notification to each user
        for user_id in user_ids:
            try:
                await self.bot.send_message(
                    chat_id=user_id,
                    text=message,
                    parse_mode=ParseMode.HTML
                )
                results[user_id] = True
                self.logger.info(f"Trade alert sent to user {user_id}")
                
            except Exception as e:
                self.logger.error(f"Failed to send trade alert to user {user_id}: {e}")
                results[user_id] = False
                
        return results
        
    def _format_trade_alert_message(self, trade_data: Dict[str, Any]) -> str:
        """
        Format a trade alert message from trade data.
        
        Args:
            trade_data: Dictionary containing trade information
            
        Returns:
            Formatted message string
        """
        message = f"""
🚨 <b>INSIDER TRADING ALERT</b> 🚨

Company: {trade_data.get('company_name', 'Unknown')}
Insider: {trade_data.get('insider_name', 'Unknown')} ({trade_data.get('relationship', 'Unknown')})
Transaction: {trade_data.get('transaction_type', 'Unknown')}
Date: {trade_data.get('transaction_date', 'Unknown')}
Price: ${trade_data.get('price', 0.0):.2f}
Quantity: {trade_data.get('quantity', 0):,}
Total Value: ${trade_data.get('total_value', 0.0):,.2f}

#InsiderTrading #{trade_data.get('company_name', 'Unknown').replace(' ', '')}
        """
        
        return message.strip()
        
    async def send_admin_notification(self, message: str, 
                                    parse_mode: str = ParseMode.HTML) -> bool:
        """
        Send a notification to admin users.
        
        Args:
            message: Message to send
            parse_mode: Telegram parse mode
            
        Returns:
            bool: True if message was sent successfully to at least one admin
        """
        if not self.bot:
            raise RuntimeError("Notification system not initialized with bot instance")
            
        try:
            # In a real implementation, you would get admin user IDs from the database
            # For now, we'll use a placeholder
            admin_user_ids = []  # Get from config or database
            
            if not admin_user_ids:
                self.logger.warning("No admin users configured for notifications")
                return False
                
            success_count = 0
            
            for user_id in admin_user_ids:
                try:
                    await self.bot.send_message(
                        chat_id=user_id,
                        text=f"🔔 <b>Admin Notification</b>\n\n{message}",
                        parse_mode=parse_mode
                    )
                    success_count += 1
                    self.logger.info(f"Admin notification sent to user {user_id}")
                    
                except Exception as e:
                    self.logger.error(f"Failed to send admin notification to user {user_id}: {e}")
                    
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"Error sending admin notification: {e}")
            return False
            
    async def send_system_status_update(self, status_data: Dict[str, Any]) -> bool:
        """
        Send system status update to admin users.
        
        Args:
            status_data: Dictionary containing system status information
            
        Returns:
            bool: True if message was sent successfully
        """
        if not self.bot:
            raise RuntimeError("Notification system not initialized with bot instance")
            
        try:
            message = f"""
📊 <b>System Status Update</b>

Active Users: {status_data.get('active_users', 0)}
Trades Tracked: {status_data.get('trades_tracked', 0)}
Last Analysis: {status_data.get('last_analysis', 'Never')}
System Uptime: {status_data.get('uptime', 'Unknown')}

<b>Services Status:</b>
Degiro API: {'✅ Connected' if status_data.get('degiro_connected', False) else '❌ Disconnected'}
Scheduler: {'✅ Running' if status_data.get('scheduler_running', False) else '❌ Stopped'}
        """
            
            return await self.send_admin_notification(message.strip())
            
        except Exception as e:
            self.logger.error(f"Error sending system status update: {e}")
            return False
            
    async def send_error_notification(self, error_message: str, 
                                    error_details: Optional[str] = None) -> bool:
        """
        Send error notification to admin users.
        
        Args:
            error_message: Brief error description
            error_details: Detailed error information (optional)
            
        Returns:
            bool: True if message was sent successfully
        """
        if not self.bot:
            raise RuntimeError("Notification system not initialized with bot instance")
            
        try:
            message = f"""
❗ <b>Error Notification</b>

<b>Error:</b> {error_message}

<b>Time:</b> {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

<b>Details:</b>
{error_details if error_details else 'No additional details provided'}
        """
            
            return await self.send_admin_notification(message.strip())
            
        except Exception as e:
            self.logger.error(f"Error sending error notification: {e}")
            return False
            
    async def send_portfolio_update(self, user_id: int, 
                                  portfolio_data: Dict[str, Any]) -> bool:
        """
        Send portfolio update to a user.
        
        Args:
            user_id: User's Telegram ID
            portfolio_data: Dictionary containing portfolio information
            
        Returns:
            bool: True if message was sent successfully
        """
        if not self.bot:
            raise RuntimeError("Notification system not initialized with bot instance")
            
        try:
            # Format portfolio message
            positions = portfolio_data.get('positions', [])
            total_value = portfolio_data.get('total_value', 0.0)
            
            if not positions:
                message = "📊 <b>Portfolio Update</b>\n\nYour portfolio is currently empty."
            else:
                message = "📊 <b>Portfolio Update</b>\n\n"
                for position in positions:
                    message += (
                        f"<b>{position.get('name', 'Unknown')} ({position.get('symbol', 'Unknown')})</b>\n"
                        f"Quantity: {position.get('quantity', 0)}\n"
                        f"Price: €{position.get('price', 0.0):.2f}\n"
                        f"Value: €{position.get('total_value', 0.0):.2f}\n\n"
                    )
                    
                message += f"<b>Total Portfolio Value: €{total_value:.2f}</b>"
                
            await self.bot.send_message(
                chat_id=user_id,
                text=message.strip(),
                parse_mode=ParseMode.HTML
            )
            
            self.logger.info(f"Portfolio update sent to user {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send portfolio update to user {user_id}: {e}")
            return False
            
    async def send_welcome_message(self, user_id: int, 
                                 is_new_user: bool = True) -> bool:
        """
        Send welcome message to a user.
        
        Args:
            user_id: User's Telegram ID
            is_new_user: Whether this is a new user
            
        Returns:
            bool: True if message was sent successfully
        """
        if not self.bot:
            raise RuntimeError("Notification system not initialized with bot instance")
            
        try:
            message = f"""
🎉 <b>Welcome{' back' if not is_new_user else ''} to the Insider Trading Bot!</b> 🎉

I monitor insider trading activities and send you notifications when significant transactions occur.

You're now{' re' if not is_new_user else ' '}subscribed to receive insider trading alerts!

Use /help to see available commands.
            """
            
            await self.bot.send_message(
                chat_id=user_id,
                text=message.strip(),
                parse_mode=ParseMode.HTML
            )
            
            self.logger.info(f"Welcome message sent to user {user_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to send welcome message to user {user_id}: {e}")
            return False