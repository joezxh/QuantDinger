import request from '@/utils/request'

const BASE = '/api/data-sources'

// ─── 数据源配置管理 ─────────────────────────────────────────────────────────

/**
 * 获取所有数据源配置
 */
export function getDataSources(params?: {
  search?: string
  layer?: string
  enabled?: boolean
  page?: number
  page_size?: number
}) {
  return request.get<{
    data_sources: any[]
    total: number
  }>(`${BASE}/`, { params })
}

/**
 * 获取指定数据源配置详情
 */
export function getDataSource(sourceCode: string) {
  return request.get<any>(`${BASE}/${sourceCode}`)
}

/**
 * 创建数据源配置
 */
export function createDataSource(data: {
  source_code: string
  source_name: string
  layer: string
  market_categories: string[]
  enabled: boolean
  load_balance_strategy: string
  config_json: Record<string, any>
  notes?: string
}) {
  return request.post<any>(`${BASE}/`, data)
}

/**
 * 更新数据源配置
 */
export function updateDataSource(sourceCode: string, data: Record<string, any>) {
  return request.put<any>(`${BASE}/${sourceCode}`, data)
}

/**
 * 删除数据源配置
 */
export function deleteDataSource(sourceCode: string) {
  return request.delete<any>(`${BASE}/${sourceCode}`)
}

/**
 * 启用/禁用数据源
 */
export function toggleDataSource(sourceCode: string, enabled: boolean) {
  return request.post<any>(`${BASE}/${sourceCode}/toggle`, { enabled })
}

/**
 * 测试数据源连接
 */
export function testDataSource(sourceCode: string) {
  return request.post<any>(`${BASE}/health/${sourceCode}`)
}

// ─── 健康状态管理 ───────────────────────────────────────────────────────────

/**
 * 获取所有数据源健康状态
 */
export function getHealthStatus() {
  return request.get<any>(`${BASE}/health`)
}

/**
 * 获取路由器状态
 */
export function getRouterStatus() {
  return request.get<any>(`${BASE}/router/status`)
}

/**
 * 获取数据类别列表
 */
export function getDataCategories() {
  return request.get<any>(`${BASE}/categories`)
}

// ─── API 密钥管理 ───────────────────────────────────────────────────────────

/**
 * 获取数据源的API密钥列表
 */
export function getApiKeys(sourceCode: string) {
  return request.get<any>(`${BASE}/${sourceCode}/api-keys`)
}

/**
 * 添加API密钥
 */
export function addApiKey(sourceCode: string, data: {
  key_type: string
  key_alias: string
  encrypted_key_value: string
  weight?: number
  daily_call_limit?: number
  status?: boolean
}) {
  return request.post<any>(`${BASE}/${sourceCode}/api-keys`, data)
}

/**
 * 更新API密钥
 */
export function updateApiKey(sourceCode: string, keyId: number, data: Record<string, any>) {
  return request.put<any>(`${BASE}/${sourceCode}/api-keys/${keyId}`, data)
}

/**
 * 删除API密钥
 */
export function deleteApiKey(sourceCode: string, keyId: number) {
  return request.delete<any>(`${BASE}/${sourceCode}/api-keys/${keyId}`)
}

/**
 * 启用/禁用API密钥
 */
export function toggleApiKey(sourceCode: string, keyId: number, enabled: boolean) {
  return request.post<any>(`${BASE}/${sourceCode}/api-keys/${keyId}/toggle`, { enabled })
}

// ─── 限流配置管理 ───────────────────────────────────────────────────────────

/**
 * 获取数据源限流配置
 */
export function getRateLimitConfig(sourceCode: string) {
  return request.get<any>(`${BASE}/${sourceCode}/rate-limit`)
}

/**
 * 更新限流配置
 */
export function updateRateLimitConfig(sourceCode: string, data: {
  strategy?: string
  rate?: number
  period?: number
  burst?: number
  max_concurrent?: number
  enable_adaptive?: boolean
  reduce_rate_on_error?: boolean
  error_threshold?: number
  priority?: number
  notes?: string
}) {
  return request.put<any>(`${BASE}/${sourceCode}/rate-limit`, data)
}

/**
 * 获取限流统计信息
 */
export function getRateLimitStats(sourceCode: string) {
  return request.get<any>(`${BASE}/${sourceCode}/rate-limit/stats`)
}

// ─── 优先级调整 ─────────────────────────────────────────────────────────────

/**
 * 获取优先级调整状态
 */
export function getPriorityStatus() {
  return request.get<any>(`${BASE}/priority/status`)
}

/**
 * 手动触发优先级调整
 */
export function adjustPriorities() {
  return request.post<any>(`${BASE}/priority/adjust`, {})
}

// ─── 宏观经济数据 ───────────────────────────────────────────────────────────

/**
 * 获取宏观经济指标
 */
export function getMacroIndicators(category?: string) {
  return request.get<any>(`${BASE}/macro/indicators`, {
    params: { category }
  })
}

// ─── 新闻数据 ───────────────────────────────────────────────────────────────

/**
 * 获取新闻数据
 */
export function getNews(params?: {
  source?: string
  query?: string
  limit?: number
}) {
  return request.get<any>(`${BASE}/news`, { params })
}

// ─── DeFi TVL数据 ───────────────────────────────────────────────────────────

/**
 * 获取DeFi TVL数据
 */
export function getDefiTvl(type?: string) {
  return request.get<any>(`${BASE}/defi/tvl`, {
    params: { type }
  })
}

// ─── CFTC持仓报告 ───────────────────────────────────────────────────────────

/**
 * 获取CFTC持仓报告
 */
export function getCotReport(commodity?: string, limit?: number) {
  return request.get<any>(`${BASE}/cftc/cot`, {
    params: { commodity, limit }
  })
}

// ─── CBOE波动率指数 ─────────────────────────────────────────────────────────

/**
 * 获取CBOE波动率指数历史数据
 */
export function getCboeHistory(params?: {
  index?: string
  start_date?: string
  end_date?: string
}) {
  return request.get<any>(`${BASE}/cboe/history`, { params })
}

/**
 * 获取CBOE可用指数列表
 */
export function getCboeIndices() {
  return request.get<any>(`${BASE}/cboe/indices`)
}

/**
 * 获取VIX期货期限结构
 */
export function getCboeFutures(date?: string) {
  return request.get<any>(`${BASE}/cboe/futures`, {
    params: { date }
  })
}

// ─── BEA经济指标 ────────────────────────────────────────────────────────────

/**
 * 获取BEA宏观经济指标
 */
export function getBeaIndicators(params?: {
  indicator?: string
  year?: string
  frequency?: string
}) {
  return request.get<any>(`${BASE}/bea/indicators`, { params })
}

// ─── 基本面数据 ─────────────────────────────────────────────────────────────

/**
 * 获取基本面数据
 */
export function getFundamentals(ticker: string, frequency?: string) {
  return request.get<any>(`${BASE}/fundamentals/${ticker}`, {
    params: { frequency }
  })
}
