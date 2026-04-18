from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger
from aiogram import Bot
import asyncio
import logging
from time import monotonic

from database.db import db
from database.models import User
from config_data import config

logger = logging.getLogger(__name__)


class NotificationService:
    def __init__(self, bot: Bot, rate_limit_per_sec: int = 30):
        self.bot = bot
        self.scheduler = AsyncIOScheduler()
        self._running = False
        self.rate_limit_per_sec = max(1, rate_limit_per_sec)

    async def send_daily_notifications(self):
        """Отправка ежедневных уведомлений пользователям, с базовой обработкой ошибок и троттлингом."""
        logger.info("Starting daily notifications job")
        with db.session_scope() as session:
            users = session.query(User).filter(User.notifications == True).all()

        if not users:
            logger.info("No users with notifications enabled")
            return

        delay = 1.0 / self.rate_limit_per_sec
        last = monotonic()

        for user in users:
            try:
                await self.bot.send_message(chat_id=int(user.id), text=config.NOTIFICATION_TEXT)
                logger.debug("Notification sent to %s", int(user.id))
            except Exception as e:
                logger.exception("Failed to send notification to %s: %s", user.id, e)

            now = monotonic()
            elapsed = now - last
            if elapsed < delay:
                await asyncio.sleep(delay - elapsed)
            last = monotonic()

        logger.info("Daily notifications job finished")

    def start_scheduler(self):
        """Запуск планировщика уведомлений"""
        if self._running:
            logger.info("Notification scheduler already running")
            return

        hour, minute = _parse_notification_time(config.NOTIFICATION_TIME)
        self.scheduler.add_job(
            self.send_daily_notifications,
            trigger=CronTrigger(hour=hour, minute=minute),
            id="daily_notifications",
        )
        self.scheduler.start()
        self._running = True
        logger.info("Notification scheduler started")

    def shutdown_scheduler(self):
        """Остановка планировщика"""
        if not self._running:
            logger.info("Notification scheduler not running")
            return
        self.scheduler.shutdown(wait=False)
        self._running = False
        logger.info("Notification scheduler stopped")


notification_service = None


def _parse_notification_time(value: str) -> tuple[int, int]:
    try:
        hour_str, minute_str = value.split(":", 1)
        hour = int(hour_str)
        minute = int(minute_str)
        if 0 <= hour <= 23 and 0 <= minute <= 59:
            return hour, minute
    except (AttributeError, ValueError):
        logger.warning("Invalid notification time '%s', fallback to 09:00", value)

    return 9, 0


def setup_notifications(bot: Bot) -> NotificationService:
    """Инициализация сервиса уведомлений. Возвращает созданный сервис."""
    global notification_service
    notification_service = NotificationService(bot)
    notification_service.start_scheduler()
    return notification_service
