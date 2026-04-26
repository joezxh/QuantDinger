/**
 * Dify Workflow API
 * Workflow management and execution
 */
import request from '@/utils/request'

const BASE_URL = '/api/dify'

/**
 * List all registered Dify workflows
 */
export function getWorkflows () {
  return request({
    url: `${BASE_URL}/workflows`,
    method: 'get'
  })
}

/**
 * Get a single workflow by code
 * @param {String} code - Workflow code
 */
export function getWorkflow (code) {
  return request({
    url: `${BASE_URL}/workflows/${code}`,
    method: 'get'
  })
}

/**
 * Create/register a new workflow
 * @param {Object} data - Workflow configuration
 */
export function createWorkflow (data) {
  return request({
    url: `${BASE_URL}/workflows`,
    method: 'post',
    data
  })
}

/**
 * Update an existing workflow
 * @param {String} code - Workflow code
 * @param {Object} data - Updated configuration
 */
export function updateWorkflow (code, data) {
  return request({
    url: `${BASE_URL}/workflows/${code}`,
    method: 'put',
    data
  })
}

/**
 * Delete a workflow
 * @param {String} code - Workflow code
 */
export function deleteWorkflow (code) {
  return request({
    url: `${BASE_URL}/workflows/${code}`,
    method: 'delete'
  })
}

/**
 * Execute a workflow in batch mode
 * @param {String} code - Workflow code
 * @param {Object} data - { inputs, streaming }
 */
export function runWorkflow (code, data) {
  return request({
    url: `${BASE_URL}/workflows/${code}/run`,
    method: 'post',
    data
  })
}

/**
 * Get execution logs for a workflow
 * @param {String} code - Workflow code
 * @param {Object} params - { limit }
 */
export function getWorkflowLogs (code, params) {
  return request({
    url: `${BASE_URL}/workflows/${code}/logs`,
    method: 'get',
    params
  })
}
