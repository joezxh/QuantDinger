import request from '@/utils/request'

const api = {
  providers: '/api/llm/providers',
  keys: '/api/llm/keys',
  models: '/api/llm/models',
  stats: '/api/llm/stats',
  logs: '/api/llm/logs'
}

// Providers
export function getProviders(parameter) {
  return request({
    url: api.providers,
    method: 'get',
    params: parameter
  })
}

export function saveProvider(data) {
  return request({
    url: api.providers,
    method: data.id ? 'put' : 'post',
    data
  })
}

export function deleteProvider(id) {
  return request({
    url: `${api.providers}/${id}`,
    method: 'delete'
  })
}

// Keys
export function getKeys(parameter) {
  return request({
    url: api.keys,
    method: 'get',
    params: parameter
  })
}

export function saveKey(data) {
  return request({
    url: api.keys,
    method: data.id ? 'put' : 'post',
    data
  })
}

export function deleteKey(id) {
  return request({
    url: `${api.keys}/${id}`,
    method: 'delete'
  })
}

// Models
export function getModels(parameter) {
  return request({
    url: api.models,
    method: 'get',
    params: parameter
  })
}

export function saveModel(data) {
  return request({
    url: api.models,
    method: data.id ? 'put' : 'post',
    data
  })
}

export function deleteModel(id) {
  return request({
    url: `${api.models}/${id}`,
    method: 'delete'
  })
}

// Stats & Logs
export function getLLMStats() {
  return request({
    url: api.stats,
    method: 'get'
  })
}

export function getLLMLogs(parameter) {
  return request({
    url: api.logs,
    method: 'get',
    params: parameter
  })
}
