"""Notification repository."""
from sqlalchemy import select, desc

from app.database.repositories.base import BaseRepository
from app.models.notification import StrategyNotification, StrategyLog


class NotificationRepository(BaseRepository):
    def get_notification_by_id(self, notification_id: int):
        return self.session.get(StrategyNotification, notification_id)

    def list_notifications_by_user(
        self, user_id: int, is_read: int = None, limit: int = 50, offset: int = 0,
    ):
        stmt = select(StrategyNotification).where(
            StrategyNotification.user_id == user_id,
        )
        if is_read is not None:
            stmt = stmt.where(StrategyNotification.is_read == is_read)
        stmt = stmt.order_by(desc(StrategyNotification.created_at)).offset(offset).limit(limit)
        return list(self.session.execute(stmt).scalars())

    def list_notifications_by_strategy(self, strategy_id: int, limit: int = 50):
        stmt = (
            select(StrategyNotification)
            .where(StrategyNotification.strategy_id == strategy_id)
            .order_by(desc(StrategyNotification.created_at))
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars())

    def create_notification(self, **kwargs):
        notification = StrategyNotification(**kwargs)
        self.add(notification)
        self.flush()
        return notification

    def mark_read(self, notification_id: int):
        notification = self.get_notification_by_id(notification_id)
        if notification:
            notification.is_read = 1
            self.flush()
        return notification

    def mark_all_read(self, user_id: int):
        stmt = (
            select(StrategyNotification)
            .where(
                StrategyNotification.user_id == user_id,
                StrategyNotification.is_read == 0,
            )
        )
        notifications = list(self.session.execute(stmt).scalars())
        for n in notifications:
            n.is_read = 1
        self.flush()
        return len(notifications)

    def clear_all(self, user_id: int):
        stmt = select(StrategyNotification).where(
            StrategyNotification.user_id == user_id,
        )
        notifications = list(self.session.execute(stmt).scalars())
        for n in notifications:
            self.session.delete(n)
        self.flush()
        return len(notifications)

    def get_log_by_id(self, log_id: int):
        return self.session.get(StrategyLog, log_id)

    def list_logs_by_strategy(self, strategy_id: int, limit: int = 100):
        stmt = (
            select(StrategyLog)
            .where(StrategyLog.strategy_id == strategy_id)
            .order_by(desc(StrategyLog.timestamp))
            .limit(limit)
        )
        return list(self.session.execute(stmt).scalars())

    def create_log(self, **kwargs):
        log = StrategyLog(**kwargs)
        self.add(log)
        self.flush()
        return log
