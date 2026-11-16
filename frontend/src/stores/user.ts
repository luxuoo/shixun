import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi } from '@/api'

interface User {
  id: number
  username: string
  name: string
  role: string
  email?: string
  class_id?: number
  student_id?: string
}

export const useUserStore = defineStore('user', () => {
  const token = ref<string>(localStorage.getItem('token') || '')
  const user = ref<User | null>(null)
  const loading = ref(false)
  const lastError = ref('')

  const isLoggedIn = computed(() => !!token.value)
  const isAdmin = computed(() => user.value?.role === 'admin')
  const isTeacher = computed(() => user.value?.role === 'teacher' || user.value?.role === 'admin')
  const isStudent = computed(() => user.value?.role === 'student')

  async function login(username: string, password: string) {
    const data = await authApi.login({ username, password }) as any
    token.value = data.access_token
    localStorage.setItem('token', data.access_token)
    await fetchUser()
    return data
  }

  async function fetchUser() {
    if (loading.value) return
    loading.value = true
    try {
      const data = await authApi.getMe() as any
      user.value = data
      lastError.value = ''
    } catch (error: any) {
      // 关键：只有 401 才算登录失效。发布时服务会重启几秒，
      // 期间 /auth/me 会 502 —— 之前这里一律清 token，导致「更新完被踢回登录页」。
      if (error?.status === 401) {
        token.value = ''
        user.value = null
        localStorage.removeItem('token')
        lastError.value = '登录已过期，请重新登录'
      } else {
        lastError.value = error?.detail || '暂时无法连接服务器'
        // 保留 token 与已缓存的用户信息，页面继续可用
      }
    } finally {
      loading.value = false
    }
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
  }

  return {
    token,
    user,
    loading,
    isLoggedIn,
    isAdmin,
    isTeacher,
    isStudent,
    lastError,
    login,
    fetchUser,
    logout
  }
})
