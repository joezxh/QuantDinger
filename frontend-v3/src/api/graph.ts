/**
 * Graph Analysis API
 * Knowledge graph context, queries and quality monitoring
 */
import request from '@/utils/request'

const BASE_URL = '/api/graph-analysis'

/**
 * Get structured graph context for a market+symbol pair
 * @param params - { market, symbol }
 */
export function getGraphContext(params: Record<string, any>) {
  return request.get<any>(`${BASE_URL}/context`, { params })
}

/**
 * Get graph context formatted as LLM-ready text
 * @param params - { market, symbol }
 */
export function getGraphContextForLLM(params: Record<string, any>) {
  return request.get<any>(`${BASE_URL}/context/llm`, { params })
}

/**
 * Find assets correlated with the given symbol
 * @param params - { market, symbol }
 */
export function getRelatedAssets(params: Record<string, any>) {
  return request.get<any>(`${BASE_URL}/related`, { params })
}

/**
 * Get recent events affecting a symbol
 * @param params - { symbol, limit }
 */
export function getRecentEvents(params: Record<string, any>) {
  return request.get<any>(`${BASE_URL}/events`, { params })
}

/**
 * Execute a read-only Cypher query (admin/debug use)
 * @param data - { query, params }
 */
export function runCypherQuery(data: Record<string, any>) {
  return request.post<any>(`${BASE_URL}/cypher`, data)
}

/**
 * Get graph data quality / readiness report
 */
export function getGraphQuality() {
  return request.get<any>(`${BASE_URL}/quality`)
}

/**
 * Query contagion path between two assets
 * @param params - { from, to, market }
 */
export function getContagionPath(params: Record<string, any>) {
  return request.get<any>(`${BASE_URL}/contagion-path`, { params })
}

/**
 * Get smart-money signals for a symbol
 * @param symbol
 * @param params - { symbol, domain }
 */
export function getSmartMoney(symbol: string, params: Record<string, any>) {
  return request.get<any>(`${BASE_URL}/smart-money/${encodeURIComponent(symbol)}`, { params })
}

/**
 * Trace event impact chain
 * @param eventUid
 * @param params - { event_uid, max_depth }
 */
export function getEventImpact(eventUid: string, params: Record<string, any>) {
  return request.get<any>(`${BASE_URL}/event-impact/${encodeURIComponent(eventUid)}`, { params })
}
