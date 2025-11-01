"""
Scheduler module for the Insider Trading Bot.

This module handles periodic tasks such as checking for new insider trades,
updating portfolio information, and running analysis.
"""

import logging
import asyncio
from typing import Optional
from datetime import datetime, timedelta
import traceback

from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.jobstores.base import JobLookupError

from config import Config
from notifications import NotificationSystem

logger = logging.getLogger(__name__)


class Scheduler:
    """
    Manages scheduled tasks for the bot including trade monitoring,
    portfolio updates, and system maintenance.
    """
    
    def __init__(self, bot_instance):
        """
        Initialize the scheduler.
        
        Args:
            bot_instance: Main bot instance for accessing other components
        """
        self.bot = bot_instance
        self.config = Config()
        self.notification_system = bot_instance.notification_system
        self.scheduler = None
        self.is_running = False
        self.logger = logging.getLogger(__name__)
        
        # Job IDs for tracking scheduled tasks
        self.job_ids = {
            'trade_check': 'trade_check_job',
            'portfolio_update': 'portfolio_update_job',
            'system_maintenance': 'system_maintenance_job'
        }
        
    def initialize(self):
        """
        Initialize the scheduler with job stores and executors.
        """
        if self.scheduler is not None:
            self.logger.warning("Scheduler already initialized")
            return
            
        try:
            # Create scheduler with default settings
            self.scheduler = AsyncIOScheduler()
            
            self.logger.info("Scheduler initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize scheduler: {e}")
            raise
            
    def start(self):
        """
        Start the scheduler and all scheduled jobs.
        """
        if self.scheduler is None:
            self.logger.error("Scheduler not initialized")
            return
            
        if self.is_running:
            self.logger.warning("Scheduler already running")
            return
            
        try:
            # Add scheduled jobs
            self._add_scheduled_jobs()
            
            # Start the scheduler
            self.scheduler.start()
            self.is_running = True
            
            self.logger.info("Scheduler started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start scheduler: {e}")
            raise
            
    def _add_scheduled_jobs(self):
        """
        Add all scheduled jobs to the scheduler.
        """
        if self.scheduler is None:
            raise RuntimeError("Scheduler not initialized")
            
        try:
            # Add trade checking job
            self.scheduler.add_job(
                self._check_for_new_trades,
                'interval',
                minutes=self.config.CHECK_INTERVAL_MINUTES,
                id=self.job_ids['trade_check'],
                replace_existing=True,
                next_run_time=datetime.now() + timedelta(seconds=10)  # Run first check after 10 seconds
            )
            
            # Add portfolio update job (if Degiro is enabled)
            if self.config.is_degiro_enabled():
                self.scheduler.add_job(
                    self._update_portfolio_info,
                    'interval',
                    hours=1,  # Update portfolio every hour
                    id=self.job_ids['portfolio_update'],
                    replace_existing=True
                )
                
            # Add system maintenance job
            self.scheduler.add_job(
                self._perform_system_maintenance,
                'interval',
                hours=24,  # Run maintenance daily
                id=self.job_ids['system_maintenance'],
                replace_existing=True
            )
            
            self.logger.info("Scheduled jobs added successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to add scheduled jobs: {e}")
            raise
            
    async def _check_for_new_trades(self):
        """
        Check for new insider trades and send notifications.
        This is the main periodic task of the bot.
        """
        try:
            self.logger.info("Starting insider trade check...")
            
            # Update system state
            await self.bot.state_manager.update_system_state(
                last_trade_check=datetime.utcnow()
            )
            
            # TODO: Implement actual trade checking logic
            # This would involve:
            # 1. Fetching new insider trading data from a source
            # 2. Comparing with existing data in the database
            # 3. Identifying new trades
            # 4. Sending notifications to users
            
            # For now, we'll just log that the check occurred
            self.logger.info("Insider trade check completed")
            
        except Exception as e:
            self.logger.error(f"Error during trade check: {e}")
            self.logger.debug(traceback.format_exc())
            
            # Send admin notification about the error
            await self.notification_system.send_admin_notification(
                f"Error during trade check: {str(e)}"
            )
            
    async def _update_portfolio_info(self):
        """
        Update portfolio information for all connected users.
        """
        try:
            self.logger.info("Starting portfolio update...")
            
            # Get all users with active Degiro sessions
            users = await self.bot.database.get_all_users(active_only=True)
            
            updated_count = 0
            for user in users:
                try:
                    session = await self.bot.state_manager.get_user_session(user.id)
                    if session:
                        # Update portfolio for this user
                        # TODO: Implement portfolio update logic
                        updated_count += 1
                        
                except Exception as e:
                    self.logger.error(f"Error updating portfolio for user {user.telegram_id}: {e}")
                    continue
                    
            self.logger.info(f"Portfolio update completed for {updated_count} users")
            
        except Exception as e:
            self.logger.error(f"Error during portfolio update: {e}")
            self.logger.debug(traceback.format_exc())
            
            # Send admin notification about the error
            await self.notification_system.send_admin_notification(
                f"Error during portfolio update: {str(e)}"
            )
            
    async def _perform_system_maintenance(self):
        """
        Perform regular system maintenance tasks.
        """
        try:
            self.logger.info("Starting system maintenance...")
            
            # TODO: Implement system maintenance tasks such as:
            # 1. Cleaning up old database records
            # 2. Rotating log files
            # 3. Updating system statistics
            # 4. Checking for software updates
            
            self.logger.info("System maintenance completed")
            
        except Exception as e:
            self.logger.error(f"Error during system maintenance: {e}")
            self.logger.debug(traceback.format_exc())
            
            # Send admin notification about the error
            await self.notification_system.send_admin_notification(
                f"Error during system maintenance: {str(e)}"
            )
            
    def pause_job(self, job_id: str) -> bool:
        """
        Pause a scheduled job.
        
        Args:
            job_id: ID of the job to pause
            
        Returns:
            bool: True if job was paused successfully
        """
        if self.scheduler is None or not self.is_running:
            return False
            
        try:
            self.scheduler.pause_job(job_id)
            self.logger.info(f"Job {job_id} paused successfully")
            return True
            
        except JobLookupError:
            self.logger.warning(f"Job {job_id} not found")
            return False
        except Exception as e:
            self.logger.error(f"Error pausing job {job_id}: {e}")
            return False
            
    def resume_job(self, job_id: str) -> bool:
        """
        Resume a paused scheduled job.
        
        Args:
            job_id: ID of the job to resume
            
        Returns:
            bool: True if job was resumed successfully
        """
        if self.scheduler is None or not self.is_running:
            return False
            
        try:
            self.scheduler.resume_job(job_id)
            self.logger.info(f"Job {job_id} resumed successfully")
            return True
            
        except JobLookupError:
            self.logger.warning(f"Job {job_id} not found")
            return False
        except Exception as e:
            self.logger.error(f"Error resuming job {job_id}: {e}")
            return False
            
    def shutdown(self):
        """
        Shutdown the scheduler and all jobs.
        """
        if self.scheduler is None or not self.is_running:
            return
            
        try:
            self.scheduler.shutdown()
            self.is_running = False
            self.logger.info("Scheduler shutdown completed")
            
        except Exception as e:
            self.logger.error(f"Error during scheduler shutdown: {e}")
            
    def get_job_status(self) -> dict:
        """
        Get the status of all scheduled jobs.
        
        Returns:
            dict: Dictionary with job statuses
        """
        if self.scheduler is None:
            return {}
            
        try:
            jobs = self.scheduler.get_jobs()
            status = {}
            
            for job in jobs:
                status[job.id] = {
                    'name': job.name,
                    'next_run_time': job.next_run_time.isoformat() if job.next_run_time else None,
                    'pending': job.pending
                }
                
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting job status: {e}")
            return {}