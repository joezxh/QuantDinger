import request from '@/utils/request'

const api = {
  providerList: '/api/llm/provider/list',
  providerCreate: '/api/llm/provider/create',
  providerUpdate: '/api/llm/provider/update',
  keyList: '/api/llm/key/list',
  keyCreate: '/api/llm/key/create',
  keyUpdate: '/api/llm/key/update',
  modelList: '/api/llm/model/list',
  modelCreate: '/api/llm/model/create',
  modelUpdate: '/api/llm/model/update',
  stats: '/api/llm/monitor/stats'
}

// Providers
export function getProviders (parameter) {
  return request({
    url: api.providerList,
    method: 'get',
    params: parameter
  })
}

export function saveProvider (data) {
  return request({
    url: data.id ? api.providerUpdate : api.providerCreate,
    method: data.id ? 'put' : 'post',
    data
  })
}

export function deleteProvider (id) {
  return Promise.reject(new Error('Delete provider endpoint not yet implemented'))
}

// Keys
export function getKeys (parameter) {
  return request({
    url: api.keyList,
    method: 'get',
    params: parameter
  })
}

export function saveKey (data) {
  return request({
    url: data.id ? api.keyUpdate : api.keyCreate,
    method: data.id ? 'put' : 'post',
    data
  })
}

export function deleteKey (id) {
  return Promise.reject(new Error('Delete key endpoint not yet implemented'))
}

// Models
export function getModels (parameter) {
  return request({
    url: api.modelList,
    method: 'get',
    params: parameter
  })
}

export function saveModel (data) {
  return request({
    url: data.id ? api.modelUpdate : api.modelCreate,
    method: data.id ? 'put' : 'post',
    data
  })
}

export function deleteModel (id) {
  return Promise.reject(new Error('Delete model endpoint not yet implemented'))
}

// Stats & Logs
export function getLLMStats () {
  return request({
    url: api.stats,
    method: 'get'
  })
}

export function getLLMLogs (parameter) {
  return Promise.reject(new Error('LLM logs endpoint not yet implemented'))
}
