import request from '@/utils/request'

export function getSettingsSchema() {
  return request.get<any>('/api/settings/schema')
}

export function getSettingsValues() {
  return request.get<any>('/api/settings/values')
}

export function saveSettings(data: Record<string, Record<string, any>>) {
  return request.post<any>('/api/settings/save', data)
}

export function getOpenRouterBalance() {
  return request.get<any>('/api/settings/openrouter/balance')
}
