/**
 * Generic sync task scheduler API
 */
import request from '@/utils/request'

const BASE_URL = '/api/sync'

/**
 * Get sync job configurations
 * @param {Object} params - query params (source_type, executor_type)
 */
export function getSyncJobs (params) {
  return request({
    url: `${BASE_URL}/jobs`,
    method: 'get',
    params
  })
}

/**
 * Create a new sync job
 * @param {Object} data
 */
export function createSyncJob (data) {
  return request({
    url: `${BASE_URL}/jobs`,
    method: 'post',
    data
  })
}

/**
 * Update sync job configuration
 * @param {number} jobId
 * @param {Object} data
 */
export function updateSyncJob (jobId, data) {
  return request({
    url: `${BASE_URL}/jobs/${jobId}`,
    method: 'put',
    data
  })
}

/**
 * Delete a sync job
 * @param {number} jobId
 */
export function deleteSyncJob (jobId) {
  return request({
    url: `${BASE_URL}/jobs/${jobId}`,
    method: 'delete'
  })
}

/**
 * Manually trigger a sync job
 * @param {number} jobId
 * @param {Object} data - { run_type, limit }
 */
export function runSyncJob (jobId, data = {}) {
  return request({
    url: `${BASE_URL}/jobs/${jobId}/run`,
    method: 'post',
    data
  })
}

/**
 * Get sync execution history
 * @param {Object} params
 */
export function getSyncRuns (params) {
  return request({
    url: `${BASE_URL}/runs`,
    method: 'get',
    params
  })
}

/**
 * Get current scheduler status
 */
export function getSyncStatus () {
  return request({
    url: `${BASE_URL}/status`,
    method: 'get'
  })
}

/**
 * Initialize default sync jobs
 */
export function initSyncJobs () {
  return request({
    url: `${BASE_URL}/init`,
    method: 'post'
  })
}
