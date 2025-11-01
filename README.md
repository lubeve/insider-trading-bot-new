# Telegram Insider Trading Bot

A Telegram bot that monitors insider trading activities and sends notifications to users about significant transactions.

## Features

- Monitors insider trading activities
- Sends real-time notifications via Telegram
- Configurable notification settings
- Integration with Degiro API for trading capabilities (optional)

## Prerequisites

- Python 3.8+
- A Telegram account
- A Telegram Bot Token (obtained via @BotFather)
- (Optional) Degiro account credentials for trading integration

## Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/lubeve/insider-trading-bot-new.git
   cd insider-trading-bot-new
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

4. Create a `.env` file with your configuration:
   ```env
   TELEGRAM_TOKEN=your_telegram_bot_token
   DEGIRO_USERNAME=your_degiro_username
   DEGIRO_PASSWORD=your_degiro_password
   DATABASE_URL=sqlite:///insider_trading.db
   CHECK_INTERVAL_MINUTES=30
   LOG_LEVEL=INFO
   ```

## Usage

1. Start the bot:
   ```bash
   python bot.py
   ```

2. Open Telegram and search for your bot by username.

3. Send `/start` to begin receiving notifications.

## Commands

- `/start` - Start the bot and receive a welcome message
- `/help` - Show available commands
- `/status` - Check the bot's current status
- `/settings` - Configure notification settings

## Configuration

The bot can be configured using environment variables in the `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `TELEGRAM_TOKEN` | Your Telegram Bot Token | - |
| `DEGIRO_USERNAME` | Your Degiro username | - |
| `DEGIRO_PASSWORD` | Your Degiro password | - |
| `DATABASE_URL` | Database connection string | `sqlite:///insider_trading.db` |
| `CHECK_INTERVAL_MINUTES` | Interval between checks (minutes) | `30` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.