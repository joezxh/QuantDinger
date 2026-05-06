/**
 * Polymarket预测市场API
 * 仅保留按需分析功能
 */
import request from '@/utils/request'

const BASE_URL = '/api/polymarket'

/**
 * 分析Polymarket预测市场（从链接或标题）
 * @param data - 请求数据
 * @param data.input - Polymarket链接或市场标题
 * @param data.language - 语言 (zh-CN/en-US)
 */
export function analyzePolymarketMarket(data: { input: string; language?: string }) {
  return request.post<unknown>(`${BASE_URL}/analyze`, data, { timeout: 120000 })
}

/**
 * 获取Polymarket分析历史记录
 * @param params - 查询参数
 * @param params.page - 页码
 * @param params.page_size - 每页数量
 */
export function getPolymarketHistory(params?: { page?: number; page_size?: number }) {
  return request.get<unknown>(`${BASE_URL}/history`, { params })
}
