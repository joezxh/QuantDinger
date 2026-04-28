/**
 * API 通用类型定义
 */

/** 统一响应格式 */
export interface ApiResponse<T = unknown> {
  code: number
  message: string
  data: T
}

/** 分页查询参数 */
export interface PageParams {
  page?: number
  pageSize?: number
  [key: string]: unknown
}

/** 分页响应数据 */
export interface PageData<T = unknown> {
  list: T[]
  total: number
  page: number
  pageSize: number
}

/** 字典项 */
export interface DictionaryItem {
  item_code: string
  item_name: string
  color?: string
  sort_order?: number
}

/** 用户信息 */
export interface UserInfo {
  id: string | number
  username?: string
  nickname?: string
  avatar?: string
  email?: string
  role?: {
    id: string
    permissions?: string[]
  }
  permissions?: string[]
  is_demo?: boolean
}

/** 登录请求参数 */
export interface LoginParams {
  username: string
  password: string
  turnstile_token?: string
}

/** 登录响应数据 */
export interface LoginResult {
  token: string
  userinfo?: UserInfo
  is_new_user?: boolean
}
