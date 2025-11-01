"""
Utility functions for the Insider Trading Bot.

This module provides various helper functions used throughout the application,
including encryption, data validation, and formatting utilities.
"""

import logging
import json
import hashlib
from typing import Any, Dict, List, Optional
from datetime import datetime
from cryptography.fernet import Fernet
import re

from config import Config

logger = logging.getLogger(__name__)


class EncryptionManager:
    """
    Manages encryption and decryption of sensitive data.
    """
    
    def __init__(self):
        """
        Initialize the encryption manager with the configured key.
        """
        self.config = Config()
        try:
            self.cipher_suite = Fernet(self.config.ENCRYPTION_KEY.encode())
        except Exception as e:
            logger.error(f"Failed to initialize encryption cipher: {e}")
            raise
            
    def encrypt(self, data: str) -> str:
        """
        Encrypt data using Fernet encryption.
        
        Args:
            data: String data to encrypt
            
        Returns:
            Encrypted data as string
        """
        try:
            encrypted_data = self.cipher_suite.encrypt(data.encode())
            return encrypted_data.decode()
        except Exception as e:
            logger.error(f"Encryption failed: {e}")
            raise
            
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt data using Fernet decryption.
        
        Args:
            encrypted_data: Encrypted data as string
            
        Returns:
            Decrypted data as string
        """
        try:
            decrypted_data = self.cipher_suite.decrypt(encrypted_data.encode())
            return decrypted_data.decode()
        except Exception as e:
            logger.error(f"Decryption failed: {e}")
            raise


class DataValidator:
    """
    Validates data formats and constraints.
    """
    
    @staticmethod
    def is_valid_telegram_id(telegram_id: int) -> bool:
        """
        Validate Telegram user ID.
        
        Args:
            telegram_id: Telegram user ID to validate
            
        Returns:
            bool: True if valid
        """
        return isinstance(telegram_id, int) and telegram_id > 0
        
    @staticmethod
    def is_valid_username(username: str) -> bool:
        """
        Validate Telegram username format.
        
        Args:
            username: Username to validate
            
        Returns:
            bool: True if valid
        """
        if not username:
            return True  # Username is optional
            
        # Telegram usernames are 5-32 characters, lowercase letters, digits, underscores
        pattern = r'^[a-zA-Z0-9_]{5,32}$'
        return bool(re.match(pattern, username))
        
    @staticmethod
    def is_valid_email(email: str) -> bool:
        """
        Validate email format.
        
        Args:
            email: Email to validate
            
        Returns:
            bool: True if valid
        """
        if not email:
            return False
            
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return bool(re.match(pattern, email))
        
    @staticmethod
    def is_valid_degiro_credentials(username: str, password: str) -> bool:
        """
        Validate Degiro credentials.
        
        Args:
            username: Degiro username
            password: Degiro password
            
        Returns:
            bool: True if valid
        """
        # Basic validation - in a real implementation, you might want to check
        # against Degiro's actual requirements
        return bool(username and password and len(username) > 0 and len(password) > 0)


class DataFormatter:
    """
    Formats data for display and storage.
    """
    
    @staticmethod
    def format_currency(amount: float, currency: str = "EUR") -> str:
        """
        Format currency amount for display.
        
        Args:
            amount: Amount to format
            currency: Currency code
            
        Returns:
            Formatted currency string
        """
        currency_symbols = {
            "EUR": "€",
            "USD": "$",
            "GBP": "£",
            "JPY": "¥"
        }
        
        symbol = currency_symbols.get(currency, currency)
        return f"{symbol}{amount:,.2f}"
        
    @staticmethod
    def format_percentage(value: float) -> str:
        """
        Format percentage value for display.
        
        Args:
            value: Percentage value
            
        Returns:
            Formatted percentage string
        """
        return f"{value:+.2f}%" if value >= 0 else f"{value:-.2f}%"
        
    @staticmethod
    def format_datetime(dt: datetime, format_type: str = "default") -> str:
        """
        Format datetime for display.
        
        Args:
            dt: Datetime to format
            format_type: Format type (default, short, long)
            
        Returns:
            Formatted datetime string
        """
        formats = {
            "default": "%Y-%m-%d %H:%M:%S",
            "short": "%m/%d %H:%M",
            "long": "%A, %B %d, %Y at %H:%M:%S"
        }
        
        fmt = formats.get(format_type, formats["default"])
        return dt.strftime(fmt)


class JSONEncoder(json.JSONEncoder):
    """
    Custom JSON encoder for handling special data types.
    """
    
    def default(self, obj):
        """
        Override default method to handle datetime objects.
        """
        if isinstance(obj, datetime):
            return obj.isoformat()
        return super().default(obj)


def safe_json_dumps(data: Any) -> str:
    """
    Safely serialize data to JSON string.
    
    Args:
        data: Data to serialize
        
    Returns:
        JSON string representation
    """
    try:
        return json.dumps(data, cls=JSONEncoder, ensure_ascii=False)
    except Exception as e:
        logger.error(f"JSON serialization failed: {e}")
        return "{}"


def safe_json_loads(json_string: str) -> Any:
    """
    Safely deserialize JSON string.
    
    Args:
        json_string: JSON string to deserialize
        
    Returns:
        Deserialized data or None if failed
    """
    try:
        return json.loads(json_string)
    except Exception as e:
        logger.error(f"JSON deserialization failed: {e}")
        return None


def generate_hash(data: str) -> str:
    """
    Generate SHA-256 hash of data.
    
    Args:
        data: String data to hash
        
    Returns:
        SHA-256 hash as hexadecimal string
    """
    return hashlib.sha256(data.encode()).hexdigest()


def chunks(lst: List[Any], n: int) -> List[List[Any]]:
    """
    Split list into chunks of specified size.
    
    Args:
        lst: List to split
        n: Chunk size
        
    Returns:
        List of chunks
    """
    for i in range(0, len(lst), n):
        yield lst[i:i + n]


def truncate_string(text: str, max_length: int = 100, suffix: str = "...") -> str:
    """
    Truncate string to specified length.
    
    Args:
        text: Text to truncate
        max_length: Maximum length
        suffix: Suffix to append if truncated
        
    Returns:
        Truncated string
    """
    if len(text) <= max_length:
        return text
    return text[:max_length - len(suffix)] + suffix


# Global instances for reuse
encryption_manager: Optional[EncryptionManager] = None


def get_encryption_manager() -> EncryptionManager:
    """
    Get singleton instance of EncryptionManager.
    
    Returns:
        EncryptionManager instance
    """
    global encryption_manager
    if encryption_manager is None:
        encryption_manager = EncryptionManager()
    return encryption_manager