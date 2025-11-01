#!/usr/bin/env python3
"""
Telegram Insider Trading Bot

A bot that monitors insider trading activities and sends notifications to users.
"""

import logging
import os
import sqlite3
import schedule
import time
from datetime import datetime
from dotenv import load_dotenv
from telegram import Update
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters, CallbackContext

# Load environment variables
load_dotenv()

# Configuration
TELEGRAM_TOKEN = os.getenv('TELEGRAM_TOKEN')
DEGIRO_USERNAME = os.getenv('DEGIRO_USERNAME')
DEGIRO_PASSWORD = os.getenv('DEGIRO_PASSWORD')
DATABASE_URL = os.getenv('DATABASE_URL', 'insider_trading.db')
CHECK_INTERVAL_MINUTES = int(os.getenv('CHECK_INTERVAL_MINUTES', 30))
LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')

# Set up logging
logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    level=getattr(logging, LOG_LEVEL.upper())
)
logger = logging.getLogger(__name__)

# Database setup
def init_db():
    """Initialize the database with required tables."""
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    # Create users table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY,
            telegram_id INTEGER UNIQUE,
            username TEXT,
            first_name TEXT,
            last_name TEXT,
            is_active BOOLEAN DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create insider_trades table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS insider_trades (
            id INTEGER PRIMARY KEY,
            company_name TEXT,
            insider_name TEXT,
            relationship TEXT,
            transaction_date DATE,
            transaction_type TEXT,
            price REAL,
            quantity INTEGER,
            total_value REAL,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    # Create notifications table
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS notifications (
            id INTEGER PRIMARY KEY,
            user_id INTEGER,
            trade_id INTEGER,
            sent_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (user_id) REFERENCES users (id),
            FOREIGN KEY (trade_id) REFERENCES insider_trades (id)
        )
    ''')
    
    conn.commit()
    conn.close()
    logger.info("Database initialized successfully")

# User management
def add_user(telegram_id, username, first_name, last_name):
    """Add a new user to the database."""
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT OR IGNORE INTO users (telegram_id, username, first_name, last_name)
            VALUES (?, ?, ?, ?)
        ''', (telegram_id, username, first_name, last_name))
        conn.commit()
        logger.info(f"User {username} added to database")
    except Exception as e:
        logger.error(f"Error adding user: {e}")
    finally:
        conn.close()

def get_active_users():
    """Retrieve all active users from the database."""
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    try:
        cursor.execute('SELECT telegram_id FROM users WHERE is_active = 1')
        users = cursor.fetchall()
        return [user[0] for user in users]
    except Exception as e:
        logger.error(f"Error retrieving users: {e}")
        return []
    finally:
        conn.close()

# Mock function to simulate fetching insider trading data
def fetch_insider_trades():
    """
    Fetch recent insider trading data.
    In a real implementation, this would connect to a data source or API.
    """
    # Simulate fetching data with a delay
    time.sleep(1)
    
    # Mock data - in reality, this would come from an external source
    mock_trades = [
        {
            'company_name': 'TechCorp Inc.',
            'insider_name': 'John Doe',
            'relationship': 'CEO',
            'transaction_date': '2025-11-01',
            'transaction_type': 'Buy',
            'price': 150.25,
            'quantity': 1000,
            'total_value': 150250.00
        },
        {
            'company_name': 'Global Solutions Ltd.',
            'insider_name': 'Jane Smith',
            'relationship': 'CFO',
            'transaction_date': '2025-10-31',
            'transaction_type': 'Sell',
            'price': 42.75,
            'quantity': 5000,
            'total_value': 213750.00
        }
    ]
    
    return mock_trades

