import { apiClient } from './client'

export interface UserInfo {
  id: number
  username: string
  nickname: string | null
  avatar: string | null
  gender: 'male' | 'female' | 'unknown'
  bio: string | null
  phone?: string | null
}

export interface AuthData {
  token: string
  userInfo: UserInfo
}

export const userApi = {
  login: (username: string, password: string) =>
    apiClient.post<AuthData>('/api/user/login', { username, password }),

  register: (username: string, password: string) =>
    apiClient.post<AuthData>('/api/user/register', { username, password }),

  getInfo: () =>
    apiClient.get<UserInfo>('/api/user/info', true),

  update: (data: Partial<Pick<UserInfo, 'nickname' | 'avatar' | 'gender' | 'bio' | 'phone'>>) =>
    apiClient.put<UserInfo>('/api/user/update', data, true),

  changePassword: (oldPassword: string, newPassword: string) =>
    apiClient.put<null>('/api/user/password', { oldPassword, newPassword }, true),

  // 登出，让服务端 token 立即失效
  logout: () =>
    apiClient.post<null>('/api/user/logout', undefined, true),

  // 上传头像：将 File 转为 base64 data URI 后提交（无需 multipart）
  uploadAvatar: async (file: File): Promise<{ avatar: string }> => {
    const base64 = await new Promise<string>((resolve, reject) => {
      const reader = new FileReader()
      reader.onload = () => resolve(reader.result as string)
      reader.onerror = reject
      reader.readAsDataURL(file)
    })
    return apiClient.post<{ avatar: string }>('/api/user/avatar', { image: base64 }, true)
  }
}
