"""
权限管理 API 路由
提供权限 CRUD、角色 CRUD、用户-角色分配、角色-权限分配的接口
"""
from flask import Blueprint, jsonify, request, g

from app.utils.auth import login_required, admin_required, get_current_user_id
from app.utils.logger import get_logger
from app.services.permission_service import get_permission_service

logger = get_logger(__name__)
permission_bp = Blueprint("permission", __name__)

_svc = get_permission_service


# ──────────────────────────────────────────────
#  Permission CRUD
# ──────────────────────────────────────────────

@permission_bp.route("/tree", methods=["GET"])
@login_required
def permission_tree():
    """获取完整权限树"""
    try:
        include_buttons = request.args.get("buttons", "1") == "1"
        result = _svc().get_permission_tree(include_buttons=include_buttons)
        return jsonify({"code": 1, "msg": "success", "data": result})
    except Exception as e:
        logger.error(f"permission_tree failed: {e}")
        return jsonify({"code": 0, "msg": str(e)}), 500


@permission_bp.route("/<int:perm_id>", methods=["GET"])
@login_required
def get_permission(perm_id: int):
    """获取单个权限"""
    try:
        result = _svc().get_permission(perm_id)
        if not result:
            return jsonify({"code": 0, "msg": "权限不存在"}), 404
        return jsonify({"code": 1, "msg": "success", "data": result})
    except Exception as e:
        logger.error(f"get_permission failed: {e}")
        return jsonify({"code": 0, "msg": str(e)}), 500


@permission_bp.route("", methods=["POST"])
@login_required
@admin_required
def create_permission():
    """创建权限（admin only）"""
    try:
        data = request.get_json() or {}
        required = ["name", "permission_code"]
        for field in required:
            if field not in data or not data[field]:
                return jsonify({"code": 0, "msg": f"缺少必填字段: {field}"}), 400
        result = _svc().create_permission(data)
        return jsonify({"code": 1, "msg": "success", "data": result})
    except Exception as e:
        logger.error(f"create_permission failed: {e}")
        return jsonify({"code": 0, "msg": str(e)}), 500


@permission_bp.route("/<int:perm_id>", methods=["PUT"])
@login_required
@admin_required
def update_permission(perm_id: int):
    """更新权限（admin only）"""
    try:
        data = request.get_json() or {}
        result = _svc().update_permission(perm_id, data)
        if not result:
            return jsonify({"code": 0, "msg": "权限不存在"}), 404
        return jsonify({"code": 1, "msg": "success", "data": result})
    except Exception as e:
        logger.error(f"update_permission failed: {e}")
        return jsonify({"code": 0, "msg": str(e)}), 500


@permission_bp.route("/<int:perm_id>", methods=["DELETE"])
@login_required
@admin_required
def delete_permission(perm_id: int):
    """删除权限（admin only）"""
    try:
        success = _svc().delete_permission(perm_id)
        if not success:
            return jsonify({"code": 0, "msg": "权限不存在"}), 404
        return jsonify({"code": 1, "msg": "删除成功"})
    except Exception as e:
        logger.error(f"delete_permission failed: {e}")
        return jsonify({"code": 0, "msg": str(e)}), 500


# ──────────────────────────────────────────────
#  Role CRUD
# ──────────────────────────────────────────────

@permission_bp.route("/roles", methods=["GET"])
@login_required
def list_roles():
    """列出角色（分页）"""
    try:
        page = request.args.get("page", 1, type=int)
        page_size = request.args.get("page_size", 20, type=int)
        result = _svc().list_roles(page=page, page_size=page_size)
        return jsonify({"code": 1, "msg": "success", "data": result})
    except Exception as e:
        logger.error(f"list_roles failed: {e}")
        return jsonify({"code": 0, "msg": str(e)}), 500


@permission_bp.route("/roles/all", methods=["GET"])
@login_required
def all_roles():
    """获取所有角色（不分页，供下拉）"""
    try:
        result = _svc().get_all_roles()
        return jsonify({"code": 1, "msg": "success", "data": result})
    except Exception as e:
        logger.error(f"all_roles failed: {e}")
        return jsonify({"code": 0, "msg": str(e)}), 500


@permission_bp.route("/roles/<int:role_id>", methods=["GET"])
@login_required
def get_role(role_id: int):
    """获取单个角色（含权限ID列表）"""
    try:
        result = _svc().get_role(role_id)
        if not result:
            return jsonify({"code": 0, "msg": "角色不存在"}), 404
        return jsonify({"code": 1, "msg": "success", "data": result})
    except Exception as e:
        logger.error(f"get_role failed: {e}")
        return jsonify({"code": 0, "msg": str(e)}), 500


