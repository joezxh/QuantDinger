import request from '@/utils/request'

const BASE_URL = '/api/fast-analysis'

export interface AnalyzeParams {
  market: string
  symbol: string
  language?: string
  timeframe?: string
  use_dify?: boolean
  workflow_code?: string
}

export function fastAnalyze(params: AnalyzeParams) {
  return request.post<any>(`${BASE_URL}/analyze`, params, {
    timeout: 300000,
  })
}

export function fastAnalyzeLegacy(params: AnalyzeParams) {
  return request.post<any>(`${BASE_URL}/analyze-legacy`, params, {
    timeout: 300000,
  })
}

export function getAnalysisHistory(params: Record<string, any>) {
  return request.get<any>(`${BASE_URL}/history`, { params })
}

export function getAllAnalysisHistory(params: Record<string, any>) {
  return request.get<any>(`${BASE_URL}/history/all`, { params })
}

export function deleteAnalysisHistory(memoryId: number) {
  return request.delete<any>(`${BASE_URL}/history/${memoryId}`)
}

export function submitFeedback(params: { memory_id: number; feedback: string }) {
  return request.post<any>(`${BASE_URL}/feedback`, params)
}

export function getPerformanceStats(params: Record<string, any>) {
  return request.get<any>(`${BASE_URL}/performance`, { params })
}

export function getSimilarPatterns(params: Record<string, any>) {
  return request.get<any>(`${BASE_URL}/similar-patterns`, { params })
}