# Database operations for trades
def save_trade(trade_data):
    """Save an insider trade to the database."""
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO insider_trades 
            (company_name, insider_name, relationship, transaction_date, transaction_type, price, quantity, total_value)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        ''', (
            trade_data['company_name'],
            trade_data['insider_name'],
            trade_data['relationship'],
            trade_data['transaction_date'],
            trade_data['transaction_type'],
            trade_data['price'],
            trade_data['quantity'],
            trade_data['total_value']
        ))
        conn.commit()
        trade_id = cursor.lastrowid
        logger.info(f"Trade for {trade_data['company_name']} saved to database")
        return trade_id
    except Exception as e:
        logger.error(f"Error saving trade: {e}")
        return None
    finally:
        conn.close()

def trade_exists(company_name, insider_name, transaction_date):
    """Check if a trade already exists in the database."""
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            SELECT id FROM insider_trades 
            WHERE company_name = ? AND insider_name = ? AND transaction_date = ?
        ''', (company_name, insider_name, transaction_date))
        result = cursor.fetchone()
        return result is not None
    except Exception as e:
        logger.error(f"Error checking trade existence: {e}")
        return False
    finally:
        conn.close()

# Notification system
def send_notification(bot, user_id, trade_data):
    """Send a notification to a user about an insider trade."""
    message = f"""
<b>🚨 INSIDER TRADING ALERT 🚨</b>

Company: {trade_data['company_name']}
Insider: {trade_data['insider_name']} ({trade_data['relationship']})
Transaction: {trade_data['transaction_type']}
Date: {trade_data['transaction_date']}
Price: ${trade_data['price']:.2f}
Quantity: {trade_data['quantity']:,}
Total Value: ${trade_data['total_value']:,.2f}

#InsiderTrading #{trade_data['company_name'].replace(' ', '')}
    """
    
    try:
        bot.send_message(
            chat_id=user_id,
            text=message,
            parse_mode='HTML'
        )
        logger.info(f"Notification sent to user {user_id}")
        return True
    except Exception as e:
        logger.error(f"Error sending notification to user {user_id}: {e}")
        return False

def save_notification(user_id, trade_id):
    """Save notification record to the database."""
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    try:
        cursor.execute('''
            INSERT INTO notifications (user_id, trade_id)
            VALUES (?, ?)
        ''', (user_id, trade_id))
        conn.commit()
        logger.info(f"Notification record saved for user {user_id}")
    except Exception as e:
        logger.error(f"Error saving notification: {e}")
    finally:
        conn.close()

# Main monitoring function
def check_for_new_trades(bot):
    """Check for new insider trades and send notifications."""
    logger.info("Checking for new insider trades...")
    
    # Fetch recent trades
    trades = fetch_insider_trades()
    
    # Get active users
    users = get_active_users()
    
    if not users:
        logger.info("No active users found")
        return
    
    new_trades_count = 0
    
    for trade in trades:
        # Check if trade already exists in database
        if not trade_exists(trade['company_name'], trade['insider_name'], trade['transaction_date']):
            # Save new trade to database
            trade_id = save_trade(trade)
            if trade_id:
                new_trades_count += 1
                
                # Send notifications to all active users
                for user_id in users:
                    if send_notification(bot, user_id, trade):
                        # Save notification record
                        save_notification(user_id, trade_id)
    
    logger.info(f"Check completed. Found {new_trades_count} new trades.")

# Telegram bot handlers
def start(update: Update, context: CallbackContext):
    """Handler for /start command."""
    user = update.effective_user
    chat_id = update.effective_chat.id
    
    # Add user to database
    add_user(user.id, user.username, user.first_name, user.last_name)
    
    # Send welcome message
    welcome_message = """
🎉 <b>Welcome to the Insider Trading Bot!</b> 🎉

I will monitor insider trading activities and send you notifications when significant transactions occur.

<b>Commands:</b>
/start - Start the bot
/help - Show this help message
/status - Check bot status
/settings - Configure notification settings

You're now subscribed to receive insider trading alerts!
    """
    
    context.bot.send_message(
        chat_id=chat_id,
        text=welcome_message,
        parse_mode='HTML'
    )
    
    logger.info(f"User {user.username} started the bot")

