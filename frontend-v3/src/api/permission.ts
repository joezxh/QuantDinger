import request from '@/utils/request'

const BASE = '/api/permission'

export function getPermissionTree(includeButtons = true) {
  return request.get<any>(`${BASE}/tree`, {
    params: { buttons: includeButtons ? '1' : '0' },
  })
}

export function getPermission(id: number) {
  return request.get<any>(`${BASE}/${id}`)
}

export function createPermission(data: Record<string, any>) {
  return request.post<any>(BASE, data)
}

export function updatePermission(id: number, data: Record<string, any>) {
  return request.put<any>(`${BASE}/${id}`, data)
}

export function deletePermission(id: number) {
  return request.delete<any>(`${BASE}/${id}`)
}

export function getRoleList(params: Record<string, any>) {
  return request.get<any>(`${BASE}/roles`, { params })
}

export function getAllRoles() {
  return request.get<any>(`${BASE}/roles/all`)
}

export function getRole(id: number) {
  return request.get<any>(`${BASE}/roles/${id}`)
}

export function createRole(data: Record<string, any>) {
  return request.post<any>(`${BASE}/roles`, data)
}

export function updateRole(id: number, data: Record<string, any>) {
  return request.put<any>(`${BASE}/roles/${id}`, data)
}

export function deleteRole(id: number) {
  return request.delete<any>(`${BASE}/roles/${id}`)
}

export function assignPermissionsToRole(roleId: number, permissionIds: number[]) {
  return request.put<any>(`${BASE}/roles/${roleId}/permissions`, {
    permission_ids: permissionIds,
  })
}

export function getUserRoles(userId: number) {
  return request.get<any>(`${BASE}/users/${userId}/roles`)
}

export function assignRolesToUser(userId: number, roleIds: number[]) {
  return request.put<any>(`${BASE}/users/${userId}/roles`, {
    role_ids: roleIds,
  })
}

export function getMyMenu() {
  return request.get<any>(`${BASE}/my/menu`)
}

export function getMyPermissionCodes() {
  return request.get<any>(`${BASE}/my/codes`)
}
