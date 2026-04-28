import request from '@/utils/request'

export function getProfile() {
  return request.get<any>('/api/users/profile')
}

export function updateProfile(data: Record<string, any>) {
  return request.put<any>('/api/users/profile/update', data)
}

export function changePassword(data: { old_password: string; new_password: string }) {
  return request.post<any>('/api/users/change-password', data)
}

export function getReferralData() {
  return request.get<any>('/api/users/referral')
}

export function getBillingInfo() {
  return request.get<any>('/api/users/billing')
}
