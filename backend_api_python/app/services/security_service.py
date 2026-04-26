"""
Security Service - Handles Turnstile verification, rate limiting, and brute-force protection.
"""
import os
import json
import requests
from datetime import datetime, timedelta
from typing import Tuple, Optional, Dict, Any

from app.database.repositories.oauth_security_repository import OAuthSecurityRepository
from app.database.session import get_session
from app.utils.logger import get_logger

logger = get_logger(__name__)

_security_service = None


def get_security_service():
    global _security_service
    if _security_service is None:
        _security_service = SecurityService()
    return _security_service


class SecurityService:
    """Security service for authentication protection"""

    def __init__(self):
        self._load_config()

    def _load_config(self):
        self.turnstile_site_key = os.getenv('TURNSTILE_SITE_KEY', '')
        self.turnstile_secret_key = os.getenv('TURNSTILE_SECRET_KEY', '')
        self.turnstile_enabled = bool(self.turnstile_site_key and self.turnstile_secret_key)
        self.ip_max_attempts = int(os.getenv('SECURITY_IP_MAX_ATTEMPTS', '10'))
        self.ip_window_minutes = int(os.getenv('SECURITY_IP_WINDOW_MINUTES', '5'))
        self.ip_block_minutes = int(os.getenv('SECURITY_IP_BLOCK_MINUTES', '15'))
        self.account_max_attempts = int(os.getenv('SECURITY_ACCOUNT_MAX_ATTEMPTS', '5'))
        self.account_window_minutes = int(os.getenv('SECURITY_ACCOUNT_WINDOW_MINUTES', '60'))
        self.account_block_minutes = int(os.getenv('SECURITY_ACCOUNT_BLOCK_MINUTES', '30'))
        self.code_rate_limit_seconds = int(os.getenv('VERIFICATION_CODE_RATE_LIMIT', '60'))
        self.code_ip_hourly_limit = int(os.getenv('VERIFICATION_CODE_IP_HOURLY_LIMIT', '10'))

    def get_security_config(self) -> Dict[str, Any]:
        mobile_ver = (os.getenv('MOBILE_APP_LATEST_VERSION') or '').strip()
        mobile_url = (os.getenv('MOBILE_APP_DOWNLOAD_URL') or '').strip() or 'https://www.quantdinger.com/download/app.apk'
        return {
            'turnstile_enabled': self.turnstile_enabled,
            'turnstile_site_key': self.turnstile_site_key,
            'registration_enabled': os.getenv('ENABLE_REGISTRATION', 'true').lower() == 'true',
            'oauth_google_enabled': bool(os.getenv('GOOGLE_CLIENT_ID', '')),
            'oauth_github_enabled': bool(os.getenv('GITHUB_CLIENT_ID', '')),
            'mobile_app_latest_version': mobile_ver,
            'mobile_app_download_url': mobile_url,
        }

    def verify_turnstile(self, token: str, ip_address: str = None) -> Tuple[bool, str]:
        if not self.turnstile_enabled:
            return True, 'turnstile_disabled'
        if not token:
            return False, 'Missing Turnstile token'
        try:
            response = requests.post(
                'https://challenges.cloudflare.com/turnstile/v0/siteverify',
                data={'secret': self.turnstile_secret_key, 'response': token, 'remoteip': ip_address},
                timeout=10,
            )
            result = response.json()
            if result.get('success'):
                return True, 'verified'
            error_codes = result.get('error-codes', [])
            logger.warning(f"Turnstile verification failed: {error_codes}")
            return False, 'Turnstile verification failed'
        except requests.RequestException as e:
            logger.error(f"Turnstile API error: {e}")
            return False, 'Turnstile service unavailable'

    def record_login_attempt(self, identifier: str, identifier_type: str, success: bool, ip_address: str = None, user_agent: str = None) -> bool:
        try:
            with get_session() as session:
                OAuthSecurityRepository(session).add_login_attempt(
                    identifier=identifier,
                    identifier_type=identifier_type,
                    success=success,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    attempt_time=datetime.now(),
                )
            return True
        except Exception as e:
            logger.error(f"Failed to record login attempt: {e}")
            return False

    def is_blocked(self, identifier: str, identifier_type: str) -> Tuple[bool, int]:
        try:
            if identifier_type == 'ip':
                max_attempts = self.ip_max_attempts
                window_minutes = self.ip_window_minutes
                block_minutes = self.ip_block_minutes
            else:
                max_attempts = self.account_max_attempts
                window_minutes = self.account_window_minutes
                block_minutes = self.account_block_minutes
            window_start = datetime.now() - timedelta(minutes=window_minutes)
            with get_session() as session:
                row = OAuthSecurityRepository(session).get_login_attempt_summary(
                    identifier=identifier,
                    identifier_type=identifier_type,
                    window_start=window_start,
                )
            failed_count = row['count'] or 0
            last_attempt = row['last_attempt']
            if failed_count >= max_attempts and last_attempt:
                block_until = last_attempt + timedelta(minutes=block_minutes)
                if datetime.now() < block_until:
                    remaining = int((block_until - datetime.now()).total_seconds())
                    return True, remaining
            return False, 0
        except Exception as e:
            logger.error(f"Failed to check block status: {e}")
            return False, 0

    def check_login_allowed(self, username: str, ip_address: str) -> Tuple[bool, str]:
        ip_blocked, ip_remaining = self.is_blocked(ip_address, 'ip')
        if ip_blocked:
            minutes = ip_remaining // 60
            return False, f'Too many failed attempts from this IP. Try again in {minutes + 1} minutes.'
        account_blocked, account_remaining = self.is_blocked(username, 'account')
        if account_blocked:
            minutes = account_remaining // 60
            return False, f'Account temporarily locked due to too many failed attempts. Try again in {minutes + 1} minutes.'
        return True, 'allowed'

    def clear_login_attempts(self, identifier: str, identifier_type: str) -> bool:
        try:
            with get_session() as session:
                OAuthSecurityRepository(session).clear_login_attempts(identifier=identifier, identifier_type=identifier_type)
            return True
        except Exception as e:
            logger.error(f"Failed to clear login attempts: {e}")
            return False

    def log_security_event(self, action: str, user_id: int = None, ip_address: str = None, user_agent: str = None, details: dict = None) -> bool:
        try:
            with get_session() as session:
                OAuthSecurityRepository(session).add_security_log(
                    user_id=user_id,
                    action=action,
                    ip_address=ip_address,
                    user_agent=user_agent,
                    details_json=json.dumps(details) if details else None,
                )
            return True
        except Exception as e:
            logger.error(f"Failed to log security event: {e}")
            return False
