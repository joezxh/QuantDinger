"""User repository helpers."""
from sqlalchemy import func, select

from app.database.repositories.base import BaseRepository
from app.models.user import User


class UserRepository(BaseRepository):
    def get_by_id(self, user_id: int):
        return self.session.get(User, user_id)

    def get_by_username(self, username: str):
        stmt = select(User).where(User.username == username)
        return self.session.execute(stmt).scalar_one_or_none()

    def get_by_email(self, email: str):
        stmt = select(User).where(func.lower(User.email) == func.lower(email))
        return self.session.execute(stmt).scalar_one_or_none()

    def update_last_login(self, user_id: int):
        user = self.get_by_id(user_id)
        if user:
            user.last_login_at = func.now()
            self.flush()
        return user

    def get_token_version(self, user_id: int) -> int:
        user = self.get_by_id(user_id)
        return int(getattr(user, "token_version", 1) or 1) if user else 1

    def increment_token_version(self, user_id: int) -> int:
        user = self.get_by_id(user_id)
        if not user:
            return 1
        user.token_version = int(getattr(user, "token_version", 1) or 1) + 1
        self.flush()
        return int(user.token_version)
