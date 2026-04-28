import request from '@/utils/request'

export function placeQuickOrder(data: Record<string, unknown>) {
  return request.post<unknown>('/api/quick-trade/place-order', data)
}

export function getQuickTradeBalance(params: Record<string, unknown>) {
  return request.get<unknown>('/api/quick-trade/balance', { params })
}

export function getQuickTradePosition(params: Record<string, unknown>) {
  return request.get<unknown>('/api/quick-trade/position', { params })
}

export function getQuickTradeHistory(params: Record<string, unknown>) {
  return request.get<unknown>('/api/quick-trade/history', { params })
}

export function closeQuickTradePosition(data: Record<string, unknown>) {
  return request.post<unknown>('/api/quick-trade/close-position', data)
}
