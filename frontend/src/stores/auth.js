import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import * as authApi from '../api/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const email = ref(localStorage.getItem('email') || '')

  const isLoggedIn = computed(() => !!token.value)

  function setSession(accessToken, userEmail = '') {
    token.value = accessToken
    email.value = userEmail
    localStorage.setItem('token', accessToken)
    if (userEmail) localStorage.setItem('email', userEmail)
  }

  function logout() {
    token.value = ''
    email.value = ''
    localStorage.removeItem('token')
    localStorage.removeItem('email')
  }

  async function login(emailInput, password) {
    const { data } = await authApi.login(emailInput, password)
    setSession(data.access_token, emailInput)
  }

  async function register(emailInput, password) {
    await authApi.register(emailInput, password)
    await login(emailInput, password)
  }

  return { token, email, isLoggedIn, login, register, logout }
})
