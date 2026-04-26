import request from '@/utils/request'

const api = {
  configList: '/api/data-source/configs',
  configDetail: '/api/data-source/configs',
  configTest: '/api/data-source/configs',
  keyList: '/api/data-source/keys',
  datasetList: '/api/data-source/datasets',
  cacheList: '/api/data-source/cache',
  cacheCleanup: '/api/data-source/cache/cleanup'
}

// DataSource Config
export function getConfigs (parameter) {
  return request({
    url: api.configList,
    method: 'get',
    params: parameter
  })
}

export function getConfig (id) {
  return request({
    url: `${api.configDetail}/${id}`,
    method: 'get'
  })
}

export function saveConfig (data) {
  return request({
    url: data.id ? `${api.configList}/${data.id}` : api.configList,
    method: data.id ? 'put' : 'post',
    data
  })
}

export function deleteConfig (id) {
  return request({
    url: `${api.configList}/${id}`,
    method: 'delete'
  })
}

export function testConfig (id) {
  return request({
    url: `${api.configTest}/${id}/test`,
    method: 'post'
  })
}

// API Keys
export function getKeys (parameter) {
  return request({
    url: api.keyList,
    method: 'get',
    params: parameter
  })
}

export function saveKey (data) {
  return request({
    url: data.id ? `${api.keyList}/${data.id}` : api.keyList,
    method: data.id ? 'put' : 'post',
    data
  })
}

export function deleteKey (id) {
  return request({
    url: `${api.keyList}/${id}`,
    method: 'delete'
  })
}

// Datasets
export function getDatasets (parameter) {
  return request({
    url: api.datasetList,
    method: 'get',
    params: parameter
  })
}

export function saveDataset (data) {
  return request({
    url: data.id ? `${api.datasetList}/${data.id}` : api.datasetList,
    method: data.id ? 'put' : 'post',
    data
  })
}

export function deleteDataset (id) {
  return request({
    url: `${api.datasetList}/${id}`,
    method: 'delete'
  })
}

export function getConfigDatasets (configId) {
  return request({
    url: `${api.configDetail}/${configId}/datasets`,
    method: 'get'
  })
}

// Cache
export function getCacheList (parameter) {
  return request({
    url: api.cacheList,
    method: 'get',
    params: parameter
  })
}

export function deleteCache (id) {
  return request({
    url: `${api.cacheList}/${id}`,
    method: 'delete'
  })
}

export function cleanupCache (data) {
  return request({
    url: api.cacheCleanup,
    method: 'post',
    data
  })
}
