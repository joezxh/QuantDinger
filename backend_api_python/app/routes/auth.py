"""Authentication API Routes"""
import os
from flask import Blueprint, request, jsonify, g
from urllib.parse import urlencode, urlparse, urlunparse, parse_qsl
from app.utils.auth import generate_token, authenticate_legacy, login_required, get_current_user_id
from app.utils.logger import get_logger

logger = get_logger(__name__)
auth_bp = Blueprint('auth', __name__)


def _build_frontend_login_redirect(frontend_url: str, **params) -> str:
    base = (frontend_url or '').strip().rstrip('/')
    if not base:
        base = 'http://localhost:8080'
    candidate = base if '://' in base else f'https://{base}'
    try:
        parsed = urlparse(candidate)
    except Exception:
        parsed = None
    origin = ''
    has_real_path = False
    has_hash_route = False
    if parsed and parsed.scheme and parsed.netloc:
        origin = f"{parsed.scheme}://{parsed.netloc}".rstrip('/')
        if parsed.fragment:
            has_hash_route = True
        path_part = (parsed.path or '').rstrip('/')
        if path_part and path_part != '':
            has_real_path = True
    else:
        origin = base
    clean_params = {k: v for k, v in params.items() if v is not None and v != ''}
    qs = urlencode(clean_params)
    if has_hash_route:
        login_url = f"{origin}/#/user/login"
        return f"{login_url}?{qs}" if qs else login_url
    if has_real_path:
        existing_qs = dict(parse_qsl(parsed.query or '', keep_blank_values=True))
        existing_qs.update(clean_params)
        return urlunparse((parsed.scheme, parsed.netloc, parsed.path, parsed.params, urlencode(existing_qs), ''))
    login_url = f"{origin}/#/user/login"
    return f"{login_url}?{qs}" if qs else login_url


def _is_single_user_mode() -> bool:
    return os.getenv('SINGLE_USER_MODE', 'false').lower() == 'true'


def _get_client_ip() -> str:
    if request.headers.get('X-Forwarded-For'):
        return request.headers.get('X-Forwarded-For').split(',')[0].strip()
    if request.headers.get('X-Real-IP'):
        return request.headers.get('X-Real-IP')
    return request.remote_addr or '0.0.0.0'


def _get_user_agent() -> str:
    return request.headers.get('User-Agent', '')[:500]


