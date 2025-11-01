"""
State Manager module for the Insider Trading Bot.

This module handles the persistence and recovery of bot state,
including user sessions, portfolio data, and system configuration.
"""

import logging
from typing import Dict, Any, Optional
from datetime import datetime, timedelta
import asyncio

from database import DatabaseManager, User, Session
from degiro_client import DegiroClient
from config import Config

logger = logging.getLogger(__name__)


class StateManager:
    """
    Manages the bot's state including user sessions, portfolio data, and recovery procedures.
    """
    
    def __init__(self, database: DatabaseManager):
        """
        Initialize the state manager.
        
        Args:
            database: Database manager instance
        """
        self.database = database
        self.config = Config()
        self.degiro_client = DegiroClient()
        self._is_recovering = False
        self.logger = logging.getLogger(__name__)
        
    async def recover_state(self):
        """
        Recover system state from database on startup.
        This includes restoring user sessions and checking for expired sessions.
        """
        if self._is_recovering:
            self.logger.warning("State recovery already in progress")
            return
            
        self._is_recovering = True
        self.logger.info("Starting state recovery...")
        
        try:
            # Recover system state
            await self._recover_system_state()
            
            # Recover user sessions
            await self._recover_user_sessions()
            
            self.logger.info("State recovery completed successfully")
            
        except Exception as e:
            self.logger.error(f"State recovery failed: {e}")
            raise
        finally:
            self._is_recovering = False
            
    async def _recover_system_state(self):
        """
        Recover global system state from database.
        """
        try:
            system_state = await self.database.get_system_state()
            if system_state:
                self.logger.info(
                    f"Recovered system state (last analysis: {system_state.last_analysis_run})"
                )
            else:
                self.logger.info("No existing system state found, starting fresh")
                
        except Exception as e:
            self.logger.error(f"Failed to recover system state: {e}")
            raise
            
    async def _recover_user_sessions(self):
        """
        Recover and validate all user sessions.
        Attempt to reconnect users with valid credentials.
        """
        try:
            users = await self.database.get_all_users(active_only=True)
            self.logger.info(f"Found {len(users)} active users to recover sessions for")
            
            reconnected_count = 0
            for user in users:
                try:
                    # Check if user has an active session
                    session = await self.database.get_active_session(user.id)
                    if session and await self._is_session_valid(session):
                        self.logger.info(f"Session for user {user.telegram_id} is still valid")
                        reconnected_count += 1
                        continue
                        
                    # If no valid session, attempt to reconnect if Degiro is enabled
                    if self.config.is_degiro_enabled():
                        if await self._reconnect_user(user):
                            reconnected_count += 1
                            
                except Exception as e:
                    self.logger.error(f"Error recovering session for user {user.telegram_id}: {e}")
                    continue
                    
            self.logger.info(f"Successfully reconnected {reconnected_count} users")
            
        except Exception as e:
            self.logger.error(f"Failed to recover user sessions: {e}")
            raise
            
    async def _is_session_valid(self, session) -> bool:
        """
        Check if a session is still valid by testing its credentials.
        
        Args:
            session: Session object to validate
            
        Returns:
            bool: True if session is valid, False otherwise
        """
        try:
            # Check if session has expired
            if session.expires_at and session.expires_at < datetime.utcnow():
                return False
                
            # Additional validation logic could be added here
            # For now, we'll assume sessions are valid if they haven't expired
            return True
            
        except Exception as e:
            self.logger.error(f"Error validating session: {e}")
            return False
            
    async def _reconnect_user(self, user: User) -> bool:
        """
        Attempt to reconnect a user using stored credentials.
        
        Args:
            user: User object to reconnect
            
        Returns:
            bool: True if reconnection was successful
        """
        try:
            # Try to get stored credentials (this is a simplified implementation)
            # In a real implementation, you would retrieve and decrypt stored credentials
            username = self.config.DEGIRO_USERNAME
            password = self.config.DEGIRO_PASSWORD
            
            if not username or not password:
                self.logger.warning(f"No credentials found for user {user.telegram_id}")
                return False
                
            # Attempt to login
            # Note: In a real implementation, you would need to handle
            # credential storage and retrieval per user
            login_success = await self.degiro_client.login(username, password)
            
            if login_success:
                # Store new session in database
                client = self.degiro_client.get_client()
                if client:
                    await self.database.create_session(
                        user_id=user.id,
                        session_id=client.session_id,
                        session_key=client.session_key,
                        client_id=client.client_id,
                        expires_at=datetime.utcnow() + timedelta(hours=30)  # Degiro sessions typically last 30 minutes
                    )
                    self.logger.info(f"Successfully reconnected user {user.telegram_id}")
                    return True
            else:
                self.logger.warning(f"Failed to reconnect user {user.telegram_id}")
                return False
                
        except Exception as e:
            self.logger.error(f"Error reconnecting user {user.telegram_id}: {e}")
            return False
            
    async def save_user_session(self, user_id: int, session_data: Dict[str, Any]) -> bool:
        """
        Save a user session to the database.
        
        Args:
            user_id: Database user ID
            session_data: Dictionary containing session information
            
        Returns:
            bool: True if save was successful
        """
        try:
            session = await self.database.create_session(
                user_id=user_id,
                session_id=session_data.get('session_id'),
                session_key=session_data.get('session_key'),
                client_id=session_data.get('client_id'),
                expires_at=session_data.get('expires_at')
            )
            return session is not None
            
        except Exception as e:
            self.logger.error(f"Error saving session for user {user_id}: {e}")
            return False
            
    async def clear_user_session(self, user_id: int) -> bool:
        """
        Clear a user's session from the database.
        
        Args:
            user_id: Database user ID
            
        Returns:
            bool: True if clear was successful
        """
        try:
            session = await self.database.get_active_session(user_id)
            if session:
                return await self.database.deactivate_session(session.id)
            return True  # No active session to clear
            
        except Exception as e:
            self.logger.error(f"Error clearing session for user {user_id}: {e}")
            return False
            
    async def get_user_session(self, user_id: int) -> Optional[Session]:
        """
        Get a user's active session.
        
        Args:
            user_id: Database user ID
            
        Returns:
            Session object or None if no active session
        """
        try:
            return await self.database.get_active_session(user_id)
        except Exception as e:
            self.logger.error(f"Error retrieving session for user {user_id}: {e}")
            return None
            
    async def update_system_state(self, **kwargs) -> bool:
        """
        Update the system state in the database.
        
        Args:
            **kwargs: Fields to update in system state
            
        Returns:
            bool: True if update was successful
        """
        try:
            return await self.database.update_system_state(**kwargs)
        except Exception as e:
            self.logger.error(f"Error updating system state: {e}")
            return False
            
    def is_recovering(self) -> bool:
        """
        Check if state recovery is currently in progress.
        
        Returns:
            bool: True if recovery is in progress
        """
        return self._is_recovering