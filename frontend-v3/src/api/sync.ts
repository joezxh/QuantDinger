import request from '@/utils/request'

const BASE = '/api/sync'

export function getSyncJobs(params?: Record<string, unknown>) {
  return request.get<unknown>(`${BASE}/jobs`, { params })
}

export function createSyncJob(data: Record<string, unknown>) {
  return request.post<unknown>(`${BASE}/jobs`, data)
}

export function updateSyncJob(jobId: number, data: Record<string, unknown>) {
  return request.put<unknown>(`${BASE}/jobs/${jobId}`, data)
}

export function deleteSyncJob(jobId: number) {
  return request.delete<unknown>(`${BASE}/jobs/${jobId}`)
}

export function runSyncJob(jobId: number, data: Record<string, unknown> = {}) {
  return request.post<unknown>(`${BASE}/jobs/${jobId}/run`, data)
}

export function getSyncRuns(params?: Record<string, unknown>) {
  return request.get<unknown>(`${BASE}/runs`, { params })
}

export function getSyncStatus() {
  return request.get<unknown>(`${BASE}/status`)
}

export function initSyncJobs() {
  return request.post<unknown>(`${BASE}/init`, {})
}
