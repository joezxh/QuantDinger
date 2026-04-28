/**
 * Graph Analysis API
 * Knowledge graph context, queries and quality monitoring
 */
import request from '@/utils/request'

const BASE_URL = '/api/graph-analysis'

/**
 * Get structured graph context for a market+symbol pair
 * @param {Object} params - { market, symbol }
 */
export function getGraphContext (params) {
  return request({
    url: `${BASE_URL}/context`,
    method: 'get',
    params
  })
}

/**
 * Get graph context formatted as LLM-ready text
 * @param {Object} params - { market, symbol }
 */
export function getGraphContextForLLM (params) {
  return request({
    url: `${BASE_URL}/context/llm`,
    method: 'get',
    params
  })
}

/**
 * Find assets correlated with the given symbol
 * @param {Object} params - { market, symbol }
 */
export function getRelatedAssets (params) {
  return request({
    url: `${BASE_URL}/related`,
    method: 'get',
    params
  })
}

/**
 * Get recent events affecting a symbol
 * @param {Object} params - { symbol, limit }
 */
export function getRecentEvents (params) {
  return request({
    url: `${BASE_URL}/events`,
    method: 'get',
    params
  })
}

/**
 * Execute a read-only Cypher query (admin/debug use)
 * @param {Object} data - { query, params }
 */
export function runCypherQuery (data) {
  return request({
    url: `${BASE_URL}/cypher`,
    method: 'post',
    data
  })
}

/**
 * Get graph data quality / readiness report
 */
export function getGraphQuality () {
  return request({
    url: `${BASE_URL}/quality`,
    method: 'get'
  })
}

/**
 * Query contagion path between two assets
 * @param {Object} params - { from, to, market }
 */
export function getContagionPath (params) {
  return request({
    url: `${BASE_URL}/contagion-path`,
    method: 'get',
    params
  })
}

/**
 * Get smart-money signals for a symbol
 * @param {Object} params - { symbol, domain }
 */
export function getSmartMoney (symbol, params) {
  return request({
    url: `${BASE_URL}/smart-money/${encodeURIComponent(symbol)}`,
    method: 'get',
    params
  })
}

/**
 * Trace event impact chain
 * @param {Object} params - { event_uid, max_depth }
 */
export function getEventImpact (eventUid, params) {
  return request({
    url: `${BASE_URL}/event-impact/${encodeURIComponent(eventUid)}`,
    method: 'get',
    params
  })
}
