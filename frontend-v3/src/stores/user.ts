import { defineStore } from 'pinia'
import { ref } from 'vue'
import { login as loginApi, getUserInfo as getUserInfoApi, logout as logoutApi } from '@/api/auth'
import { setToken, clearAuth } from '@/utils/request'
import type { UserInfo, LoginParams, LoginResult } from '@/types/api'

export const useUserStore = defineStore('user', () => {
  const token = ref<string>('')
  const userInfo = ref<UserInfo | null>(null)
  const roles = ref<string[]>([])
  const permissions = ref<string[]>([])

  /**
   * 登录
   */
  async function login(params: LoginParams): Promise<LoginResult> {
    const res = await loginApi(params)
    const result = res?.data as LoginResult | undefined
    const accessToken = result?.token ?? (res as any)?.token ?? null
    if (!accessToken) throw new Error('登录成功但未返回有效 token')

    token.value = accessToken
    setToken(accessToken)

    // Set user info if returned
    if (result?.userinfo) {
      userInfo.value = result.userinfo
      normalizeAndSetRoles(result.userinfo)
    }

    return result ?? { token: accessToken }
  }

  /**
   * 获取用户信息
   */
  async function fetchUserInfo(): Promise<UserInfo> {
    const res = await getUserInfoApi()
    const info = res?.data as UserInfo | undefined
    if (!info) throw new Error('获取用户信息失败')

    userInfo.value = info
    normalizeAndSetRoles(info)
    return info
  }

  /**
   * 登出
   */
  async function logout(): Promise<void> {
    try {
      await logoutApi()
    } catch {
      // Continue even if logout API fails
    }
    token.value = ''
    userInfo.value = null
    roles.value = []
    permissions.value = []
    clearAuth()
  }

  /**
   * Normalize and set roles from user info
   */
  function normalizeAndSetRoles(info: UserInfo): void {
    const rawRoles = info.role || (info as any).roles
    if (!rawRoles) {
      roles.value = ['default']
      return
    }

    if (Array.isArray(rawRoles)) {
      roles.value = rawRoles.map(r => typeof r === 'string' ? r : r.id)
    } else if (typeof rawRoles === 'object') {
      roles.value = [rawRoles.id]
      // Set permissions if available
      if (rawRoles.permissions) {
        permissions.value = rawRoles.permissions
      }
    } else {
      roles.value = [rawRoles]
    }

    // Set direct permissions if available
    if (info.permissions && Array.isArray(info.permissions)) {
      permissions.value = info.permissions
    }
  }

  /**
   * Check if user has permission
   */
  function hasPermission(required: string | string[], mode: 'OR' | 'AND' = 'OR'): boolean {
    // Super admin has all permissions
    if (roles.value.includes('*') || permissions.value.includes('*:*')) return true

    if (typeof required === 'string') {
      return permissions.value.some(p => p === required || p.startsWith(required.split(':')[0] + ':'))
    }

    if (mode === 'AND') {
      return required.every(r => permissions.value.some(p => p === r || p.startsWith(r.split(':')[0] + ':')))
    }

    return required.some(r => permissions.value.some(p => p === r || p.startsWith(r.split(':')[0] + ':')))
  }

  return {
    token,
    userInfo,
    roles,
    permissions,
    login,
    fetchUserInfo,
    logout,
    hasPermission,
  }
})
