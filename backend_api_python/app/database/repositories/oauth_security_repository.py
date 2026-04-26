"""OAuth and security repository helpers."""
from datetime import datetime

from sqlalchemy import delete, func, select

from app.database.repositories.base import BaseRepository
from app.models.auth_security import LoginAttempt, OAuthState, SecurityLog


class OAuthSecurityRepository(BaseRepository):
    def delete_expired_oauth_states(self):
        self.session.execute(delete(OAuthState).where(OAuthState.expires_at < func.now()))

    def upsert_oauth_state(self, *, state: str, provider: str, redirect: str, expires_at: datetime):
        row = self.session.get(OAuthState, state)
        if row is None:
            row = OAuthState(state=state, provider=provider, redirect=redirect, expires_at=expires_at)
            self.add(row)
        else:
            row.provider = provider
            row.redirect = redirect
            row.expires_at = expires_at
        self.flush()
        return row

    def get_valid_oauth_state_redirect(self, state: str):
        stmt = select(OAuthState).where(OAuthState.state == state, OAuthState.expires_at > func.now())
        row = self.session.execute(stmt).scalar_one_or_none()
        return row.redirect if row else ""

    def consume_oauth_state(self, state: str, provider: str) -> bool:
        stmt = select(OAuthState).where(
            OAuthState.state == state,
            OAuthState.provider == provider,
            OAuthState.expires_at > func.now(),
        )
        row = self.session.execute(stmt).scalar_one_or_none()
        if row is None:
            return False
        self.session.delete(row)
        self.flush()
        return True

    def add_login_attempt(self, **kwargs):
        row = LoginAttempt(**kwargs)
        self.add(row)
        self.flush()
        return row

    def get_login_attempt_summary(self, *, identifier: str, identifier_type: str, window_start: datetime):
        stmt = (
            select(func.count(LoginAttempt.id), func.max(LoginAttempt.attempt_time))
            .where(LoginAttempt.identifier == identifier)
            .where(LoginAttempt.identifier_type == identifier_type)
            .where(LoginAttempt.success.is_(False))
            .where(LoginAttempt.attempt_time > window_start)
        )
        count, last_attempt = self.session.execute(stmt).one()
        return {"count": int(count or 0), "last_attempt": last_attempt}

    def clear_login_attempts(self, *, identifier: str, identifier_type: str):
        self.session.execute(
            delete(LoginAttempt).where(
                LoginAttempt.identifier == identifier,
                LoginAttempt.identifier_type == identifier_type,
            )
        )

    def add_security_log(self, **kwargs):
        row = SecurityLog(**kwargs)
        self.add(row)
        self.flush()
        return row
