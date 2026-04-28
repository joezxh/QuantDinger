/**
 * Dify Workflow API
 * Workflow management and execution
 */
import request from '@/utils/request'

const BASE_URL = '/api/dify'

/**
 * List all registered Dify workflows
 */
export function getWorkflows() {
  return request.get<any>(`${BASE_URL}/workflows`)
}

/**
 * Get a single workflow by code
 * @param code - Workflow code
 */
export function getWorkflow(code: string) {
  return request.get<any>(`${BASE_URL}/workflows/${code}`)
}

/**
 * Create/register a new workflow
 * @param data - Workflow configuration
 */
export function createWorkflow(data: Record<string, any>) {
  return request.post<any>(`${BASE_URL}/workflows`, data)
}

/**
 * Update an existing workflow
 * @param code - Workflow code
 * @param data - Updated configuration
 */
export function updateWorkflow(code: string, data: Record<string, any>) {
  return request.put<any>(`${BASE_URL}/workflows/${code}`, data)
}

/**
 * Delete a workflow
 * @param code - Workflow code
 */
export function deleteWorkflow(code: string) {
  return request.delete<any>(`${BASE_URL}/workflows/${code}`)
}

/**
 * Execute a workflow in batch mode
 * @param code - Workflow code
 * @param data - { inputs, streaming }
 */
export function runWorkflow(code: string, data: Record<string, any>) {
  return request.post<any>(`${BASE_URL}/workflows/${code}/run`, data)
}

/**
 * Get execution logs for a workflow
 * @param code - Workflow code
 * @param params - { limit }
 */
export function getWorkflowLogs(code: string, params: Record<string, any>) {
  return request.get<any>(`${BASE_URL}/workflows/${code}/logs`, { params })
}
