import request from '@/utils/request'

const BASE_URL = '/api/global-market'

export function getMarketOverview() {
  return request.get<any>(`${BASE_URL}/overview`)
}

export function getMarketHeatmap() {
  return request.get<any>(`${BASE_URL}/heatmap`)
}

export function getMarketNews(lang = 'all') {
  return request.get<any>(`${BASE_URL}/news`, { params: { lang } })
}

export function getEconomicCalendar() {
  return request.get<any>(`${BASE_URL}/calendar`)
}

export function getMarketSentiment() {
  return request.get<any>(`${BASE_URL}/sentiment`)
}

export function getTradingOpportunities(params: Record<string, any>) {
  return request.get<any>(`${BASE_URL}/opportunities`, { params })
}

export function refreshMarketData() {
  return request.post<any>(`${BASE_URL}/refresh`)
}
