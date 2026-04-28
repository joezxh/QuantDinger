import request from '@/utils/request'

export function getPositions(params: Record<string, any> = {}) {
  return request.get<any>('/api/portfolio/positions', { params })
}

export function createPosition(data: Record<string, any>) {
  return request.post<any>('/api/portfolio/positions', data)
}

export function addPosition(data: Record<string, any>) {
  return request.post<any>('/api/portfolio/positions', data)
}

export function updatePosition(id: number, data: Record<string, any>) {
  return request.put<any>(`/api/portfolio/positions/${id}`, data)
}

export function deletePosition(id: number) {
  return request.delete<any>(`/api/portfolio/positions/${id}`)
}

export function getPortfolioSummary(params: Record<string, any> = {}) {
  return request.get<any>('/api/portfolio/summary', { params })
}

export function getMonitors() {
  return request.get<any>('/api/portfolio/monitors')
}

export function addMonitor(data: Record<string, any>) {
  return request.post<any>('/api/portfolio/monitors', data)
}

export function createMonitor(data: Record<string, any>) {
  return request.post<any>('/api/portfolio/monitors', data)
}

export function toggleMonitor(id: number, active: boolean) {
  return request.post<any>(`/api/portfolio/monitors/${id}/toggle`, { is_active: active })
}

export function updateMonitor(id: number, data: Record<string, any>) {
  return request.put<any>(`/api/portfolio/monitors/${id}`, data)
}

export function deleteMonitor(id: number) {
  return request.delete<any>(`/api/portfolio/monitors/${id}`)
}

export function runMonitor(id: number, params: Record<string, any> = {}) {
  return request.post<any>(`/api/portfolio/monitors/${id}/run`, params)
}

export function getAlerts() {
  return request.get<any>('/api/portfolio/alerts')
}

export function addAlert(data: Record<string, any>) {
  return request.post<any>('/api/portfolio/alerts', data)
}

export function updateAlert(id: number, data: Record<string, any>) {
  return request.put<any>(`/api/portfolio/alerts/${id}`, data)
}

export function deleteAlert(id: number) {
  return request.delete<any>(`/api/portfolio/alerts/${id}`)
}

export function getGroups() {
  return request.get<any>('/api/portfolio/groups')
}

export function renameGroup(data: Record<string, any>) {
  return request.post<any>('/api/portfolio/groups/rename', data)
}

export function searchSymbols(data: Record<string, any>) {
  return request.post<any>('/api/market/symbols/search', data)
}

export function getMarketTypes() {
  return request.get<any>('/api/market/types')
}
