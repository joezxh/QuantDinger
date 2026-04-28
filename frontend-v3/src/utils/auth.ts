import { TOKEN_KEY, USER_INFO_KEY } from '@/constants'

export interface UserInfo {
  id?: number
  username?: string
  email?: string
  timezone?: string
  roles?: string[]
  permissions?: string[]
  [key: string]: any
}

export function getToken(): string | null {
  try {
    return localStorage.getItem(TOKEN_KEY) || null
  } catch {
    return null
  }
}

export function setToken(token: string): void {
  try {
    localStorage.setItem(TOKEN_KEY, token)
  } catch {
    // ignore
  }
}

export function removeToken(): void {
  try {
    localStorage.removeItem(TOKEN_KEY)
  } catch {
    // ignore
  }
}

export function getUserInfo(): UserInfo | null {
  try {
    const info = localStorage.getItem(USER_INFO_KEY)
    if (!info) return null
    return JSON.parse(info)
  } catch {
    return null
  }
}

export function setUserInfo(info: UserInfo): void {
  try {
    localStorage.setItem(USER_INFO_KEY, JSON.stringify(info))
  } catch {
    // ignore
  }
}

export function removeUserInfo(): void {
  try {
    localStorage.removeItem(USER_INFO_KEY)
  } catch {
    // ignore
  }
}

export function clearAuth(): void {
  removeToken()
  removeUserInfo()
}

export function isAuthenticated(): boolean {
  return !!getToken()
}
