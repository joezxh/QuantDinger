import request from '@/utils/request'

// ─── API Endpoints ──────────────────────────────────────────────────────────
const api = {
  strategies: '/api/strategies',
  strategyDetail: '/api/strategies/detail',
  createStrategy: '/api/strategies/create',
  batchCreateStrategies: '/api/strategies/batch-create',
  updateStrategy: '/api/strategies/update',
  stopStrategy: '/api/strategies/stop',
  startStrategy: '/api/strategies/start',
  deleteStrategy: '/api/strategies/delete',
  batchStartStrategies: '/api/strategies/batch-start',
  batchStopStrategies: '/api/strategies/batch-stop',
  batchDeleteStrategies: '/api/strategies/batch-delete',
  testConnection: '/api/strategies/test-connection',
  trades: '/api/strategies/trades',
  positions: '/api/strategies/positions',
  equityCurve: '/api/strategies/equityCurve',
  notifications: '/api/strategies/notifications',
  unreadNotificationCount: '/api/strategies/notifications/unread-count',
  verifyCode: '/api/strategies/verify-code',
  aiGenerate: '/api/strategies/ai-generate',
  performance: '/api/strategies/performance',
  logs: '/api/strategies/logs',
  backtest: '/api/strategies/backtest',
  backtestHistory: '/api/strategies/backtest/history',
  backtestGet: '/api/strategies/backtest/get',
}

// ─── Types ───────────────────────────────────────────────────────────────────
export interface StrategyListParams {
  user_id?: number
  [key: string]: unknown
}

export interface CreateStrategyData {
  user_id?: number
  strategy_name: string
  strategy_type: string
  strategy_mode?: string
  llm_model_config?: Record<string, unknown>
  exchange_config?: Record<string, unknown>
  trading_config?: Record<string, unknown>
  indicator_config?: Record<string, unknown>
  script_config?: Record<string, unknown>
  [key: string]: unknown
}

export interface BatchCreateStrategyData {
  strategy_name: string
  symbols: string[]
  [key: string]: unknown
}

export interface BacktestRunData {
  timeout?: number
  [key: string]: unknown
}

// ─── Strategy CRUD ───────────────────────────────────────────────────────────

export function getStrategyList(params: StrategyListParams = {}) {
  return request.get<unknown>('/api/strategies', { params })
}

export function getStrategyDetail(id: number) {
  return request.get<unknown>(api.strategyDetail, { params: { id } })
}

export function createStrategy(data: CreateStrategyData) {
  return request.post<unknown>(api.createStrategy, data)
}

export function batchCreateStrategies(data: BatchCreateStrategyData) {
  return request.post<unknown>(api.batchCreateStrategies, data)
}

export function updateStrategy(id: number, data: Partial<CreateStrategyData>) {
  return request.put<unknown>(api.updateStrategy, data, { params: { id } })
}

export function stopStrategy(id: number) {
  return request.post<unknown>(api.stopStrategy, undefined, { params: { id } })
}

export function startStrategy(id: number) {
  return request.post<unknown>(api.startStrategy, undefined, { params: { id } })
}

export function deleteStrategy(id: number) {
  return request.delete<unknown>(api.deleteStrategy, { params: { id } })
}

// ─── Batch Operations ────────────────────────────────────────────────────────

export function batchStartStrategies(data: { strategy_ids?: number[]; strategy_group_id?: string }) {
  return request.post<unknown>(api.batchStartStrategies, data)
}

export function batchStopStrategies(data: { strategy_ids?: number[]; strategy_group_id?: string }) {
  return request.post<unknown>(api.batchStopStrategies, data)
}

export function batchDeleteStrategies(data: { strategy_ids?: number[]; strategy_group_id?: string }) {
  return request.delete<unknown>(api.batchDeleteStrategies, { data })
}

// ─── Exchange Connection ──────────────────────────────────────────────────────

export function testExchangeConnection(exchangeConfig: Record<string, unknown>) {
  return request.post<unknown>(api.testConnection, { exchange_config: exchangeConfig })
}

// ─── Records & Performance ───────────────────────────────────────────────────

export function getStrategyTrades(id: number) {
  return request.get<unknown>(api.trades, { params: { id } })
}

export function getStrategyPositions(id: number) {
  return request.get<unknown>(api.positions, { params: { id } })
}

export function getStrategyEquityCurve(id: number) {
  return request.get<unknown>(api.equityCurve, { params: { id } })
}

export function getStrategyPerformance(id: number) {
  return request.get<unknown>(api.performance, { params: { id } })
}

export function getStrategyLogs(id: number, params: Record<string, unknown> = {}) {
  return request.get<unknown>(api.logs, { params: { id, ...params } })
}

// ─── Notifications ───────────────────────────────────────────────────────────

export function getStrategyNotifications(params: { id?: number; limit?: number; since_id?: number } = {}) {
  return request.get<unknown>(api.notifications, { params })
}

export function getUnreadNotificationCount() {
  return request.get<unknown>(api.unreadNotificationCount)
}

// ─── AI & Code ───────────────────────────────────────────────────────────────

export function verifyStrategyCode(data: Record<string, unknown>) {
  return request.post<unknown>(api.verifyCode, data)
}

export function aiGenerateStrategy(data: Record<string, unknown>) {
  return request.post<unknown>(api.aiGenerate, data)
}

// ─── Backtest ────────────────────────────────────────────────────────────────

export function runStrategyBacktest(data: BacktestRunData) {
  const payload = { ...data }
  const timeout = payload.timeout
  delete payload.timeout
  return request.post<unknown>(api.backtest, payload, timeout ? { timeout } : undefined)
}

export function getStrategyBacktestHistory(params: Record<string, unknown> = {}) {
  return request.get<unknown>(api.backtestHistory, { params })
}

export function getStrategyBacktestRun(runId: string | number) {
  return request.get<unknown>(api.backtestGet, { params: { runId } })
}
