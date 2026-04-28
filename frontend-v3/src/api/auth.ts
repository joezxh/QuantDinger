import request from '@/utils/request'
import type { LoginParams, LoginResult, UserInfo } from '@/types/api'

const BASE_URL = '/api/auth'

/**
 * 登录
 */
export function login(data: LoginParams) {
  return request.post<{ code: number; data: LoginResult }>(`${BASE_URL}/login`, data)
}

/**
 * 获取当前用户信息
 */
export function getUserInfo() {
  return request.get<{ code: number; data: UserInfo }>(`${BASE_URL}/info`)
}

/**
 * 登出
 */
export function logout() {
  return request.post(`${BASE_URL}/logout`)
}

/**
 * 发送验证码
 */
export function sendVerificationCode(data: { email: string; type: string; turnstile_token?: string }) {
  return request.post(`${BASE_URL}/send-code`, data)
}

/**
 * 验证码登录
 */
export function loginWithCode(data: { email: string; code: string; turnstile_token?: string }) {
  return request.post(`${BASE_URL}/login-code`, data)
}

/**
 * 注册
 */
export function register(data: { email: string; code: string; username: string; password: string; turnstile_token?: string }) {
  return request.post(`${BASE_URL}/register`, data)
}

/**
 * 重置密码
 */
export function resetPassword(data: { email: string; code: string; new_password: string; turnstile_token?: string }) {
  return request.post(`${BASE_URL}/reset-password`, data)
}

/**
 * 修改密码
 */
export function changePassword(data: { code: string; new_password: string }) {
  return request.post(`${BASE_URL}/change-password`, data)
}

/**
 * 获取安全配置
 */
export function getSecurityConfig() {
  return request.get(`${BASE_URL}/security-config`)
}

/**
 * 获取 Google OAuth URL
 */
export function getGoogleOAuthUrl(): string {
  const base = import.meta.env.VITE_API_BASE_URL || ''
  return `${base}/api/auth/oauth/google`
}

/**
 * 获取 GitHub OAuth URL
 */
export function getGitHubOAuthUrl(): string {
  const base = import.meta.env.VITE_API_BASE_URL || ''
  return `${base}/api/auth/oauth/github`
}
