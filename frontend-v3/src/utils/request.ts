import axios from 'axios'
import { message } from 'ant-design-vue'
import type { AxiosRequestConfig } from 'axios'

// Token storage keys
const ACCESS_TOKEN = 'access_token'
const USER_INFO = 'user_info'
const USER_ROLES = 'user_roles'

// Prevent multiple concurrent 401 redirects
let isRedirectingToLogin = false

/**
 * Get token from localStorage
 */
function getToken(): string | null {
  const raw = localStorage.getItem(ACCESS_TOKEN)
  if (!raw) return null

  try {
    const parsed = JSON.parse(raw)
    if (parsed && typeof parsed === 'object') {
      return parsed.token || parsed.value || null
    }
    return typeof parsed === 'string' ? parsed : null
  } catch {
    return typeof raw === 'string' ? raw : null
  }
}

/**
 * Save token to localStorage
 */
export function setToken(token: string): void {
  localStorage.setItem(ACCESS_TOKEN, token)
}

/**
 * Remove auth data
 */
export function clearAuth(): void {
  localStorage.removeItem(ACCESS_TOKEN)
  localStorage.removeItem(USER_INFO)
  localStorage.removeItem(USER_ROLES)
}

/**
 * Check if user is authenticated
 */
export function isAuthenticated(): boolean {
  return !!getToken()
}

// Extended timeout for long-running APIs
const ANALYSIS_TIMEOUT = 180000 // 3 minutes
const AI_GENERATE_TIMEOUT = 180000 // 3 minutes
const BACKTEST_TIMEOUT = 600000 // 10 minutes

/**
 * Create axios instance
 */
const service = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL ?? '',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json;charset=utf-8',
  },
  withCredentials: true,
})

/**
 * Request interceptor
 */
service.interceptors.request.use(
  (config) => {
    // Check if timeout is default, then override for specific APIs
    const isDefaultTimeout = !config.timeout || config.timeout === service.defaults.timeout
    if (config.url && isDefaultTimeout) {
      if (config.url.includes('/backtest/aiAnalyze')) {
        config.timeout = ANALYSIS_TIMEOUT
      } else if (config.url.includes('/strategies/ai-generate') || config.url.includes('/indicator/aiGenerate')) {
        config.timeout = AI_GENERATE_TIMEOUT
      } else if (config.url.includes('/backtest')) {
        config.timeout = BACKTEST_TIMEOUT
      }
    }

    // Add Authorization header
    const token = getToken()
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }

    // Prevent caching
    config.headers['Cache-Control'] = 'no-cache'
    config.headers['Pragma'] = 'no-cache'

    // Add timestamp to GET requests to prevent caching
    if ((config.method || 'get').toLowerCase() === 'get') {
      config.params = Object.assign({}, config.params || {}, { _t: Date.now() })
    }

    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

/**
 * Response interceptor
 */
service.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    if (error.response) {
      const data = error.response.data
      const status = error.response.status

      switch (status) {
        case 401:
          if (!isRedirectingToLogin) {
            isRedirectingToLogin = true
            clearAuth()
            message.error('登录已过期，请重新登录')
            const curPath = window.location.pathname
            if (!curPath.includes('/login')) {
              const redirect = encodeURIComponent(curPath)
              window.location.href = `/login?redirect=${redirect}`
            }
          }
          break
        case 403:
          message.error('没有权限访问该资源')
          break
        case 404:
          message.error('请求的资源不存在')
          break
        case 500:
          message.error('服务器错误')
          break
        default:
          message.error(data?.message || data?.msg || '请求失败')
      }
    } else if (error.message) {
      message.error(error.message)
    } else {
      message.error('网络连接失败')
    }

    return Promise.reject(error)
  }
)

/**
 * Typed request methods
 */
const request = {
  get<T = unknown>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return service.get(url, config)
  },
  post<T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    return service.post(url, data, config)
  },
  put<T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T> {
    return service.put(url, data, config)
  },
  delete<T = unknown>(url: string, config?: AxiosRequestConfig): Promise<T> {
    return service.delete(url, config)
  },
}

export default request
