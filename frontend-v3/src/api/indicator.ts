import request from '@/utils/request'

const api = {
  getIndicators: '/api/indicator/getIndicators',
  saveIndicator: '/api/indicator/saveIndicator',
  deleteIndicator: '/api/indicator/deleteIndicator',
  verifyCode: '/api/indicator/verifyCode',
  aiGenerate: '/api/indicator/aiGenerate',
  backtest: '/api/indicator/backtest',
  backtestHistory: '/api/indicator/backtest/history',
  backtestGet: '/api/indicator/backtest/get',
  kline: '/api/indicator/kline',
  // Community endpoints
  communityIndicators: '/api/community/indicators',
  myPurchases: '/api/community/my-purchases',
  indicatorDetail: (id: number | string) => `/api/community/indicators/${id}`,
  indicatorPerformance: (id: number | string) => `/api/community/indicators/${id}/performance`,
  indicatorComments: (id: number | string) => `/api/community/indicators/${id}/comments`,
  myComment: (id: number | string) => `/api/community/indicators/${id}/my-comment`,
  purchase: (id: number | string) => `/api/community/indicators/${id}/purchase`,
  sync: (id: number | string) => `/api/community/indicators/${id}/sync`,
  // Admin endpoints
  adminReviewStats: '/api/community/admin/review-stats',
  adminPendingIndicators: '/api/community/admin/pending-indicators',
  adminReview: (id: number | string) => `/api/community/admin/indicators/${id}/review`,
  adminUnpublish: (id: number | string) => `/api/community/admin/indicators/${id}/unpublish`,
  adminDelete: (id: number | string) => `/api/community/admin/indicators/${id}`,
}

export function getIndicators(params: { userid?: number } = {}) {
  return request.get<unknown>(api.getIndicators, { params })
}

export function saveIndicator(data: { id?: number; code: string; userid?: number; name?: string; description?: string }) {
  return request.post<unknown>(api.saveIndicator, data)
}

export function deleteIndicator(data: { id: number }) {
  return request.post<unknown>(api.deleteIndicator, data) // using post as in old code
}

export function verifyCode(data: { code: string }) {
  return request.post<unknown>(api.verifyCode, data)
}

export function aiGenerate(data: { prompt: string; existingCode?: string }) {
  // Use fetch or streaming if needed for SSE, but regular request for non-stream fallback
  return request.post<unknown>(api.aiGenerate, data)
}

export function getKline(params: { symbol: string; timeframe: string; limit?: number }) {
  return request.get<unknown>(api.kline, { params })
}

export function runBacktest(data: any) {
  return request.post<unknown>(api.backtest, data)
}

export function getBacktestHistory(params: any = {}) {
  return request.get<unknown>(api.backtestHistory, { params })
}

export function getBacktestResult(runId: string) {
  return request.get<unknown>(api.backtestGet, { params: { runId } })
}

// Community Methods
export function getCommunityIndicators(params: any) {
  return request.get<any>(api.communityIndicators, { params })
}

export function getMyPurchases(params: any = { page: 1, page_size: 50 }) {
  return request.get<any>(api.myPurchases, { params })
}

export function getIndicatorCommunityDetail(id: number | string) {
  return request.get<any>(api.indicatorDetail(id))
}

export function getIndicatorPerformance(id: number | string) {
  return request.get<any>(api.indicatorPerformance(id))
}

export function getIndicatorComments(id: number | string, params: any) {
  return request.get<any>(api.indicatorComments(id), { params })
}

export function getMyIndicatorComment(id: number | string) {
  return request.get<any>(api.myComment(id))
}

export function purchaseIndicator(id: number | string) {
  return request.post<any>(api.purchase(id))
}

export function syncIndicatorCode(id: number | string) {
  return request.post<any>(api.sync(id))
}

export function addIndicatorComment(id: number | string, data: any) {
  return request.post<any>(api.indicatorComments(id), data)
}

export function updateIndicatorComment(indicatorId: number | string, commentId: number | string, data: any) {
  return request.put<any>(`${api.indicatorComments(indicatorId)}/${commentId}`, data)
}

// Admin Methods
export function getAdminReviewStats() {
  return request.get<any>(api.adminReviewStats)
}

export function getAdminPendingIndicators(params: any) {
  return request.get<any>(api.adminPendingIndicators, { params })
}

export function reviewIndicator(id: number | string, data: { action: string; note: string }) {
  return request.post<any>(api.adminReview(id), data)
}

export function unpublishIndicator(id: number | string, data: { note: string }) {
  return request.post<any>(api.adminUnpublish(id), data)
}

export function adminDeleteIndicator(id: number | string) {
  return request.delete<any>(api.adminDelete(id))
}
