"""
Configuration module for the Insider Trading Bot.

This module handles loading and validation of environment variables,
providing a centralized configuration interface for the entire application.
"""

import os
from typing import Optional
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """
    Configuration class that loads and validates all environment variables.
    """

    # Telegram Configuration
    TELEGRAM_TOKEN: str = os.getenv("TELEGRAM_TOKEN", "")
    
    # Degiro Configuration
    DEGIRO_USERNAME: Optional[str] = os.getenv("DEGIRO_USERNAME")
    DEGIRO_PASSWORD: Optional[str] = os.getenv("DEGIRO_PASSWORD")
    
    # Encryption Configuration
    ENCRYPTION_KEY: str = os.getenv("ENCRYPTION_KEY", "")
    
    # Database Configuration
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./data/insider_trading.db")
    
    # Scheduler Configuration
    CHECK_INTERVAL_MINUTES: int = int(os.getenv("CHECK_INTERVAL_MINUTES", "30"))
    
    # Logging Configuration
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
    
    # Validation flags
    _is_validated: bool = False
    
    @classmethod
    def validate(cls) -> bool:
        """
        Validate that all required configuration values are present.
        
        Returns:
            bool: True if all required config values are present, False otherwise
        """
        if cls._is_validated:
            return True
            
        # Validate required configurations
        required_configs = [
            ("TELEGRAM_TOKEN", cls.TELEGRAM_TOKEN),
            ("ENCRYPTION_KEY", cls.ENCRYPTION_KEY),
        ]
        
        missing_configs = []
        for name, value in required_configs:
            if not value:
                missing_configs.append(name)
        
        if missing_configs:
            raise ValueError(
                f"Missing required configuration values: {', '.join(missing_configs)}. "
                f"Please check your .env file."
            )
            
        # Validate encryption key length (should be 32 bytes for Fernet)
        if len(cls.ENCRYPTION_KEY.encode()) != 32:
            raise ValueError(
                f"ENCRYPTION_KEY must be 32 bytes long. "
                f"Current length: {len(cls.ENCRYPTION_KEY.encode())} bytes"
            )
            
        cls._is_validated = True
        return True
        
    @classmethod
    def is_degiro_enabled(cls) -> bool:
        """
        Check if Degiro integration is enabled.
        
        Returns:
            bool: True if both Degiro username and password are configured
        """
        return bool(cls.DEGIRO_USERNAME and cls.DEGIRO_PASSWORD)


# Validate configuration on import
try:
    Config.validate()
except ValueError as e:
    print(f"Configuration Error: {e}")
    raise