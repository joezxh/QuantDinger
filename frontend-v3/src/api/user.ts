import request from '@/utils/request'

const BASE_URL = '/api/users'

export function getUserList(params: Record<string, any>) {
  return request.get<any>(`${BASE_URL}/list`, { params })
}

export function exportUsers(params: Record<string, any>) {
  return request.get(`${BASE_URL}/export`, {
    params,
    responseType: 'blob',
  })
}

export function createUser(data: Record<string, any>) {
  return request.post<any>(BASE_URL, data)
}

export function updateUser(id: number, data: Record<string, any>) {
  return request.put<any>(`${BASE_URL}/${id}`, data)
}

export function deleteUser(id: number) {
  return request.delete<any>(`${BASE_URL}/${id}`)
}

export function resetUserPassword(data: { user_id: number; new_password: string }) {
  return request.post<any>(`${BASE_URL}/reset-password`, data)
}

export function getRoles() {
  return request.get<any>(`${BASE_URL}/roles`)
}

export function setUserCredits(data: { user_id: number; credits: number; remark?: string }) {
  return request.post<any>(`${BASE_URL}/credits`, data)
}

export function setUserVip(data: {
  user_id: number
  vip_days?: number
  vip_expires_at?: string
  remark?: string
}) {
  return request.post<any>(`${BASE_URL}/vip`, data)
}

export function getSystemStrategies(params: Record<string, any>) {
  return request.get<any>('/api/system/strategies', { params })
}

export function getAdminOrders(params: Record<string, any>) {
  return request.get<any>('/api/admin/orders', { params })
}

export function getAdminAiStats(params: Record<string, any>) {
  return request.get<any>('/api/admin/ai-stats', { params })
}

export function getAllRoles() {
  return request.get<any>('/api/roles/all')
}

export function getUserRoles(userId: number) {
  return request.get<any>(`/api/users/${userId}/roles`)
}

export function assignRolesToUser(userId: number, roleIds: number[]) {
  return request.post<any>(`/api/users/${userId}/roles`, { role_ids: roleIds })
}
