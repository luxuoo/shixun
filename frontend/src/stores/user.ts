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
    } catch (error) {
      token.value = ''
      user.value = null
      localStorage.removeItem('token')
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
    login,
    fetchUser,
    logout
  }
})
