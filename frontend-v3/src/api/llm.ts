import request from '@/utils/request'

// ─── Providers ───────────────────────────────────────────────────────────────

export function getProviders(params?: Record<string, unknown>) {
  return request.get<unknown>('/api/llm/provider/list', { params })
}

export function saveProvider(data: Record<string, unknown> & { id?: number }) {
  const url = data.id ? '/api/llm/provider/update' : '/api/llm/provider/create'
  return data.id
    ? request.put<unknown>(url, data)
    : request.post<unknown>(url, data)
}

// ─── Keys ────────────────────────────────────────────────────────────────────

export function getKeys(params?: Record<string, unknown>) {
  return request.get<unknown>('/api/llm/key/list', { params })
}

export function saveKey(data: Record<string, unknown> & { id?: number }) {
  const url = data.id ? '/api/llm/key/update' : '/api/llm/key/create'
  return data.id
    ? request.put<unknown>(url, data)
    : request.post<unknown>(url, data)
}

// ─── Models ──────────────────────────────────────────────────────────────────

export function getModels(params?: Record<string, unknown>) {
  return request.get<unknown>('/api/llm/model/list', { params })
}

export function saveModel(data: Record<string, unknown> & { id?: number }) {
  const url = data.id ? '/api/llm/model/update' : '/api/llm/model/create'
  return data.id
    ? request.put<unknown>(url, data)
    : request.post<unknown>(url, data)
}

// ─── Stats ───────────────────────────────────────────────────────────────────

export function getLLMStats() {
  return request.get<unknown>('/api/llm/monitor/stats')
}

export function getLLMLogs(params?: Record<string, unknown>) {
  return request.get<unknown>('/api/llm/monitor/logs', { params })
}

export function deleteProvider(id: number) {
  return request.delete<unknown>(`/api/llm/provider/delete/${id}`)
}

export function deleteKey(id: number) {
  return request.delete<unknown>(`/api/llm/key/delete/${id}`)
}

export function deleteModel(id: number) {
  return request.delete<unknown>(`/api/llm/model/delete/${id}`)
}

