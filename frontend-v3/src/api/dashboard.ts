/**
 * Dashboard API
 */
import request from '@/utils/request'

export function getDashboardSummary() {
  return request.get<any>('/api/dashboard/summary')
}

export function getPendingOrders(params: Record<string, any>) {
  return request.get<any>('/api/dashboard/pendingOrders', { params })
}

export function deletePendingOrder(id: number) {
  return request.delete<any>(`/api/dashboard/pendingOrders/${id}`)
}
