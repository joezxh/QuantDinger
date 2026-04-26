"""
User Service - Multi-user management

Handles user CRUD operations, password hashing, and role management.
"""
import hashlib
import re
import os
from typing import Optional, Dict, Any

from app.database.repositories.user_repository import UserRepository
from app.database.session import get_session
from app.models.user import User
from app.utils.logger import get_logger

logger = get_logger(__name__)

_TIMEZONE_ID_RE = re.compile(r'^[A-Za-z0-9_/+\-.]+$')

try:
    import bcrypt
    HAS_BCRYPT = True
except ImportError:
    HAS_BCRYPT = False
    logger.warning("bcrypt not installed. Using SHA256 for password hashing (less secure).")


class UserService:
    ROLES = ['viewer', 'user', 'manager', 'admin']
    ROLE_PERMISSIONS = {
        'viewer': ['dashboard', 'view'],
        'user': ['dashboard', 'view', 'indicator', 'backtest', 'strategy', 'portfolio'],
        'manager': ['dashboard', 'view', 'indicator', 'backtest', 'strategy', 'portfolio', 'settings'],
        'admin': ['dashboard', 'view', 'indicator', 'backtest', 'strategy', 'portfolio', 'settings', 'user_manage', 'credentials'],
    }

    def hash_password(self, password: str) -> str:
        if HAS_BCRYPT:
            salt = bcrypt.gensalt(rounds=12)
            return bcrypt.hashpw(password.encode('utf-8'), salt).decode('utf-8')
        salt = os.urandom(16).hex()
        hashed = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
        return f"sha256${salt}${hashed}"

    def verify_password(self, password: str, password_hash: str) -> bool:
        if password_hash.startswith('$2b$') or password_hash.startswith('$2a$'):
            if HAS_BCRYPT:
                try:
                    return bcrypt.checkpw(password.encode('utf-8'), password_hash.encode('utf-8'))
                except Exception:
                    return False
            return False
        if password_hash.startswith('sha256$'):
            parts = password_hash.split('$')
            if len(parts) != 3:
                return False
            salt = parts[1]
            stored_hash = parts[2]
            computed = hashlib.sha256((password + salt).encode('utf-8')).hexdigest()
            return computed == stored_hash
        return False

    def _user_to_dict(self, user) -> Optional[Dict[str, Any]]:
        if not user:
            return None
        return {
            'id': user.id,
            'username': user.username,
            'password_hash': user.password_hash,
            'email': user.email,
            'nickname': user.nickname,
            'avatar': user.avatar,
            'status': user.status,
            'role': user.role,
            'credits': user.credits,
            'vip_expires_at': user.vip_expires_at,
            'timezone': user.timezone,
            'last_login_at': user.last_login_at,
            'created_at': user.created_at,
            'updated_at': user.updated_at,
            'token_version': getattr(user, 'token_version', 1),
        }

    def get_user_by_id(self, user_id: int) -> Optional[Dict[str, Any]]:
        try:
            with get_session() as session:
                user = UserRepository(session).get_by_id(user_id)
                return self._user_to_dict(user)
        except Exception as e:
            logger.error(f"get_user_by_id failed: {e}")
            return None

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        try:
            with get_session() as session:
                user = UserRepository(session).get_by_username(username)
                return self._user_to_dict(user)
        except Exception as e:
            logger.error(f"get_user_by_username failed: {e}")
            return None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        if not email:
            return None
        try:
            with get_session() as session:
                user = UserRepository(session).get_by_email(email)
                return self._user_to_dict(user)
        except Exception as e:
            logger.error(f"get_user_by_email failed: {e}")
            return None

    def authenticate(self, username: str, password: str) -> Optional[Dict[str, Any]]:
        user = self.get_user_by_username(username)
        if not user:
            user = self.get_user_by_email(username)
        if not user:
            return None
        if user.get('status') != 'active':
            logger.warning(f"Login attempt for disabled user: {username}")
            return None
        password_hash = user.get('password_hash', '')
        if not password_hash or password_hash.strip() == '':
            logger.info(f"Password login attempted for code-login user: {username}")
            return {'_no_password': True, **user}
        if not self.verify_password(password, password_hash):
            return None
        try:
            with get_session() as session:
                repo = UserRepository(session)
                updated = repo.update_last_login(user['id'])
                if updated:
                    logger.info(f"Updated last_login_at for user_id={user['id']}")
        except Exception as e:
            logger.error(f"Failed to update last_login_at for user_id={user.get('id')}: {e}")
        user.pop('password_hash', None)
        return user

    def get_token_version(self, user_id: int) -> int:
        try:
            with get_session() as session:
                return UserRepository(session).get_token_version(user_id)
        except Exception as e:
            logger.error(f"get_token_version failed: {e}")
            return 1

    def increment_token_version(self, user_id: int) -> int:
        try:
            with get_session() as session:
                return UserRepository(session).increment_token_version(user_id)
        except Exception as e:
            logger.error(f"increment_token_version failed: {e}")
            return 1

    def get_user_permissions(self, role: str):
        return self.ROLE_PERMISSIONS.get(role or 'user', self.ROLE_PERMISSIONS['user'])

    def list_users(self, page: int = 1, page_size: int = 20, search: str = '') -> Dict[str, Any]:
        """列出用户（分页 + 搜索）"""
        try:
            with get_session() as session:
                query = session.query(User)
                if search:
                    search_pattern = f"%{search}%"
                    query = query.filter(
                        (User.username.ilike(search_pattern)) |
                        (User.email.ilike(search_pattern)) |
                        (User.nickname.ilike(search_pattern))
                    )
                total = query.count()
                items = query.order_by(User.id).offset(
                    (page - 1) * page_size
                ).limit(page_size).all()
                return {
                    "items": [self._user_to_dict(item) for item in items],
                    "total": total,
                    "page": page,
                    "page_size": page_size
                }
        except Exception as e:
            logger.error(f"list_users failed: {e}")
            return {"items": [], "total": 0, "page": page, "page_size": page_size}


def get_user_service() -> UserService:
    return UserService()
