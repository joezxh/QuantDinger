import request from '@/utils/request'

const BASE = '/api/data-source'

// ─── Configs ─────────────────────────────────────────────────────────────────

export function getConfigs(params?: Record<string, unknown>) {
  return request.get<unknown>(`${BASE}/configs`, { params })
}

export function getConfig(id: number) {
  return request.get<unknown>(`${BASE}/configs/${id}`)
}

export function saveConfig(data: Record<string, unknown> & { id?: number }) {
  return data.id
    ? request.put<unknown>(`${BASE}/configs/${data.id}`, data)
    : request.post<unknown>(`${BASE}/configs`, data)
}

export function deleteConfig(id: number) {
  return request.delete<unknown>(`${BASE}/configs/${id}`)
}

export function testConfig(id: number) {
  return request.post<unknown>(`${BASE}/configs/${id}/test`, {})
}

// ─── API Keys ────────────────────────────────────────────────────────────────

export function getDataSourceKeys(params?: Record<string, unknown>) {
  return request.get<unknown>(`${BASE}/keys`, { params })
}

export function saveDataSourceKey(data: Record<string, unknown> & { id?: number }) {
  return data.id
    ? request.put<unknown>(`${BASE}/keys/${data.id}`, data)
    : request.post<unknown>(`${BASE}/keys`, data)
}

export function deleteDataSourceKey(id: number) {
  return request.delete<unknown>(`${BASE}/keys/${id}`)
}

// ─── Datasets ────────────────────────────────────────────────────────────────

export function getDatasets(params?: Record<string, unknown>) {
  return request.get<unknown>(`${BASE}/datasets`, { params })
}

export function getConfigDatasets(configId: number) {
  return request.get<unknown>(`${BASE}/configs/${configId}/datasets`)
}

export function saveDataset(data: Record<string, unknown> & { id?: number }) {
  return data.id
    ? request.put<unknown>(`${BASE}/datasets/${data.id}`, data)
    : request.post<unknown>(`${BASE}/datasets`, data)
}

export function deleteDataset(id: number) {
  return request.delete<unknown>(`${BASE}/datasets/${id}`)
}

// ─── Cache ───────────────────────────────────────────────────────────────────

export function getCacheList(params?: Record<string, unknown>) {
  return request.get<unknown>(`${BASE}/cache`, { params })
}

export function deleteCache(id: number) {
  return request.delete<unknown>(`${BASE}/cache/${id}`)
}

export function cleanupCache(data: Record<string, unknown>) {
  return request.post<unknown>(`${BASE}/cache/cleanup`, data)
}
