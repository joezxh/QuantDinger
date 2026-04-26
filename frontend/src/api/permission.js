/**
 * RBAC Permission & Role Management API
 */
import request from '@/utils/request'

const BASE = '/api/permission'

// ==================== Permission CRUD ====================

export function getPermissionTree (includeButtons = true) {
  return request({
    url: `${BASE}/tree`,
    method: 'get',
    params: { buttons: includeButtons ? '1' : '0' }
  })
}

export function getPermission (id) {
  return request({
    url: `${BASE}/${id}`,
    method: 'get'
  })
}

export function createPermission (data) {
  return request({
    url: BASE,
    method: 'post',
    data
  })
}

export function updatePermission (id, data) {
  return request({
    url: `${BASE}/${id}`,
    method: 'put',
    data
  })
}

export function deletePermission (id) {
  return request({
    url: `${BASE}/${id}`,
    method: 'delete'
  })
}

// ==================== Role CRUD ====================

export function getRoleList (params) {
  return request({
    url: `${BASE}/roles`,
    method: 'get',
    params
  })
}

export function getAllRoles () {
  return request({
    url: `${BASE}/roles/all`,
    method: 'get'
  })
}

export function getRole (id) {
  return request({
    url: `${BASE}/roles/${id}`,
    method: 'get'
  })
}

export function createRole (data) {
  return request({
    url: `${BASE}/roles`,
    method: 'post',
    data
  })
}

export function updateRole (id, data) {
  return request({
    url: `${BASE}/roles/${id}`,
    method: 'put',
    data
  })
}

export function deleteRole (id) {
  return request({
    url: `${BASE}/roles/${id}`,
    method: 'delete'
  })
}

// ==================== Role-Permission Assignment ====================

export function assignPermissionsToRole (roleId, permissionIds) {
  return request({
    url: `${BASE}/roles/${roleId}/permissions`,
    method: 'put',
    data: { permission_ids: permissionIds }
  })
}

// ==================== User-Role Assignment ====================

export function getUserRoles (userId) {
  return request({
    url: `${BASE}/users/${userId}/roles`,
    method: 'get'
  })
}

export function assignRolesToUser (userId, roleIds) {
  return request({
    url: `${BASE}/users/${userId}/roles`,
    method: 'put',
    data: { role_ids: roleIds }
  })
}

// ==================== Current User ====================

export function getMyMenu () {
  return request({
    url: `${BASE}/my/menu`,
    method: 'get'
  })
}

export function getMyPermissionCodes () {
  return request({
    url: `${BASE}/my/codes`,
    method: 'get'
  })
}
