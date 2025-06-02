import { ref } from 'vue'
import { defineStore } from 'pinia'
import { connectSocket, disconnectSocket } from '@/services/socket'

export const useAuthStore = defineStore('auth', () => {
  const token = ref<string | null>(localStorage.getItem('token'))
  const username = ref<string | null>(localStorage.getItem('username'))
  const isAuthenticated = ref(!!token.value)

  function setAuth(newToken: string, newUsername: string) {
    token.value = newToken
    username.value = newUsername
    isAuthenticated.value = true
    localStorage.setItem('token', newToken)
    localStorage.setItem('username', newUsername)
    connectSocket(newToken)
  }

  function clearAuth() {
    token.value = null
    username.value = null
    isAuthenticated.value = false
    localStorage.removeItem('token')
    localStorage.removeItem('username')
    disconnectSocket()
  }

  return {
    token,
    username,
    isAuthenticated,
    setAuth,
    clearAuth
  }
}) 