import request from '@/utils/request'

const BASE_URL = '/api/billing'

export function getMembershipPlans() {
  return request.get<any>(`${BASE_URL}/plans`)
}

export function createUsdtOrder(plan: string) {
  return request.post<any>(`${BASE_URL}/usdt-order`, { plan })
}

export function getUsdtOrder(orderId: string, checkPayment: boolean = false) {
  return request.get<any>(`${BASE_URL}/usdt-order/${orderId}`, {
    params: { check_payment: checkPayment },
  })
}
