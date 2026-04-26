"""User Management API Routes

Provides endpoints for user CRUD operations, role management, etc.
Only accessible by admin users.
"""
import csv
from io import StringIO
import re
from flask import Blueprint, request, jsonify, g, Response
from app.database.session import get_session
from app.models.user import User
from app.services.user_service import get_user_service
from app.utils.auth import login_required, admin_required
from app.utils.logger import get_logger

logger = get_logger(__name__)

_PROFILE_TIMEZONE_RE = re.compile(r'^[A-Za-z0-9_/+\-.]+$')

user_bp = Blueprint('user_manage', __name__)


@user_bp.route('/list', methods=['GET'])
@login_required
@admin_required
def list_users():
    """
    ---
    tags:
      - System/User Management
    summary: "List users with pagination and search"
    description: "Admin only. Returns paginated user list with optional search by username, email, or nickname."
    produces:
      - application/json
    security:
      - BearerAuth: []
    parameters:
      - name: page
        in: query
        type: integer
        required: false
        default: 1
        description: "Page number, starting from 1"
      - name: page_size
        in: query
        type: integer
        required: false
        default: 20
        description: "Number of items per page, max 100"
      - name: search
        in: query
        type: string
        required: false
        description: "Search keyword to filter by username, email, or nickname"
    responses:
      200:
        description: Successful response with paginated user list
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 1
            msg:
              type: string
              example: success
            data:
              type: object
              properties:
                items:
                  type: array
                  items:
                    type: object
                total:
                  type: integer
                page:
                  type: integer
                page_size:
                  type: integer
      401:
        description: Unauthorized - Invalid or missing token
      403:
        description: Forbidden - Admin access required
      500:
        description: Internal server error
    """
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        search = request.args.get('search', '', type=str)
        page_size = min(100, max(1, page_size))
        result = get_user_service().list_users(page=page, page_size=page_size, search=search)
        return jsonify({'code': 1, 'msg': 'success', 'data': result})
    except Exception as e:
        logger.error(f"list_users failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@user_bp.route('/export', methods=['GET'])
@login_required
@admin_required
def export_users():
    """
    ---
    tags:
      - System/User Management
    summary: "Export users as CSV"
    description: "Admin only. Exports user data as a CSV file with UTF-8 BOM encoding."
    produces:
      - text/csv
    security:
      - BearerAuth: []
    parameters:
      - name: search
        in: query
        type: string
        required: false
        description: "Search keyword filter"
    responses:
      200:
        description: CSV file download
        schema:
          type: file
      401:
        description: Unauthorized - Invalid or missing token
      403:
        description: Forbidden - Admin access required
      500:
        description: Internal server error
    """
    try:
        search = request.args.get('search', '', type=str)
        users = get_user_service().list_all_users_for_export(search=search)
        output = StringIO()
        output.write('\ufeff')
        writer = csv.writer(output)
        writer.writerow([
            'ID', 'Username', 'Email', 'Nickname', 'Role', 'Status',
            'Credits', 'VIP Expires At', 'Timezone', 'Register IP',
            'Last Login At', 'Created At', 'Updated At'
        ])
        for user in users:
            writer.writerow([
                user.get('id') or '', user.get('username') or '', user.get('email') or '',
                user.get('nickname') or '', user.get('role') or '', user.get('status') or '',
                user.get('credits') or 0, user.get('vip_expires_at') or '', user.get('timezone') or '',
                user.get('register_ip') or '', user.get('last_login_at') or '', user.get('created_at') or '',
                user.get('updated_at') or '',
            ])
        return Response(
            output.getvalue(),
            mimetype='text/csv; charset=utf-8',
            headers={'Content-Disposition': 'attachment; filename="quantdinger_users_export.csv"'},
        )
    except Exception as e:
        logger.error(f"export_users failed: {e}", exc_info=True)
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@user_bp.route('/detail', methods=['GET'])
@login_required
@admin_required
def get_user_detail():
    """
    ---
    tags:
      - System/User Management
    summary: "Get user detail by ID"
    description: "Admin only. Returns detailed information for a specific user."
    produces:
      - application/json
    security:
      - BearerAuth: []
    parameters:
      - name: id
        in: query
        type: integer
        required: true
        description: "User ID"
    responses:
      200:
        description: Success
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 1
            msg:
              type: string
              example: success
            data:
              type: object
      400:
        description: Missing user id
      401:
        description: Unauthorized
      403:
        description: Forbidden
      404:
        description: User not found
      500:
        description: Internal Server Error
    """
    try:
        user_id = request.args.get('id', type=int)
        if not user_id:
            return jsonify({'code': 0, 'msg': 'Missing user id', 'data': None}), 400
        user = get_user_service().get_user_by_id(user_id)
        if not user:
            return jsonify({'code': 0, 'msg': 'User not found', 'data': None}), 404
        return jsonify({'code': 1, 'msg': 'success', 'data': user})
    except Exception as e:
        logger.error(f"get_user_detail failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@user_bp.route('/create', methods=['POST'])
@login_required
@admin_required
def create_user():
    """
    ---
    tags:
      - System/User Management
    summary: "Create a new user"
    description: "Admin only. Creates a new user account with the provided details."
    produces:
      - application/json
    consumes:
      - application/json
    security:
      - BearerAuth: []
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
              description: "Username"
            password:
              type: string
              description: "Password"
            email:
              type: string
              description: "Email address"
            nickname:
              type: string
              description: "Display nickname"
            role:
              type: string
              description: "User role (admin/user)"
    responses:
      200:
        description: Success
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 1
            msg:
              type: string
              example: User created successfully
            data:
              type: object
              properties:
                id:
                  type: integer
      400:
        description: Bad Request - Validation error
      401:
        description: Unauthorized
      403:
        description: Forbidden
      500:
        description: Internal server error
    """
    try:
        data = request.get_json() or {}
        user_id = get_user_service().create_user(data)
        return jsonify({'code': 1, 'msg': 'User created successfully', 'data': {'id': user_id}})
    except ValueError as e:
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 400
    except Exception as e:
        logger.error(f"create_user failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@user_bp.route('/delete', methods=['DELETE'])
@login_required
@admin_required
def delete_user():
    """删除用户（管理员）"""
    try:
        user_id = request.args.get('id', type=int)
        if not user_id:
            return jsonify({'code': 0, 'msg': 'Missing user id', 'data': None}), 400
        # Prevent deleting self
        if hasattr(g, 'user_id') and g.user_id == user_id:
            return jsonify({'code': 0, 'msg': 'Cannot delete yourself', 'data': None}), 400
        success = get_user_service().delete_user(user_id)
        if success:
            return jsonify({'code': 1, 'msg': 'User deleted successfully', 'data': None})
        return jsonify({'code': 0, 'msg': 'Delete failed', 'data': None}), 400
    except Exception as e:
        logger.error(f"delete_user failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@user_bp.route('/reset-password', methods=['POST'])
@login_required
@admin_required
def reset_user_password():
    """重置用户密码（管理员）"""
    try:
        data = request.get_json() or {}
        user_id = data.get('user_id')
        new_password = data.get('new_password', '')
        if not user_id:
            return jsonify({'code': 0, 'msg': 'Missing user_id', 'data': None}), 400
        if len(new_password) < 6:
            return jsonify({'code': 0, 'msg': 'Password must be at least 6 characters', 'data': None}), 400
        success = get_user_service().reset_password(user_id, new_password)
        if success:
            return jsonify({'code': 1, 'msg': 'Password reset successfully', 'data': None})
        return jsonify({'code': 0, 'msg': 'Reset failed', 'data': None}), 400
    except ValueError as e:
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 400
    except Exception as e:
        logger.error(f"reset_user_password failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@user_bp.route('/update', methods=['PUT'])
@login_required
@admin_required
def update_user():
    """
    ---
    tags:
      - System/User Management
    summary: "Update user information"
    description: "Admin only. Updates attributes of an existing user."
    produces:
      - application/json
    consumes:
      - application/json
    security:
      - BearerAuth: []
    parameters:
      - name: id
        in: query
        type: integer
        required: true
        description: "User ID"
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            username:
              type: string
            email:
              type: string
            nickname:
              type: string
            role:
              type: string
            status:
              type: string
    responses:
      200:
        description: Success
        schema:
          type: object
          properties:
            code:
              type: integer
              example: 1
            msg:
              type: string
              example: User updated successfully
      400:
        description: Missing user id or update failed
      401:
        description: Unauthorized
      403:
        description: Forbidden
      500:
        description: Internal Server Error
    """
    try:
        user_id = request.args.get('id', type=int)
        if not user_id:
            return jsonify({'code': 0, 'msg': 'Missing user id', 'data': None}), 400
        data = request.get_json() or {}
        success = get_user_service().update_user(user_id, data)
        if success:
            return jsonify({'code': 1, 'msg': 'User updated successfully', 'data': None})
        return jsonify({'code': 0, 'msg': 'Update failed', 'data': None}), 400
    except Exception as e:
        logger.error(f"update_user failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@user_bp.route('/roles', methods=['GET'])
@login_required
def get_available_roles():
    """获取可用角色列表（供下拉选择）"""
    try:
        from app.services.permission_service import get_permission_service
        roles = get_permission_service().get_all_roles()
        return jsonify({'code': 1, 'msg': 'success', 'data': roles})
    except Exception as e:
        logger.error(f"get_available_roles failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@user_bp.route('/profile', methods=['GET'])
@login_required
def get_user_profile():
    """获取当前用户资料（含计费信息）"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'code': 401, 'msg': 'Authentication required'}), 401
        user = get_user_service().get_user_by_id(user_id)
        if not user:
            return jsonify({'code': 404, 'msg': 'User not found'}), 404
        # 不返回敏感信息
        user.pop('password_hash', None)
        user.pop('token_version', None)
        # 附加计费信息
        try:
            from app.services.billing_service import get_billing_service
            billing = get_billing_service().get_user_billing_info(user_id)
            user['billing'] = billing
        except Exception as be:
            logger.warning(f"get_user_profile billing fetch failed: {be}")
            user['billing'] = {'credits': 0, 'vip_expires_at': None, 'is_vip': False}
        return jsonify({'code': 1, 'msg': 'success', 'data': user})
    except Exception as e:
        logger.error(f"get_user_profile failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@user_bp.route('/profile/update', methods=['PUT'])
@login_required
def update_profile():
    """更新当前用户资料（自服务，限 nickname/avatar/timezone）"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'code': 401, 'msg': 'Authentication required'}), 401
        data = request.get_json() or {}
        allowed = {}
        for field in ['nickname', 'avatar', 'timezone']:
            if field in data:
                value = data[field]
                if field == 'timezone' and value:
                    if not _PROFILE_TIMEZONE_RE.match(str(value)):
                        return jsonify({'code': 0, 'msg': 'Invalid timezone format', 'data': None}), 400
                allowed[field] = value
        if not allowed:
            return jsonify({'code': 0, 'msg': 'No valid fields to update', 'data': None}), 400
        success = get_user_service().update_user(user_id, allowed)
        if success:
            return jsonify({'code': 1, 'msg': 'Profile updated successfully', 'data': None})
        return jsonify({'code': 0, 'msg': 'Update failed', 'data': None}), 400
    except ValueError as e:
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 400
    except Exception as e:
        logger.error(f"update_profile failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@user_bp.route('/notification-settings', methods=['GET'])
@login_required
def get_notification_settings():
    """获取当前用户通知设置"""
    try:
        import json
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'code': 401, 'msg': 'Authentication required'}), 401
        user = get_user_service().get_user_by_id(user_id)
        if not user:
            return jsonify({'code': 404, 'msg': 'User not found'}), 404
        settings_str = user.get('notification_settings') or ''
        settings = {}
        if settings_str:
            try:
                settings = json.loads(settings_str)
            except Exception:
                settings = {}
        if 'default_channels' not in settings:
            settings['default_channels'] = ['browser']
        if 'email' not in settings:
            settings['email'] = user.get('email') or ''
        return jsonify({'code': 1, 'msg': 'success', 'data': settings})
    except Exception as e:
        logger.error(f"get_notification_settings failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@user_bp.route('/notification-settings', methods=['PUT'])
@login_required
def update_notification_settings():
    """更新当前用户通知设置"""
    try:
        import json
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'code': 401, 'msg': 'Authentication required'}), 401
        data = request.get_json() or {}
        valid_channels = ['browser', 'email', 'telegram', 'discord', 'webhook', 'phone']
        default_channels = data.get('default_channels', [])
        if not isinstance(default_channels, list):
            default_channels = ['browser']
        default_channels = [c for c in default_channels if c in valid_channels]
        if not default_channels:
            default_channels = ['browser']
        settings = {
            'default_channels': default_channels,
            'telegram_bot_token': str(data.get('telegram_bot_token') or '').strip(),
            'telegram_chat_id': str(data.get('telegram_chat_id') or '').strip(),
            'email': str(data.get('email') or '').strip(),
            'discord_webhook': str(data.get('discord_webhook') or '').strip(),
            'webhook_url': str(data.get('webhook_url') or '').strip(),
            'phone': str(data.get('phone') or '').strip(),
        }
        # Remove empty values (keep default_channels)
        settings = {k: v for k, v in settings.items() if v or k == 'default_channels'}
        settings_json = json.dumps(settings, ensure_ascii=False)
        success = get_user_service().update_user(user_id, {'notification_settings': settings_json})
        if success:
            return jsonify({'code': 1, 'msg': 'Notification settings updated', 'data': settings})
        return jsonify({'code': 0, 'msg': 'Update failed', 'data': None}), 400
    except Exception as e:
        logger.error(f"update_notification_settings failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@user_bp.route('/notification-settings/test', methods=['POST'])
@login_required
def test_notification_settings():
    """发送测试通知到当前用户配置的通知渠道"""
    try:
        import json
        from app.services.signal_notifier import SignalNotifier
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'code': 401, 'msg': 'Authentication required'}), 401
        user = get_user_service().get_user_by_id(user_id)
        if not user:
            return jsonify({'code': 404, 'msg': 'User not found'}), 404
        settings_str = user.get('notification_settings') or ''
        settings = {}
        if settings_str:
            try:
                settings = json.loads(settings_str)
            except Exception:
                settings = {}
        channels = settings.get('default_channels') or ['browser']
        if not isinstance(channels, list) or not channels:
            channels = ['browser']
        notify_email = (settings.get('email') or '').strip() or user.get('email') or ''
        targets = {
            'telegram': (settings.get('telegram_chat_id') or '').strip(),
            'telegram_bot_token': (settings.get('telegram_bot_token') or '').strip(),
            'email': notify_email,
            'phone': (settings.get('phone') or '').strip(),
            'discord': (settings.get('discord_webhook') or '').strip(),
            'webhook': (settings.get('webhook_url') or '').strip(),
        }
        accept = (request.headers.get('Accept-Language') or '') + ' ' + (request.headers.get('X-Locale') or '')
        language = 'zh-CN' if 'zh' in accept.lower() else 'en-US'
        notifier = SignalNotifier()
        results = notifier.send_profile_test_notifications(
            user_id=int(user_id),
            channels=channels,
            targets=targets,
            language=language,
        )
        any_ok = any((v or {}).get('ok') for v in results.values())
        failed = [k for k, v in results.items() if not (v or {}).get('ok')]
        if failed:
            err_detail = {k: (results.get(k) or {}).get('error', '') for k in failed}
            logger.warning("notification_settings test: user_id=%s failed_channels=%s errors=%s", user_id, failed, err_detail)
        if not any_ok:
            detail = '; '.join(f"{k}: {(results[k] or {}).get('error', '')}" for k in failed) or 'all channels failed'
            return jsonify({'code': 0, 'msg': detail, 'data': {'results': results}})
        msg = 'Test notification sent'
        if failed:
            msg = f"Sent OK; failed: {', '.join(failed)}"
        return jsonify({'code': 1, 'msg': msg, 'data': {'results': results}})
    except Exception as e:
        logger.error(f"test_notification_settings failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@user_bp.route('/my-credits-log', methods=['GET'])
@login_required
def get_my_credits_log():
    """获取当前用户积分变动日志"""
    try:
        from app.services.billing_service import get_billing_service
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'code': 401, 'msg': 'Authentication required'}), 401
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        page_size = min(100, max(1, page_size))
        result = get_billing_service().get_credits_log(user_id, page, page_size)
        return jsonify({'code': 1, 'msg': 'success', 'data': result})
    except Exception as e:
        logger.error(f"get_my_credits_log failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@user_bp.route('/my-referrals', methods=['GET'])
@login_required
def get_my_referrals():
    """获取当前用户邀请的下线列表"""
    try:
        import os
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'code': 401, 'msg': 'Authentication required'}), 401
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        page_size = min(100, max(1, page_size))
        offset = (page - 1) * page_size
        with get_session() as session:
            from sqlalchemy import func
            total = session.query(func.count(User.id)).filter(User.referred_by == user_id).scalar() or 0
            items = session.query(User).filter(User.referred_by == user_id).order_by(
                User.created_at.desc()
            ).offset(offset).limit(page_size).all()
            referrals = []
            for row in items:
                referrals.append({
                    'id': row.id,
                    'username': row.username,
                    'nickname': row.nickname,
                    'avatar': row.avatar,
                    'created_at': row.created_at.isoformat() if row.created_at else None,
                })
        return jsonify({
            'code': 1,
            'msg': 'success',
            'data': {
                'list': referrals,
                'total': total,
                'page': page,
                'page_size': page_size,
                'referral_code': str(user_id),
                'referral_bonus': int(os.getenv('CREDITS_REFERRAL_BONUS', '0')),
                'register_bonus': int(os.getenv('CREDITS_REGISTER_BONUS', '0')),
            }
        })
    except Exception as e:
        logger.error(f"get_my_referrals failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@user_bp.route('/change-password', methods=['POST'])
@login_required
def change_password():
    """修改当前用户密码（需要旧密码）"""
    try:
        user_id = getattr(g, 'user_id', None)
        if not user_id:
            return jsonify({'code': 401, 'msg': 'Authentication required'}), 401
        data = request.get_json() or {}
        old_password = data.get('old_password', '')
        new_password = data.get('new_password', '')
        if not new_password:
            return jsonify({'code': 0, 'msg': 'New password required', 'data': None}), 400
        if len(new_password) < 6:
            return jsonify({'code': 0, 'msg': 'Password must be at least 6 characters', 'data': None}), 400
        user_service = get_user_service()
        user = user_service.get_user_by_id(user_id)
        if not user:
            return jsonify({'code': 404, 'msg': 'User not found', 'data': None}), 404
        password_hash = user.get('password_hash', '')
        has_password = password_hash and password_hash.strip() != ''
        if not has_password:
            # 无密码用户直接设置新密码
            success = user_service.reset_password(user_id, new_password)
            if success:
                return jsonify({'code': 1, 'msg': 'Password set successfully', 'data': None})
            return jsonify({'code': 0, 'msg': 'Failed to set password', 'data': None}), 500
        if not old_password:
            return jsonify({'code': 0, 'msg': 'Old password required', 'data': None}), 400
        success = user_service.change_password(user_id, old_password, new_password)
        if success:
            return jsonify({'code': 1, 'msg': 'Password changed successfully', 'data': None})
        return jsonify({'code': 0, 'msg': 'Old password incorrect', 'data': None}), 400
    except ValueError as e:
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 400
    except Exception as e:
        logger.error(f"change_password failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@user_bp.route('/system-strategies', methods=['GET'])
@login_required
@admin_required
def get_system_strategies():
    """获取系统策略列表（管理员视图）"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        status = request.args.get('status', '', type=str)
        execution_mode = request.args.get('execution_mode', '', type=str)
        search = request.args.get('search', '', type=str)
        # TODO: 实现真实的策略查询逻辑
        return jsonify({
            'code': 1,
            'msg': 'success',
            'data': {
                'items': [],
                'total': 0,
                'summary': {
                    'total': 0,
                    'active': 0,
                    'paused': 0,
                    'stopped': 0
                }
            }
        })
    except Exception as e:
        logger.error(f"get_system_strategies failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@user_bp.route('/admin-orders', methods=['GET'])
@login_required
@admin_required
def get_admin_orders():
    """获取所有订单列表（管理员视图）"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        status = request.args.get('status', '', type=str)
        search = request.args.get('search', '', type=str)
        # TODO: 实现真实的订单查询逻辑
        return jsonify({
            'code': 1,
            'msg': 'success',
            'data': {
                'items': [],
                'total': 0,
                'summary': {
                    'total': 0,
                    'pending': 0,
                    'completed': 0,
                    'cancelled': 0,
                    'total_volume': 0.0,
                    'total_value': 0.0
                }
            }
        })
    except Exception as e:
        logger.error(f"get_admin_orders failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500


@user_bp.route('/admin-ai-stats', methods=['GET'])
@login_required
@admin_required
def get_admin_ai_stats():
    """获取AI使用统计（管理员视图）"""
    try:
        page = request.args.get('page', 1, type=int)
        page_size = request.args.get('page_size', 20, type=int)
        search = request.args.get('search', '', type=str)
        # TODO: 实现真实的 AI 统计查询逻辑
        return jsonify({
            'code': 1,
            'msg': 'success',
            'data': {
                'user_stats': {
                    'items': [],
                    'total': 0
                },
                'recent_records': {
                    'items': [],
                    'total': 0
                },
                'summary': {
                    'total_users': 0,
                    'active_users': 0,
                    'total_queries': 0,
                    'total_tokens': 0,
                    'total_cost': 0.0
                }
            }
        })
    except Exception as e:
        logger.error(f"get_admin_ai_stats failed: {e}")
        return jsonify({'code': 0, 'msg': str(e), 'data': None}), 500
