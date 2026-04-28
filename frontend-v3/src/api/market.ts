import request from '@/utils/request'

export function getWatchlist(parameter: Record<string, any>) {
  return request.get<any>('/api/market/watchlist/get', { params: parameter })
}

export function addWatchlist(parameter: Record<string, any>) {
  return request.post<any>('/api/market/watchlist/add', parameter)
}

export function removeWatchlist(parameter: Record<string, any>) {
  return request.post<any>('/api/market/watchlist/remove', parameter)
}

export function getWatchlistPrices(parameter: { watchlist: Array<{ market: string; symbol: string }> }) {
  return request.get<any>('/api/market/watchlist/prices', {
    params: { watchlist: JSON.stringify(parameter.watchlist || []) },
  })
}

export function chatMessage(parameter: Record<string, any>) {
  return request.post<any>('/api/ai/chat/message', parameter)
}

export function getChatHistory(parameter: Record<string, any>) {
  return request.get<any>('/api/ai/chat/history', { params: parameter })
}

export function saveChatHistory(parameter: Record<string, any>) {
  return request.post<any>('/api/ai/chat/history/save', parameter)
}

export function multiAnalysis(parameter: Record<string, any>) {
  return request.post<any>('/api/analysis/multiAnalysis', parameter, {
    timeout: 300000,
  })
}

export function createAnalysisTask(parameter: Record<string, any>) {
  return request.post<any>('/api/analysis/createTask', parameter)
}

export function getAnalysisTaskStatus(parameter: { task_id: number }) {
  return request.get<any>('/api/analysis/getTaskStatus', { params: parameter })
}

export function getAnalysisHistoryList(parameter: Record<string, any>) {
  return request.get<any>('/api/analysis/getHistoryList', { params: parameter })
}

export function deleteAnalysisTask(parameter: { task_id: number }) {
  return request.post<any>('/api/analysis/deleteTask', parameter)
}

export function reflectAnalysis(parameter: Record<string, any>) {
  return request.post<any>('/api/analysis/reflect', parameter)
}

export function getConfig() {
  return request.get<any>('/api/market/config')
}

export function getMenuFooterConfig() {
  return request.get<any>('/api/market/menuFooterConfig')
}

export function getMarketTypes() {
  return request.get<any>('/api/market/types')
}

export function searchSymbols(parameter: { market: string; keyword: string; limit?: number }) {
  return request.get<any>('/api/market/symbols/search', { params: parameter })
}

export function getHotSymbols(parameter: { market: string; limit?: number }) {
  return request.get<any>('/api/market/symbols/hot', { params: parameter })
}
