"""
OAuth Service - Handles Google and GitHub OAuth authentication.
"""
import os
import secrets
import requests
from urllib.parse import urlencode, urlparse
from datetime import datetime, timezone, timedelta
from typing import Tuple, Optional, Dict, Any

from app.database.repositories.oauth_security_repository import OAuthSecurityRepository
from app.database.session import get_session
from app.utils.logger import get_logger

logger = get_logger(__name__)

_oauth_service = None


def get_oauth_service():
    global _oauth_service
    if _oauth_service is None:
        _oauth_service = OAuthService()
    return _oauth_service


class OAuthService:
    """OAuth service for Google and GitHub authentication"""

    _state_schema_ensured: bool = False

    def __init__(self):
        self._load_config()

    def _oauth_state_ttl_minutes(self) -> int:
        try:
            return max(5, min(120, int(float(os.getenv("OAUTH_STATE_TTL_MINUTES", "20") or 20))))
        except Exception:
            return 20

    def _oauth_state_save(self, state: str, provider: str, redirect: Optional[str]) -> None:
        exp = datetime.now(timezone.utc) + timedelta(minutes=self._oauth_state_ttl_minutes())
        red = (redirect or "").strip() if redirect else ""
        with get_session() as session:
            repo = OAuthSecurityRepository(session)
            repo.delete_expired_oauth_states()
            repo.upsert_oauth_state(state=state, provider=provider, redirect=red, expires_at=exp)

    def _oauth_state_peek_redirect(self, state: str) -> str:
        if not state:
            return ""
        try:
            with get_session() as session:
                return OAuthSecurityRepository(session).get_valid_oauth_state_redirect(state)
        except Exception as e:
            logger.warning(f"OAuth state peek failed: {e}")
            return ""

    def _oauth_state_consume(self, state: str, provider: str) -> bool:
        if not state:
            return False
        try:
            with get_session() as session:
                return OAuthSecurityRepository(session).consume_oauth_state(state, provider)
        except Exception as e:
            logger.error(f"OAuth state consume failed: {e}", exc_info=True)
            return False

    def _load_config(self):
        self.google_client_id = os.getenv('GOOGLE_CLIENT_ID', '')
        self.google_client_secret = os.getenv('GOOGLE_CLIENT_SECRET', '')
        self.google_redirect_uri = os.getenv('GOOGLE_REDIRECT_URI', '')
        self.google_enabled = bool(self.google_client_id and self.google_client_secret)
        self.github_client_id = os.getenv('GITHUB_CLIENT_ID', '')
        self.github_client_secret = os.getenv('GITHUB_CLIENT_SECRET', '')
        self.github_redirect_uri = os.getenv('GITHUB_REDIRECT_URI', '')
        self.github_enabled = bool(self.github_client_id and self.github_client_secret)
        self.frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:8080')
        raw_allowed = os.getenv('OAUTH_ALLOWED_REDIRECTS', '')
        extra = [x.strip() for x in raw_allowed.split(',') if x.strip()]
        self.allowed_redirect_origins = set()
        for item in [self.frontend_url] + extra:
            origin = self._normalize_origin(item)
            if origin:
                self.allowed_redirect_origins.add(origin)

    @staticmethod
    def _normalize_origin(url: str) -> str:
        if not url:
            return ''
        try:
            parsed = urlparse(url if '://' in url else f'https://{url}')
            if not parsed.scheme or not parsed.netloc:
                return ''
            return f"{parsed.scheme}://{parsed.netloc}".lower().rstrip('/')
        except Exception:
            return ''

    def is_redirect_allowed(self, redirect_url: str) -> bool:
        origin = self._normalize_origin(redirect_url)
        if not origin:
            return False
        return origin in self.allowed_redirect_origins

    def peek_state_redirect(self, state: str) -> str:
        return self._oauth_state_peek_redirect(state)
