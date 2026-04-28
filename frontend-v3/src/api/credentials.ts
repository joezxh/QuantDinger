import request from '@/utils/request'

export function listExchangeCredentials(params: Record<string, unknown> = {}) {
  return request.get<unknown>('/api/credentials/list', { params })
}

export function getExchangeCredential(id: number, params: Record<string, unknown> = {}) {
  return request.get<unknown>('/api/credentials/get', { params: { id, ...params } })
}

export function createExchangeCredential(data: Record<string, unknown>) {
  return request.post<unknown>('/api/credentials/create', data)
}

export function deleteExchangeCredential(id: number, params: Record<string, unknown> = {}) {
  return request.delete<unknown>('/api/credentials/delete', { params: { id, ...params } })
}

/** Server egress IP (for exchange API key IP whitelist). */
export function getCredentialsEgressIp() {
  return request.get<unknown>('/api/credentials/egress-ip')
}
