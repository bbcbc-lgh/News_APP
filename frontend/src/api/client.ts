// API 基础地址：从环境变量读取，开发环境留空（走 vite proxy），生产环境配置为后端域名
const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

interface ApiResponse<T> {
  code: number
  message: string
  data: T
}

export function getToken(): string | null {
  return localStorage.getItem('token')
}

function headers(auth = false): Record<string, string> {
  const h: Record<string, string> = { 'Content-Type': 'application/json' }
  if (auth) {
    const t = getToken()
    if (t) h['Authorization'] = t
  }
  return h
}

async function req<T>(url: string, init: RequestInit, auth = false): Promise<T> {
  const res = await fetch(`${API_BASE}${url}`, { ...init, headers: headers(auth) })
  const json: ApiResponse<T> = await res.json()
  if (json.code !== 200) throw new Error(json.message || '请求失败')
  return json.data
}

export const apiClient = {
  get<T>(url: string, auth = false) { return req<T>(url, { method: 'GET' }, auth) },
  post<T>(url: string, body?: unknown, auth = false) {
    return req<T>(url, { method: 'POST', body: body ? JSON.stringify(body) : undefined }, auth)
  },
  put<T>(url: string, body?: unknown, auth = false) {
    return req<T>(url, { method: 'PUT', body: body ? JSON.stringify(body) : undefined }, auth)
  },
  delete<T>(url: string, auth = false) { return req<T>(url, { method: 'DELETE' }, auth) }
}
