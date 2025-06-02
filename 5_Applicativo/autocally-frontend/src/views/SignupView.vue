<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-blue-100">
    <div class="max-w-md w-full space-y-8 bg-white p-10 rounded-2xl shadow-xl">
      <div class="flex flex-col items-center">
        <div class="w-32 h-32 relative mb-6">
          <img
            src="@/assets/img/logo.png"
            alt="AutoCally Logo"
            class="object-contain w-32 h-32"
          />
        </div>
        <h2 class="text-3xl font-semibold text-gray-900">Create your account</h2>
        <p class="mt-2 text-sm text-gray-600">
          Or
          <router-link to="/login" class="text-[#4285F4] hover:text-[#2b5cd9]">
            sign in to your account
          </router-link>
        </p>
      </div>

      <form @submit.prevent="handleSubmit" class="mt-8 space-y-6">
        <div v-if="error" class="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md text-sm">
          {{ error }}
        </div>

        <div class="space-y-4">
          <div>
            <label for="username" class="block text-sm font-medium text-gray-700">
              Username
            </label>
            <input
              id="username"
              v-model="username"
              name="username"
              type="text"
              required
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-[#4285F4] focus:border-[#4285F4] transition-colors"
            />
          </div>
          <div>
            <label for="email" class="block text-sm font-medium text-gray-700">
              Email address
            </label>
            <input
              id="email"
              v-model="email"
              name="email"
              type="email"
              required
              autocomplete="email"
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-[#4285F4] focus:border-[#4285F4] transition-colors"
            />
          </div>
          <div>
            <label for="password" class="block text-sm font-medium text-gray-700">
              Password
            </label>
            <input
              id="password"
              v-model="password"
              name="password"
              type="password"
              required
              autocomplete="new-password"
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-[#4285F4] focus:border-[#4285F4] transition-colors"
            />
          </div>
        </div>

        <button
          type="submit"
          :disabled="isLoading"
          class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-[#4285F4] hover:bg-[#2b5cd9] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#4285F4] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span v-if="isLoading">Creating account...</span>
          <span v-else>Create account</span>
        </button>
      </form>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import axios from 'axios'
import { API_URL } from '@/services/api'

const router = useRouter()
const authStore = useAuthStore()

const username = ref('')
const email = ref('')
const password = ref('')
const error = ref('')
const isLoading = ref(false)

const handleSubmit = async () => {
  try {
    error.value = ''
    isLoading.value = true

    if (!username.value || !email.value || !password.value) {
      throw new Error('Please fill in all fields')
    }

    // Register the user
    const registerResponse = await axios.post(`${API_URL}/security/create_user`, {
      username: username.value,
      email: email.value,
      password: password.value
    })

    if (registerResponse.status !== 201) {
      throw new Error('Registration failed')
    }

    // After successful registration, log the user in
    const loginResponse = await axios.post(`${API_URL}/security/login`, {
      username: username.value,
      password: password.value
    }, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    })

    const { token, user } = loginResponse.data

    if (!token) {
      throw new Error('Login failed after registration')
    }

    // Store the token and user info
    authStore.setAuth(token, user)
    
    // Redirect to home page
    router.push('/')
  } catch (err: any) {
    if (err.response?.data?.errors) {
      // Handle validation errors from the backend
      const errors = err.response.data.errors
      error.value = Object.values(errors).flat().join(', ')
    } else {
      error.value = err instanceof Error ? err.message : 'An error occurred'
    }
    console.error('Registration failed:', err)
  } finally {
    isLoading.value = false
  }
}
</script> 