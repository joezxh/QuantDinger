import request from '@/utils/request'

export function getStrategies(params: Record<string, any> = {}) {
  return request.get<any>('/api/strategies', { params })
}

export function createStrategy(data: Record<string, any>) {
  return request.post<any>('/api/strategies', data)
}

export function updateStrategy(id: number, data: Record<string, any>) {
  return request.put<any>(`/api/strategies/${id}`, data)
}

export function deleteStrategy(id: number) {
  return request.delete<any>(`/api/strategies/${id}`)
}

export function getTrades(params: Record<string, any> = {}) {
  return request.get<any>('/api/trades', { params })
}

export function getPerformance(params: Record<string, any> = {}) {
  return request.get<any>('/api/performance', { params })
}
