"""
Database module for the Insider Trading Bot.

This module handles all database operations using SQLAlchemy ORM,
including user management, session handling, and data persistence.
"""

import os
import logging
import aiosqlite
from typing import Optional, List, Dict, Any
from datetime import datetime
from sqlalchemy import (
    create_engine, Column, Integer, String, Boolean, DateTime, 
    ForeignKey, Float, Text, UniqueConstraint
)
from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from sqlalchemy.exc import SQLAlchemyError
from contextlib import asynccontextmanager

from config import Config

# Configure logging
logger = logging.getLogger(__name__)

# Create base class for declarative models
Base = declarative_base()


class User(Base):
    """
    User model representing a Telegram user of the bot.
    """
    __tablename__ = 'users'
    
    id = Column(Integer, primary_key=True)
    telegram_id = Column(Integer, unique=True, nullable=False)
    username = Column(String)
    first_name = Column(String)
    last_name = Column(String)
    is_active = Column(Boolean, default=True)
    is_admin = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    sessions = relationship("Session", back_populates="user", cascade="all, delete-orphan")
    portfolios = relationship("Portfolio", back_populates="user", cascade="all, delete-orphan")
    funds = relationship("Fund", back_populates="user", cascade="all, delete-orphan")
    analysis_history = relationship("AnalysisHistory", back_populates="user", cascade="all, delete-orphan")


class EncryptedCredential(Base):
    """
    Model for storing encrypted user credentials.
    """
    __tablename__ = 'encrypted_credentials'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    platform = Column(String, nullable=False)  # e.g., 'degiro'
    encrypted_data = Column(Text, nullable=False)  # encrypted JSON
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="sessions")


class Session(Base):
    """
    Model for storing user session information with Degiro.
    """
    __tablename__ = 'sessions'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    session_id = Column(String)  # Degiro session ID
    session_key = Column(String)  # Degiro session key
    client_id = Column(String)  # Degiro client ID
    created_at = Column(DateTime, default=datetime.utcnow)
    expires_at = Column(DateTime)  # Session expiration time
    is_active = Column(Boolean, default=True)
    
    # Relationships
    user = relationship("User", back_populates="sessions")


class Portfolio(Base):
    """
    Model for storing user portfolio information.
    """
    __tablename__ = 'portfolios'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    name = Column(String, nullable=False)
    is_default = Column(Boolean, default=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="portfolios")
    positions = relationship("PortfolioPosition", back_populates="portfolio", cascade="all, delete-orphan")


class PortfolioPosition(Base):
    """
    Model for storing individual positions in a user portfolio.
    """
    __tablename__ = 'portfolio_positions'
    
    id = Column(Integer, primary_key=True)
    portfolio_id = Column(Integer, ForeignKey('portfolios.id'), nullable=False)
    product_id = Column(String, nullable=False)  # Degiro product ID
    symbol = Column(String, nullable=False)
    name = Column(String, nullable=False)
    quantity = Column(Float, nullable=False)
    price = Column(Float, nullable=False)
    total_value = Column(Float, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    portfolio = relationship("Portfolio", back_populates="positions")


class Fund(Base):
    """
    Model for storing user fund information.
    """
    __tablename__ = 'funds'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    currency = Column(String(3), nullable=False)  # e.g., 'EUR', 'USD'
    available_funds = Column(Float, nullable=False)
    total_funds = Column(Float, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="funds")


class SystemState(Base):
    """
    Model for storing global system state information.
    """
    __tablename__ = 'system_state'
    
    id = Column(Integer, primary_key=True)
    last_analysis_run = Column(DateTime)
    last_trade_check = Column(DateTime)
    version = Column(String)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)


class AnalysisHistory(Base):
    """
    Model for storing history of trading analysis runs.
    """
    __tablename__ = 'analysis_history'
    
    id = Column(Integer, primary_key=True)
    user_id = Column(Integer, ForeignKey('users.id'), nullable=False)
    trigger_type = Column(String, nullable=False)  # manual, scheduled, webhook
    status = Column(String, nullable=False)  # success, failed, partial
    details = Column(Text)  # JSON details about the analysis
    created_at = Column(DateTime, default=datetime.utcnow)
    
    # Relationships
    user = relationship("User", back_populates="analysis_history")


