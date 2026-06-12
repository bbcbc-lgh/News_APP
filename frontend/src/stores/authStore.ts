import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { userApi, type UserInfo } from '@/api/user'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const userInfo = ref<UserInfo | null>(null)

  const isLoggedIn = computed(() => !!token.value)

  function setAuth(t: string, info: UserInfo) {
    token.value = t
    userInfo.value = info
    localStorage.setItem('token', t)
  }

  async function login(username: string, password: string) {
    const data = await userApi.login(username, password)
    setAuth(data.token, data.userInfo)
  }

  async function register(username: string, password: string) {
    const data = await userApi.register(username, password)
    setAuth(data.token, data.userInfo)
  }

  async function fetchInfo() {
    userInfo.value = await userApi.getInfo()
  }

  async function updateInfo(data: Parameters<typeof userApi.update>[0]) {
    userInfo.value = await userApi.update(data)
  }

  // 登出：通知服务端使 token 失效，再清除本地状态
  async function logout() {
    try {
      await userApi.logout()
    } catch (_) {
      // token 已过期或网络异常时忽略错误，直接清除本地状态
    }
    token.value = null
    userInfo.value = null
    localStorage.removeItem('token')
  }

  return { token, userInfo, isLoggedIn, login, register, fetchInfo, updateInfo, logout }
})