@permission_bp.route("/roles", methods=["POST"])
@login_required
@admin_required
def create_role():
    """创建角色（admin only）"""
    try:
        data = request.get_json() or {}
        required = ["name", "role_code"]
        for field in required:
            if field not in data or not data[field]:
                return jsonify({"code": 0, "msg": f"缺少必填字段: {field}"}), 400
        result = _svc().create_role(data)
        return jsonify({"code": 1, "msg": "success", "data": result})
    except Exception as e:
        logger.error(f"create_role failed: {e}")
        return jsonify({"code": 0, "msg": str(e)}), 500


@permission_bp.route("/roles/<int:role_id>", methods=["PUT"])
@login_required
@admin_required
def update_role(role_id: int):
    """更新角色（admin only）"""
    try:
        data = request.get_json() or {}
        result = _svc().update_role(role_id, data)
        if not result:
            return jsonify({"code": 0, "msg": "角色不存在"}), 404
        return jsonify({"code": 1, "msg": "success", "data": result})
    except Exception as e:
        logger.error(f"update_role failed: {e}")
        return jsonify({"code": 0, "msg": str(e)}), 500


@permission_bp.route("/roles/<int:role_id>", methods=["DELETE"])
@login_required
@admin_required
def delete_role(role_id: int):
    """删除角色（admin only）"""
    try:
        success = _svc().delete_role(role_id)
        if not success:
            return jsonify({"code": 0, "msg": "角色不存在"}), 404
        return jsonify({"code": 1, "msg": "删除成功"})
    except Exception as e:
        logger.error(f"delete_role failed: {e}")
        return jsonify({"code": 0, "msg": str(e)}), 500


# ──────────────────────────────────────────────
#  Role-Permission assignment
# ──────────────────────────────────────────────

@permission_bp.route("/roles/<int:role_id>/permissions", methods=["PUT"])
@login_required
@admin_required
def assign_permissions(role_id: int):
    """为角色分配权限（admin only）"""
    try:
        data = request.get_json() or {}
        permission_ids = data.get("permission_ids", [])
        if not isinstance(permission_ids, list):
            return jsonify({"code": 0, "msg": "permission_ids 必须是数组"}), 400
        success = _svc().assign_permissions_to_role(role_id, permission_ids)
        if not success:
            return jsonify({"code": 0, "msg": "角色不存在"}), 404
        return jsonify({"code": 1, "msg": "权限分配成功"})
    except Exception as e:
        logger.error(f"assign_permissions failed: {e}")
        return jsonify({"code": 0, "msg": str(e)}), 500


# ──────────────────────────────────────────────
#  User-Role assignment
# ──────────────────────────────────────────────

@permission_bp.route("/users/<int:user_id>/roles", methods=["GET"])
@login_required
@admin_required
def get_user_roles(user_id: int):
    """获取用户的角色列表（admin only）"""
    try:
        result = _svc().get_user_roles(user_id)
        return jsonify({"code": 1, "msg": "success", "data": result})
    except Exception as e:
        logger.error(f"get_user_roles failed: {e}")
        return jsonify({"code": 0, "msg": str(e)}), 500


@permission_bp.route("/users/<int:user_id>/roles", methods=["PUT"])
@login_required
@admin_required
def assign_user_roles(user_id: int):
    """为用户分配角色（admin only）"""
    try:
        data = request.get_json() or {}
        role_ids = data.get("role_ids", [])
        if not isinstance(role_ids, list):
            return jsonify({"code": 0, "msg": "role_ids 必须是数组"}), 400
        success = _svc().assign_roles_to_user(user_id, role_ids)
        if not success:
            return jsonify({"code": 0, "msg": "用户不存在"}), 404
        return jsonify({"code": 1, "msg": "角色分配成功"})
    except Exception as e:
        logger.error(f"assign_user_roles failed: {e}")
        return jsonify({"code": 0, "msg": str(e)}), 500


# ──────────────────────────────────────────────
#  Current user info (for frontend menu)
# ──────────────────────────────────────────────

@permission_bp.route("/my/menu", methods=["GET"])
@login_required
def my_menu():
    """获取当前用户的菜单权限树"""
    try:
        user_id = get_current_user_id()
        result = _svc().get_user_menu_permissions(user_id)
        return jsonify({"code": 1, "msg": "success", "data": result})
    except Exception as e:
        logger.error(f"my_menu failed: {e}")
        return jsonify({"code": 0, "msg": str(e)}), 500


@permission_bp.route("/my/codes", methods=["GET"])
@login_required
def my_permission_codes():
    """获取当前用户的权限编码列表"""
    try:
        user_id = get_current_user_id()
        result = _svc().get_user_permission_codes(user_id)
        return jsonify({"code": 1, "msg": "success", "data": result})
    except Exception as e:
        logger.error(f"my_permission_codes failed: {e}")
        return jsonify({"code": 0, "msg": str(e)}), 500
