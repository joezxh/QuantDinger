import request from '@/utils/request'

const api = {
  strategies: '/addons/quantdinger/strategy/strategies',
  createAIStrategy: '/addons/quantdinger/strategy/aiCreate',
  updateAIStrategy: '/addons/quantdinger/strategy/aiUpdate',
  deleteStrategy: '/addons/quantdinger/strategy/delete',
  startStrategy: '/addons/quantdinger/strategy/start',
  stopStrategy: '/addons/quantdinger/strategy/stop',
  testConnection: '/addons/quantdinger/strategy/testConnection',
  aiDecisions: '/addons/quantdinger/strategy/aiDecisions',
  getCryptoSymbols: '/addons/quantdinger/strategy/getCryptoSymbols',
}

/**
 * 获取AI交易策略列表
 */
export function getStrategies() {
  return request.get<unknown>(api.strategies)
}

/**
 * 创建AI交易策略
 */
export function createAIStrategy(data: Record<string, unknown>) {
  return request.post<unknown>(api.createAIStrategy, data)
}

/**
 * 更新AI交易策略
 */
export function updateAIStrategy(data: Record<string, unknown>) {
  return request.post<unknown>(api.updateAIStrategy, data)
}

/**
 * 删除策略
 */
export function deleteStrategy(strategyId: number | string) {
  return request.delete<unknown>(api.deleteStrategy, { params: { id: strategyId } })
}

/**
 * 启动策略
 */
export function startStrategy(strategyId: number | string) {
  return request.post<unknown>(api.startStrategy, undefined, { params: { id: strategyId } })
}

/**
 * 停止策略
 */
export function stopStrategy(strategyId: number | string) {
  return request.post<unknown>(api.stopStrategy, undefined, { params: { id: strategyId } })
}

/**
 * 测试交易所连接
 */
export function testConnection(data: Record<string, unknown>) {
  return request.post<unknown>(api.testConnection, data)
}

/**
 * 获取AI决策记录
 */
export function getAIDecisions(strategyId: number | string, params: Record<string, unknown> = {}) {
  return request.get<unknown>(api.aiDecisions, { params: { strategy_id: strategyId, ...params } })
}

/**
 * 获取系统支持的交易对列表
 */
export function getCryptoSymbols() {
  return request.get<unknown>(api.getCryptoSymbols)
}
