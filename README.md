# Telegram Insider Trading Bot

A Telegram bot that monitors insider trading activities and sends notifications to users about significant transactions.

## Features

- Monitors insider trading activities from various sources
- Sends real-time notifications via Telegram
- Configurable notification settings
- Integration with Degiro API for trading capabilities (optional)
- Persistent user sessions with automatic reconnection
- Secure credential storage with encryption
- Docker deployment support (including Synology NAS)
- SQLite database for storing user data and analysis history

## Architecture Overview

The bot is structured with the following components:

1. **Telegram Bot Interface**: Handles user interactions via Telegram commands
2. **State Management**: Manages persistent user sessions and bot state
3. **Degiro Integration**: Interfaces with Degiro API for trading operations
4. **Scheduler**: Manages periodic analysis tasks
5. **Database Layer**: SQLite database for persistent storage
6. **Notification System**: Sends alerts to users via Telegram

## Prerequisites

- Python 3.9+
- A Telegram account
- A Telegram Bot Token (obtained via @BotFather)
- (Optional) Degiro account credentials for trading integration
- Docker (for containerized deployment)

## Installation

### Standard Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/lubeve/insider-trading-bot-new.git
   cd insider-trading-bot-new
   ```

2. Create a virtual environment:
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\\Scripts\\activate
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
   ENCRYPTION_KEY=your_secret_key_for_credential_encryption
   DATABASE_URL=sqlite:///./data/insider_trading.db
   CHECK_INTERVAL_MINUTES=30
   LOG_LEVEL=INFO
   ```

### Docker Installation

1. Clone the repository:
   ```bash
   git clone https://github.com/lubeve/insider-trading-bot-new.git
   cd insider-trading-bot-new
   ```

2. Create a `.env` file with your configuration:
   ```env
   TELEGRAM_TOKEN=your_telegram_bot_token
   DEGIRO_USERNAME=your_degiro_username
   DEGIRO_PASSWORD=your_degiro_password
   ENCRYPTION_KEY=your_secret_key_for_credential_encryption
   DATABASE_URL=sqlite:///./data/insider_trading.db
   CHECK_INTERVAL_MINUTES=30
   LOG_LEVEL=INFO
   ```

3. Build and run the Docker container:
   ```bash
   docker-compose up -d
   ```

### Synology NAS Installation

1. Install Docker from the Synology Package Center
2. Create a shared folder for the bot (e.g., `insider-trading-bot`)
3. Place the `docker-compose.yml` file in the shared folder
4. Create a `.env` file in the shared folder with your configuration
5. Open Docker app and go to "Images" > "Import" to import the docker-compose.yml file
6. Start the container

## Usage

1. Start the bot:
   ```bash
   python bot.py
   ```
   or with Docker:
   ```bash
   docker-compose up -d
   ```

2. Open Telegram and search for your bot by username.

3. Send `/start` to begin receiving notifications.

## Commands

- `/start` - Start the bot and receive a welcome message
- `/help` - Show available commands
- `/status` - Check the bot's current status
- `/settings` - Configure notification settings
- `/portfolio` - View current portfolio (if Degiro integration is enabled)
- `/disconnect` - Disconnect your Degiro account

## Configuration

The bot can be configured using environment variables in the `.env` file:

| Variable | Description | Default |
|----------|-------------|---------|
| `TELEGRAM_TOKEN` | Your Telegram Bot Token | - |
| `DEGIRO_USERNAME` | Your Degiro username | - |
| `DEGIRO_PASSWORD` | Your Degiro password | - |
| `ENCRYPTION_KEY` | Key for encrypting credentials (32 bytes) | - |
| `DATABASE_URL` | Database connection string | `sqlite:///./data/insider_trading.db` |
| `CHECK_INTERVAL_MINUTES` | Interval between checks (minutes) | `30` |
| `LOG_LEVEL` | Logging level | `INFO` |

## Deployment Architecture

### Directory Structure
```
insider-trading-bot/
├── bot.py              # Main bot application
├── config.py           # Configuration management
├── state_manager.py    # User session and bot state management
├── degiro_client.py    # Degiro API integration
├── telegram_handler.py # Telegram bot interface
├── scheduler.py        # Task scheduling
├── database.py         # Database interface
├── notifications.py    # Notification system
├── security.py         # Encryption utilities
├── requirements.txt    # Python dependencies
├── .env                # Configuration file (not in repo)
├── .gitignore          # Git ignore rules
├── Dockerfile          # Docker configuration
├── docker-compose.yml  # Docker Compose configuration
├── data/               # Database storage (persistent)
├── logs/               # Log files
└── tests/              # Test files
```

### Database Schema

The bot uses an SQLite database with the following tables:
- `users`: Telegram user information
- `encrypted_credentials`: Encrypted Degiro credentials
- `sessions`: Persistent user session data
- `portfolio_history`: Historical portfolio data
- `funds_history`: Historical funds data
- `system_state`: Overall bot state and configuration
- `analysis_history`: Record of insider trading analysis
- `notifications`: Scheduled and sent notifications

## Contributing

1. Fork the repository
2. Create a feature branch
3. Commit your changes
4. Push to the branch
5. Create a new Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.