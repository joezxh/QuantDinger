"""
Authentication Utilities

JWT token generation, verification, and middleware decorators.
Supports multi-user authentication with role-based access control.
"""
import jwt
import datetime
import os
from functools import wraps
from flask import request, jsonify, g
from app.config.settings import Config
from app.utils.logger import get_logger

logger = get_logger(__name__)


def generate_token(user_id: int, username: str, role: str = 'user', token_version: int = 1) -> str:
    try:
        payload = {
            'exp': datetime.datetime.utcnow() + datetime.timedelta(days=7),
            'iat': datetime.datetime.utcnow(),
            'sub': username,
            'user_id': user_id,
            'role': role,
            'token_version': token_version,
        }
        return jwt.encode(payload, Config.SECRET_KEY, algorithm='HS256')
    except Exception as e:
        logger.error(f"Token generation failed: {e}")
        return None


def verify_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, Config.SECRET_KEY, algorithms=['HS256'])
        user_id = payload.get('user_id')
        token_version = payload.get('token_version')
        if user_id and token_version is not None:
            if not _verify_token_version(user_id, token_version):
                logger.debug(f"Token version mismatch for user {user_id}: expected current, got {token_version}")
                return None
        return payload
    except jwt.ExpiredSignatureError:
        logger.debug("Token expired")
        return None
    except jwt.InvalidTokenError as e:
        logger.debug(f"Invalid token: {e}")
        return None


def _verify_token_version(user_id: int, token_version: int) -> bool:
    try:
        from app.services.user_service import get_user_service
        db_token_version = get_user_service().get_token_version(user_id)
        return int(token_version) == int(db_token_version)
    except Exception as e:
        logger.error(f"_verify_token_version failed: {e}")
        return False


def get_current_user_id() -> int:
    return getattr(g, 'user_id', None)


def get_current_user_role() -> str:
    return getattr(g, 'user_role', 'user')


def login_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        auth_header = request.headers.get('Authorization')
        if auth_header:
            parts = auth_header.split()
            if len(parts) == 2 and parts[0].lower() == 'bearer':
                token = parts[1]
        if not token:
            return jsonify({'code': 401, 'msg': 'Token missing', 'data': None}), 401
        payload = verify_token(token)
        if not payload:
            return jsonify({'code': 401, 'msg': 'Token invalid or expired', 'data': None}), 401
        g.user = payload.get('sub')
        g.user_id = payload.get('user_id')
        g.user_role = payload.get('role', 'user')
        return f(*args, **kwargs)
    return decorated


def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        user_id = getattr(g, 'user_id', None)
        # Legacy check — fallback to simple role string
        role = getattr(g, 'user_role', None)
        if role == 'admin':
            return f(*args, **kwargs)
        # RBAC check — user must have super_admin or admin role
        if user_id:
            try:
                from app.services.permission_service import get_permission_service
                svc = get_permission_service()
                codes = svc.get_user_permission_codes(user_id)
                # Admin-level access: has system management permissions
                if 'system:user:view' in codes or 'system:role:view' in codes:
                    return f(*args, **kwargs)
            except Exception as e:
                logger.warning(f"RBAC admin check failed: {e}")
        return jsonify({'code': 403, 'msg': 'Admin access required', 'data': None}), 403
    return decorated


def manager_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        role = getattr(g, 'user_role', None)
        if role not in ('admin', 'manager'):
            return jsonify({'code': 403, 'msg': 'Manager access required', 'data': None}), 403
        return f(*args, **kwargs)
    return decorated


def permission_required(permission: str):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user_id = getattr(g, 'user_id', None)
            # Legacy check — use hardcoded role permissions
            role = getattr(g, 'user_role', 'user')
            from app.services.user_service import get_user_service
            permissions = get_user_service().get_user_permissions(role)
            if permission in permissions:
                return f(*args, **kwargs)
            # RBAC check — use database permission codes
            if user_id:
                try:
                    from app.services.permission_service import get_permission_service
                    svc = get_permission_service()
                    if svc.has_permission(user_id, permission):
                        return f(*args, **kwargs)
                except Exception as e:
                    logger.warning(f"RBAC permission check failed: {e}")
            return jsonify({'code': 403, 'msg': f'Permission denied: {permission}', 'data': None}), 403
        return decorated
    return decorator


def require_permission(permission_code: str):
    """RBAC 权限装饰器 — 检查用户是否拥有指定 permission_code
    
    用法:
        @require_permission('system:user:create')
        def create_user():
            ...
    """
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            user_id = getattr(g, 'user_id', None)
            if not user_id:
                return jsonify({'code': 403, 'msg': 'Authentication required', 'data': None}), 403
            try:
                from app.services.permission_service import get_permission_service
                svc = get_permission_service()
                if svc.has_permission(user_id, permission_code):
                    return f(*args, **kwargs)
            except Exception as e:
                logger.error(f"require_permission check failed: {e}")
            return jsonify({'code': 403, 'msg': f'Permission denied: {permission_code}', 'data': None}), 403
        return decorated
    return decorator


def _is_single_user_mode() -> bool:
    return os.getenv('SINGLE_USER_MODE', 'false').lower() == 'true'


def authenticate_legacy(username: str, password: str) -> dict:
    if username == Config.ADMIN_USER and password == Config.ADMIN_PASSWORD:
        return {'user_id': 1, 'username': username, 'role': 'admin', 'nickname': 'Admin'}
    return None