def help_command(update: Update, context: CallbackContext):
    """Handler for /help command."""
    help_message = """
<b>🤖 Insider Trading Bot Help</b>

I monitor insider trading activities and send you notifications when significant transactions occur.

<b>Available Commands:</b>
/start - Start the bot and subscribe to alerts
/help - Show this help message
/status - Check the bot's current status
/settings - Configure notification settings (coming soon)

<b>How it works:</b>
1. I check for new insider trading transactions periodically
2. I notify you when significant transactions occur
3. You can stay informed about insider activities that may impact stock prices

For any issues, contact the bot administrator.
    """
    
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=help_message,
        parse_mode='HTML'
    )

def status(update: Update, context: CallbackContext):
    """Handler for /status command."""
    # Get database statistics
    conn = sqlite3.connect(DATABASE_URL)
    cursor = conn.cursor()
    
    try:
        # Get user count
        cursor.execute('SELECT COUNT(*) FROM users WHERE is_active = 1')
        user_count = cursor.fetchone()[0]
        
        # Get trade count
        cursor.execute('SELECT COUNT(*) FROM insider_trades')
        trade_count = cursor.fetchone()[0]
        
        # Get recent trades
        cursor.execute('''
            SELECT company_name, insider_name, transaction_type, total_value 
            FROM insider_trades 
            ORDER BY created_at DESC 
            LIMIT 5
        ''')
        recent_trades = cursor.fetchall()
    except Exception as e:
        logger.error(f"Error retrieving status: {e}")
        user_count = 0
        trade_count = 0
        recent_trades = []
    finally:
        conn.close()
    
    # Format recent trades
    trades_text = ""
    if recent_trades:
        trades_text = "\n<b>Recent Trades:</b>\n"
        for trade in recent_trades:
            trades_text += f"• {trade[0]} - {trade[1]} {trade[2]} ${trade[3]:,.2f}\n"
    else:
        trades_text = "\n<i>No recent trades found</i>"
    
    status_message = f"""
<b>📊 Bot Status</b>

Active Users: {user_count}
Trades Tracked: {trade_count}
Check Interval: {CHECK_INTERVAL_MINUTES} minutes
Last Updated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

{trades_text}
    """
    
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=status_message,
        parse_mode='HTML'
    )

def settings(update: Update, context: CallbackContext):
    """Handler for /settings command."""
    settings_message = """
<b>⚙️ Notification Settings</b>

Notification preferences are currently managed globally. 
Future updates will allow individual configuration.
    """
    
    context.bot.send_message(
        chat_id=update.effective_chat.id,
        text=settings_message,
        parse_mode='HTML'
    )

# Main function
def main():
    """Main function to run the bot."""
    # Initialize database
    init_db()
    
    # Check if TELEGRAM_TOKEN is set
    if not TELEGRAM_TOKEN:
        logger.error("TELEGRAM_TOKEN is not set. Please check your .env file.")
        return
    
    # Create the Updater and pass it your bot's token
    updater = Updater(TELEGRAM_TOKEN)
    
    # Get the dispatcher to register handlers
    dispatcher = updater.dispatcher
    
    # Register command handlers
    dispatcher.add_handler(CommandHandler("start", start))
    dispatcher.add_handler(CommandHandler("help", help_command))
    dispatcher.add_handler(CommandHandler("status", status))
    dispatcher.add_handler(CommandHandler("settings", settings))
    
    # Start the Bot
    updater.start_polling()
    
    logger.info("Telegram bot started successfully")
    
    # Schedule the monitoring function
    schedule.every(CHECK_INTERVAL_MINUTES).minutes.do(check_for_new_trades, updater.bot)
    
    # Run the monitoring function once at startup
    check_for_new_trades(updater.bot)
    
    # Keep the bot running
    try:
        while True:
            schedule.run_pending()
            time.sleep(1)
    except KeyboardInterrupt:
        logger.info("Bot stopped by user")
        updater.stop()

if __name__ == '__main__':
    main()