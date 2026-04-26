"""
Permission Service — RBAC management

Handles Permission CRUD, Role CRUD, user-role assignments, and role-permission assignments.
"""
from typing import Any, Dict, List, Optional

from app.database.session import get_session
from app.models.permission import Permission, Role, RolePermission, UserRole
from app.models.user import User
from app.utils.logger import get_logger

logger = get_logger(__name__)


class PermissionService:
    """权限管理服务"""

    # ──────────────────────────────────────────────
    #  Permission helpers
    # ──────────────────────────────────────────────

    def _perm_to_dict(self, p: Permission, _depth: int = 0) -> Dict[str, Any]:
        """将 Permission 对象转为字典，递归包含子节点"""
        result: Dict[str, Any] = {
            "id": p.id,
            "name": p.name,
            "permission_code": p.permission_code,
            "type": p.type,
            "parent_id": p.parent_id,
            "path": p.path,
            "component": p.component,
            "icon": p.icon,
            "sort_order": p.sort_order,
            "visible": p.visible,
            "status": p.status,
            "created_at": str(p.created_at) if p.created_at else None,
            "updated_at": str(p.updated_at) if p.updated_at else None,
        }
        # Only nest one level deep to avoid infinite loops in javascipt
        if _depth < 2 and p.children:
            result["children"] = [
                self._perm_to_dict(c, _depth + 1) for c in p.children
            ]
        else:
            result["children"] = []
        return result

    def _role_to_dict(self, r: Role) -> Dict[str, Any]:
        """将 Role 对象转为字典"""
        return {
            "id": r.id,
            "name": r.name,
            "role_code": r.role_code,
            "description": r.description,
            "status": r.status,
            "created_at": str(r.created_at) if r.created_at else None,
            "updated_at": str(r.updated_at) if r.updated_at else None,
        }

    # ──────────────────────────────────────────────
    #  Permission CRUD
    # ──────────────────────────────────────────────

    def get_permission_tree(self, include_buttons: bool = True) -> List[Dict[str, Any]]:
        """获取完整权限树（仅 dir + menu 的顶层 + 所有子节点）"""
        with get_session() as session:
            q = session.query(Permission).filter(Permission.parent_id.is_(None))
            if not include_buttons:
                q = q.filter(Permission.type.in_(["dir", "menu"]))
            q = q.order_by(Permission.sort_order, Permission.id)
            roots = q.all()
            return [self._perm_to_dict(r) for r in roots]

    def get_permission(self, perm_id: int) -> Optional[Dict[str, Any]]:
        """获取单个权限"""
        with get_session() as session:
            p = session.query(Permission).get(perm_id)
            return self._perm_to_dict(p) if p else None

    def create_permission(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建权限"""
        with get_session() as session:
            perm = Permission(
                name=data["name"],
                permission_code=data["permission_code"],
                type=data.get("type", "menu"),
                parent_id=data.get("parent_id"),
                path=data.get("path"),
                component=data.get("component"),
                icon=data.get("icon", ""),
                sort_order=data.get("sort_order", 0),
                visible=data.get("visible", True),
                status=data.get("status", "active"),
            )
            session.add(perm)
            session.flush()
            session.refresh(perm)
            return self._perm_to_dict(perm)

    def update_permission(self, perm_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新权限"""
        with get_session() as session:
            perm = session.query(Permission).get(perm_id)
            if not perm:
                return None
            updatable = [
                "name", "permission_code", "type", "parent_id",
                "path", "component", "icon", "sort_order", "visible", "status",
            ]
            for field in updatable:
                if field in data:
                    setattr(perm, field, data[field])
            session.flush()
            session.refresh(perm)
            return self._perm_to_dict(perm)

    def delete_permission(self, perm_id: int) -> bool:
        """删除权限（级联删除子权限）"""
        with get_session() as session:
            perm = session.query(Permission).get(perm_id)
            if not perm:
                return False
            session.delete(perm)
            return True

    # ──────────────────────────────────────────────
    #  Role CRUD
    # ──────────────────────────────────────────────

    def list_roles(self, page: int = 1, page_size: int = 20) -> Dict[str, Any]:
        """列出角色"""
        with get_session() as session:
            q = session.query(Role).order_by(Role.id)
            total = q.count()
            items = q.offset((page - 1) * page_size).limit(page_size).all()
            return {
                "items": [self._role_to_dict(r) for r in items],
                "total": total,
                "page": page,
                "page_size": page_size,
            }

    def get_all_roles(self) -> List[Dict[str, Any]]:
        """获取所有角色（不分页，供下拉选择）"""
        with get_session() as session:
            roles = session.query(Role).filter(Role.status == "active").order_by(Role.id).all()
            return [
                {"id": r.id, "name": r.name, "role_code": r.role_code}
                for r in roles
            ]

    def get_role(self, role_id: int) -> Optional[Dict[str, Any]]:
        """获取单个角色（含权限列表）"""
        with get_session() as session:
            r = session.query(Role).get(role_id)
            if not r:
                return None
            result = self._role_to_dict(r)
            result["permission_ids"] = [p.id for p in r.permissions]
            return result

    def create_role(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """创建角色"""
        with get_session() as session:
            role = Role(
                name=data["name"],
                role_code=data["role_code"],
                description=data.get("description", ""),
                status=data.get("status", "active"),
            )
            session.add(role)
            session.flush()
            session.refresh(role)
            return self._role_to_dict(role)

    def update_role(self, role_id: int, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """更新角色"""
        with get_session() as session:
            role = session.query(Role).get(role_id)
            if not role:
                return None
            updatable = ["name", "role_code", "description", "status"]
            for field in updatable:
                if field in data:
                    setattr(role, field, data[field])
            session.flush()
            session.refresh(role)
            return self._role_to_dict(role)

    def delete_role(self, role_id: int) -> bool:
        """删除角色"""
        with get_session() as session:
            role = session.query(Role).get(role_id)
            if not role:
                return False
            session.delete(role)
            return True

    # ──────────────────────────────────────────────
    #  Role-Permission assignment
    # ──────────────────────────────────────────────

    def assign_permissions_to_role(self, role_id: int, permission_ids: List[int]) -> bool:
        """为角色分配权限（先清空再分配）"""
        with get_session() as session:
            role = session.query(Role).get(role_id)
            if not role:
                return False
            # Clear existing
            session.query(RolePermission).filter(
                RolePermission.role_id == role_id
            ).delete()
            # Insert new
            for pid in permission_ids:
                link = RolePermission(role_id=role_id, permission_id=pid)
                session.add(link)
            return True

    def get_role_permission_ids(self, role_id: int) -> List[int]:
        """获取角色的权限ID列表"""
        with get_session() as session:
            links = (
                session.query(RolePermission.permission_id)
                .filter(RolePermission.role_id == role_id)
                .all()
            )
            return [r[0] for r in links]

    # ──────────────────────────────────────────────
    #  User-Role assignment
    # ──────────────────────────────────────────────

    def get_user_roles(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户的角色列表"""
        with get_session() as session:
            user = session.query(User).get(user_id)
            if not user:
                return []
            return [self._role_to_dict(r) for r in user.roles]

    def assign_roles_to_user(self, user_id: int, role_ids: List[int]) -> bool:
        """为用户分配角色（先清空再分配）"""
        with get_session() as session:
            user = session.query(User).get(user_id)
            if not user:
                return False
            # Clear existing
            session.query(UserRole).filter(
                UserRole.user_id == user_id
            ).delete()
            # Insert new
            for rid in role_ids:
                link = UserRole(user_id=user_id, role_id=rid)
                session.add(link)
            return True

    # ──────────────────────────────────────────────
    #  Auth check helpers
    # ──────────────────────────────────────────────

    def get_user_permission_codes(self, user_id: int) -> List[str]:
        """获取用户所有权限编码（扁平列表，用于鉴权）"""
        with get_session() as session:
            user = session.query(User).get(user_id)
            if not user:
                return []
            codes: List[str] = []
            for role in user.roles:
                for perm in role.permissions:
                    codes.append(perm.permission_code)
            return list(set(codes))  # de-duplicate

    def get_user_menu_permissions(self, user_id: int) -> List[Dict[str, Any]]:
        """获取用户有权限的菜单（仅 dir + menu 类型，树形结构，供前端动态菜单使用）"""
        with get_session() as session:
            user = session.query(User).get(user_id)
            if not user:
                return []

            # Collect all granted permission ids
            granted_ids: set[int] = set()
            for role in user.roles:
                for perm in role.permissions:
                    granted_ids.add(perm.id)

            # Get top-level dir/menu that the user has
            roots = (
                session.query(Permission)
                .filter(
                    Permission.parent_id.is_(None),
                    Permission.type.in_(["dir", "menu"]),
                    Permission.status == "active",
                )
                .order_by(Permission.sort_order, Permission.id)
                .all()
            )

            def filter_tree(node: Permission) -> Optional[Dict[str, Any]]:
                if node.id not in granted_ids:
                    return None
                d = self._perm_to_dict(node)
                # For dir nodes, filter children
                if node.type == "dir":
                    filtered_children = []
                    for child in node.children:
                        c = filter_tree(child)
                        if c:
                            filtered_children.append(c)
                    d["children"] = filtered_children
                    # Hide dir if no children visible
                    if not filtered_children:
                        return None
                else:
                    d["children"] = []
                # Frontend needs meta info for route rendering
                d["meta"] = {
                    "title": d["name"],
                    "icon": d["icon"],
                    "permission": [d["permission_code"]],
                }
                return d

            result: List[Dict[str, Any]] = []
            for root in roots:
                node = filter_tree(root)
                if node:
                    result.append(node)
            return result

    def has_permission(self, user_id: int, permission_code: str) -> bool:
        """检查用户是否拥有指定权限"""
        codes = self.get_user_permission_codes(user_id)
        return permission_code in codes


# Singleton helper — matches existing service patterns
_permission_service: Optional[PermissionService] = None


def get_permission_service() -> PermissionService:
    global _permission_service
    if _permission_service is None:
        _permission_service = PermissionService()
    return _permission_service