@auth_bp.route('/login', methods=['POST'])
def login():
    """
    ---
    tags:
      - System/Authentication
    summary: "User login"
    description: "Authenticate with username/email and password. Supports captcha verification, rate limiting, and security event logging."
    produces:
      - application/json
    consumes:
      - application/json
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - username
            - password
          properties:
            username:
              type: string
              description: "Username or email address"
            password:
              type: string
              description: "Account password"
            turnstile_token:
              type: string
              description: "Cloudflare Turnstile verification token (optional)"
    responses:
      200:
        description: Login successful, returns JWT token and user info
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 1
            msg:
              type: string
              example: Login successful
            data:
              type: object
              properties:
                token:
                  type: string
                  description: "JWT access token for subsequent API calls"
                userinfo:
                  type: object
                  description: "Current user profile information"
      400:
        description: Missing credentials or captcha verification failed
      401:
        description: Invalid username or password
      403:
        description: Account is disabled or pending activation
      429:
        description: Too many login attempts, temporarily blocked
      500:
        description: Internal server error
    """
    ip_address = _get_client_ip()
    user_agent = _get_user_agent()
    try:
        from app.services.security_service import get_security_service
        from app.services.user_service import get_user_service
        security = get_security_service()
        user_service = get_user_service()
        data = request.get_json()
        if not data:
            return jsonify({'code': 400, 'msg': 'No data provided', 'data': None}), 400
        username = data.get('username') or data.get('account')
        password = data.get('password')
        turnstile_token = data.get('turnstile_token')
        if not username or not password:
            return jsonify({'code': 400, 'msg': 'Missing username/email or password', 'data': None}), 400
        turnstile_ok, turnstile_msg = security.verify_turnstile(turnstile_token, ip_address)
        if not turnstile_ok:
            return jsonify({'code': 0, 'msg': turnstile_msg, 'data': None}), 400
        allowed, block_msg = security.check_login_allowed(username, ip_address)
        if not allowed:
            return jsonify({'code': 0, 'msg': block_msg, 'data': {'blocked': True}}), 429
        user = None
        if not _is_single_user_mode():
            try:
                user = user_service.authenticate(username, password)
                if user and user.get('_no_password'):
                    user.pop('_no_password', None)
                    security.record_login_attempt(ip_address, 'ip', False, ip_address, user_agent)
                    security.record_login_attempt(username, 'account', False, ip_address, user_agent)
                    security.log_security_event('login_failed', user.get('id'), ip_address, user_agent, {'username': username, 'reason': 'no_password_set'})
                    return jsonify({'code': 0, 'msg': 'This account was created with email verification code and has no password set. Please use email code login or set a password first in your profile settings.', 'data': None}), 401
            except Exception as e:
                logger.warning(f"Multi-user auth failed, trying legacy: {e}")
        if not user:
            user = authenticate_legacy(username, password)
        if not user:
            security.record_login_attempt(ip_address, 'ip', False, ip_address, user_agent)
            security.record_login_attempt(username, 'account', False, ip_address, user_agent)
            security.log_security_event('login_failed', None, ip_address, user_agent, {'username': username, 'reason': 'invalid_credentials'})
            return jsonify({'code': 0, 'msg': 'Invalid credentials', 'data': None}), 401
        if user.get('status') == 'disabled':
            security.log_security_event('login_blocked', user.get('id'), ip_address, user_agent, {'reason': 'account_disabled'})
            return jsonify({'code': 0, 'msg': 'Account is disabled', 'data': None}), 403
        if user.get('status') == 'pending':
            return jsonify({'code': 0, 'msg': 'Account is pending activation', 'data': None}), 403
        try:
            new_token_version = user_service.increment_token_version(user.get('id') or user.get('user_id', 1))
        except Exception as e:
            logger.warning(f"Failed to increment token_version: {e}")
            new_token_version = 1
        token = generate_token(user_id=user.get('id') or user.get('user_id', 1), username=user.get('username', username), role=user.get('role', 'admin'), token_version=new_token_version)
        if not token:
            return jsonify({'code': 500, 'msg': 'Token generation error', 'data': None}), 500
        security.record_login_attempt(ip_address, 'ip', True, ip_address, user_agent)
        security.record_login_attempt(username, 'account', True, ip_address, user_agent)
        security.clear_login_attempts(ip_address, 'ip')
        security.clear_login_attempts(username, 'account')
        security.log_security_event('login_success', user.get('id'), ip_address, user_agent)
        userinfo = {
            'id': user.get('id') or user.get('user_id', 1),
            'username': user.get('username', username),
            'nickname': user.get('nickname', 'User'),
            'avatar': user.get('avatar', '/avatar2.jpg'),
            'timezone': str(user.get('timezone') or '').strip(),
            'role': {
                'id': user.get('role', 'admin'),
                'permissions': user_service.get_user_permissions(user.get('role', 'admin'))
            },
        }
        # ── RBAC: 附加角色和权限数据 ──
        try:
            from app.services.permission_service import get_permission_service
            ps = get_permission_service()
            uid = userinfo['id']
            rbac_roles = [r['role_code'] for r in ps.get_user_roles(uid)]
            rbac_codes = ps.get_user_permission_codes(uid)
            userinfo['roles'] = rbac_roles if rbac_roles else [user.get('role', 'user')]
            userinfo['permissions'] = rbac_codes
        except Exception as e:
            logger.warning(f"RBAC data fetch failed for login: {e}")
            userinfo['roles'] = [user.get('role', 'user')]
            userinfo['permissions'] = user_service.get_user_permissions(user.get('role', 'admin'))
        return jsonify({'code': 1, 'msg': 'Login successful', 'data': {'token': token, 'userinfo': userinfo}})
    except Exception as e:
        logger.error(f"Login error: {e}")
        return jsonify({'code': 500, 'msg': str(e), 'data': None}), 500


@auth_bp.route('/info', methods=['GET'])
@login_required
def info():
    """获取当前登录用户信息（含RBAC权限）"""
    try:
        from app.services.user_service import get_user_service
        user_service = get_user_service()
        user_id = get_current_user_id()
        user = user_service.get_user_by_id(user_id)
        if not user:
            return jsonify({'code': 0, 'msg': 'User not found', 'data': None}), 404

        userinfo = {
            'id': user.get('id'),
            'username': user.get('username'),
            'nickname': user.get('nickname', 'User'),
            'avatar': user.get('avatar', '/avatar2.jpg'),
            'timezone': str(user.get('timezone') or '').strip(),
            'role': {
                'id': user.get('role', 'user'),
                'permissions': user_service.get_user_permissions(user.get('role', 'user'))
            },
        }
        # RBAC 数据
        try:
            from app.services.permission_service import get_permission_service
            ps = get_permission_service()
            rbac_roles = [r['role_code'] for r in ps.get_user_roles(user_id)]
            rbac_codes = ps.get_user_permission_codes(user_id)
            userinfo['roles'] = rbac_roles if rbac_roles else [user.get('role', 'user')]
            userinfo['permissions'] = rbac_codes
        except Exception as e:
            logger.warning(f"RBAC data fetch failed for info: {e}")
            userinfo['roles'] = [user.get('role', 'user')]
            userinfo['permissions'] = user_service.get_user_permissions(user.get('role', 'user'))

        return jsonify({'code': 1, 'msg': 'success', 'data': userinfo})
    except Exception as e:
        logger.error(f"info failed: {e}")
        return jsonify({'code': 500, 'msg': str(e), 'data': None}), 500
