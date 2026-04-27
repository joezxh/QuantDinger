"""Verification code repository."""
from datetime import datetime, timezone

from sqlalchemy import func, select

from app.database.repositories.base import BaseRepository
from app.models.verification import VerificationCode, OAuthLink


class VerificationRepository(BaseRepository):
    def get_by_id(self, code_id: int):
        return self.session.get(VerificationCode, code_id)

    def get_valid_code(self, email: str, code: str, code_type: str):
        stmt = (
            select(VerificationCode)
            .where(
                VerificationCode.email == email,
                VerificationCode.code == code,
                VerificationCode.type == code_type,
                VerificationCode.used_at.is_(None),
                VerificationCode.expires_at > datetime.now(timezone.utc),
            )
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def create_code(self, *, email, code, code_type, expires_at, **kwargs):
        record = VerificationCode(
            email=email,
            code=code,
            type=code_type,
            expires_at=expires_at,
            **kwargs,
        )
        self.add(record)
        self.flush()
        return record

    def mark_used(self, code_id: int):
        code = self.get_by_id(code_id)
        if code:
            code.used_at = datetime.now(timezone.utc)
            self.flush()
        return code

    def invalidate_old_codes(self, email: str, code_type: str):
        """Mark all existing unused codes of the same type as used."""
        stmt = (
            select(VerificationCode)
            .where(
                VerificationCode.email == email,
                VerificationCode.type == code_type,
                VerificationCode.used_at.is_(None),
            )
        )
        codes = list(self.session.execute(stmt).scalars())
        now = datetime.now(timezone.utc)
        for code in codes:
            code.used_at = now
        self.flush()
        return len(codes)

    def get_latest_unused(self, email: str, code_type: str):
        """Get the most recent unused code for this email/type."""
        stmt = (
            select(VerificationCode)
            .where(
                VerificationCode.email == email,
                VerificationCode.type == code_type,
                VerificationCode.used_at.is_(None),
            )
            .order_by(VerificationCode.created_at.desc())
            .limit(1)
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def count_locked(self, email: str, code_type: str, max_attempts: int, lock_window: datetime) -> int:
        """Count how many codes are locked due to too many failed attempts."""
        stmt = (
            select(func.count(VerificationCode.id))
            .where(
                VerificationCode.email == email,
                VerificationCode.type == code_type,
                VerificationCode.attempts >= max_attempts,
                VerificationCode.last_attempt_at > lock_window,
                VerificationCode.used_at.is_(None),
            )
        )
        return self.session.execute(stmt).scalar() or 0

    def increment_attempts(self, code_id: int) -> int:
        """Increment attempt counter and return new value."""
        code = self.get_by_id(code_id)
        if code:
            code.attempts = (code.attempts or 0) + 1
            code.last_attempt_at = datetime.now(timezone.utc)
            self.flush()
            return code.attempts
        return 0

    def count_recent_by_email(self, email: str, since: datetime) -> int:
        """Count verification codes sent to this email since the given time."""
        stmt = (
            select(func.count(VerificationCode.id))
            .where(
                VerificationCode.email == email,
                VerificationCode.created_at > since,
            )
        )
        return self.session.execute(stmt).scalar() or 0

    def count_recent_by_ip(self, ip_address: str, since: datetime) -> int:
        """Count verification codes sent from this IP since the given time."""
        stmt = (
            select(func.count(VerificationCode.id))
            .where(
                VerificationCode.ip_address == ip_address,
                VerificationCode.created_at > since,
            )
        )
        return self.session.execute(stmt).scalar() or 0

    def get_oauth_link_by_provider(self, provider: str, provider_user_id: str):
        stmt = (
            select(OAuthLink)
            .where(
                OAuthLink.provider == provider,
                OAuthLink.provider_user_id == provider_user_id,
            )
        )
        return self.session.execute(stmt).scalar_one_or_none()

    def list_oauth_links_by_user(self, user_id: int):
        stmt = select(OAuthLink).where(OAuthLink.user_id == user_id)
        return list(self.session.execute(stmt).scalars())

    def create_oauth_link(self, **kwargs):
        link = OAuthLink(**kwargs)
        self.add(link)
        self.flush()
        return link