class DatabaseManager:
    """
    Database manager class handling all database operations.
    """
    
    def __init__(self):
        """
        Initialize the database manager with configuration.
        """
        self.config = Config()
        self.engine = None
        self.async_engine = None
        self.async_session = None
        self.logger = logging.getLogger(__name__)
        
    async def initialize(self):
        """
        Initialize database connection and create tables if they don't exist.
        """
        try:
            # Create directories if they don't exist
            db_path = self.config.DATABASE_URL.replace('sqlite:///', '')
            os.makedirs(os.path.dirname(db_path), exist_ok=True)
            
            # Create async engine
            self.async_engine = create_async_engine(
                self.config.DATABASE_URL,
                echo=False,  # Set to True for SQL debugging
                future=True
            )
            
            # Create session factory
            self.async_session = sessionmaker(
                self.async_engine, 
                class_=AsyncSession, 
                expire_on_commit=False
            )
            
            # Create tables
            async with self.async_engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
                
            self.logger.info("Database initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Database initialization failed: {e}")
            raise
            
    @asynccontextmanager
    async def get_session(self):
        """
        Context manager for database sessions.
        """
        async with self.async_session() as session:
            try:
                yield session
            except SQLAlchemyError as e:
                await session.rollback()
                self.logger.error(f"Database error: {e}")
                raise
            except Exception as e:
                await session.rollback()
                self.logger.error(f"Unexpected error: {e}")
                raise
            else:
                await session.commit()
                
    async def close(self):
        """
        Close database connections.
        """
        if self.async_engine:
            await self.async_engine.dispose()
            self.logger.info("Database connections closed")
            
    # User management methods
    async def create_user(self, telegram_id: int, username: str = None, 
                         first_name: str = None, last_name: str = None) -> User:
        """
        Create a new user in the database.
        
        Args:
            telegram_id: Telegram user ID
            username: Telegram username
            first_name: User's first name
            last_name: User's last name
            
        Returns:
            User: Created user object
        """
        async with self.get_session() as session:
            user = User(
                telegram_id=telegram_id,
                username=username,
                first_name=first_name,
                last_name=last_name
            )
            session.add(user)
            await session.flush()  # Get the ID without committing
            return user
            
    async def get_user(self, telegram_id: int) -> Optional[User]:
        """
        Retrieve a user by their Telegram ID.
        
        Args:
            telegram_id: Telegram user ID
            
        Returns:
            User or None if not found
        """
        async with self.get_session() as session:
            result = await session.execute(
                select(User).where(User.telegram_id == telegram_id)
            )
            return result.scalar_one_or_none()
            
    async def get_user_by_id(self, user_id: int) -> Optional[User]:
        """
        Retrieve a user by their database ID.
        
        Args:
            user_id: Database user ID
            
        Returns:
            User or None if not found
        """
        async with self.get_session() as session:
            result = await session.execute(
                select(User).where(User.id == user_id)
            )
            return result.scalar_one_or_none()
            
    async def get_all_users(self, active_only: bool = True) -> List[User]:
        """
        Retrieve all users from the database.
        
        Args:
            active_only: If True, only return active users
            
        Returns:
            List of User objects
        """
        async with self.get_session() as session:
            query = select(User)
            if active_only:
                query = query.where(User.is_active == True)
            result = await session.execute(query)
            return result.scalars().all()
            
    async def update_user(self, telegram_id: int, **kwargs) -> bool:
        """
        Update user information.
        
        Args:
            telegram_id: Telegram user ID
            **kwargs: Fields to update
            
        Returns:
            bool: True if update was successful
        """
        async with self.get_session() as session:
            result = await session.execute(
                update(User)
                .where(User.telegram_id == telegram_id)
                .values(**kwargs)
            )
            return result.rowcount > 0
            
    async def delete_user(self, telegram_id: int) -> bool:
        """
        Delete a user from the database.
        
        Args:
            telegram_id: Telegram user ID
            
        Returns:
            bool: True if deletion was successful
        """
        async with self.get_session() as session:
            result = await session.execute(
                delete(User).where(User.telegram_id == telegram_id)
            )
            return result.rowcount > 0
            
    # Session management methods
    async def create_session(self, user_id: int, session_id: str = None,
                            session_key: str = None, client_id: str = None,
                            expires_at: datetime = None) -> Session:
        """
        Create a new session for a user.
        
        Args:
            user_id: Database user ID
            session_id: Degiro session ID
            session_key: Degiro session key
            client_id: Degiro client ID
            expires_at: Session expiration time
            
        Returns:
            Session: Created session object
        """
        async with self.get_session() as session:
            # Deactivate existing sessions for this user
            await session.execute(
                update(Session)
                .where(Session.user_id == user_id)
                .values(is_active=False)
            )
            
            # Create new session
            db_session = Session(
                user_id=user_id,
                session_id=session_id,
                session_key=session_key,
                client_id=client_id,
                expires_at=expires_at,
                is_active=True
            )
            session.add(db_session)
            await session.flush()
            return db_session
            
    async def get_active_session(self, user_id: int) -> Optional[Session]:
        """
        Get the active session for a user.
        
        Args:
            user_id: Database user ID
            
        Returns:
            Session or None if no active session
        """
        async with self.get_session() as session:
            result = await session.execute(
                select(Session)
                .where(Session.user_id == user_id)
                .where(Session.is_active == True)
            )
            return result.scalar_one_or_none()
            
    async def deactivate_session(self, session_id: int) -> bool:
        """
        Deactivate a session.
        
        Args:
            session_id: Database session ID
            
        Returns:
            bool: True if deactivation was successful
        """
        async with self.get_session() as session:
            result = await session.execute(
                update(Session)
                .where(Session.id == session_id)
                .values(is_active=False)
            )
            return result.rowcount > 0
            
    # System state methods
    async def get_system_state(self) -> Optional[SystemState]:
        """
        Retrieve the current system state.
        
        Returns:
            SystemState or None if not found
        """
        async with self.get_session() as session:
            result = await session.execute(select(SystemState))
            state = result.scalar_one_or_none()
            
            if not state:
                # Create default system state
                state = SystemState()
                session.add(state)
                await session.flush()
                
            return state
            
    async def update_system_state(self, **kwargs) -> bool:
        """
        Update the system state.
        
        Args:
            **kwargs: Fields to update
            
        Returns:
            bool: True if update was successful
        """
        async with self.get_session() as session:
            # Check if system state exists
            result = await session.execute(select(SystemState))
            state = result.scalar_one_or_none()
            
            if not state:
                state = SystemState()
                session.add(state)
                
            # Update fields
            for key, value in kwargs.items():
                setattr(state, key, value)
                
            return True

# Import select, update, delete from sqlalchemy for use in methods
from sqlalchemy import select, update, delete