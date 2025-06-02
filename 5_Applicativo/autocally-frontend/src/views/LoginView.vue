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
        <h2 class="text-3xl font-semibold text-gray-900">Sign in to AutoCally</h2>
        <p class="mt-2 text-sm text-gray-600">
          Or
          <router-link to="/signup" class="text-[#4285F4] hover:text-[#2b5cd9]">
            create a new account
          </router-link>
        </p>
      </div>

      <form @submit.prevent="handleSubmit" class="mt-8 space-y-6">
        <div v-if="error" class="bg-red-50 border border-red-200 text-red-600 px-4 py-3 rounded-md text-sm">
          {{ error }}
        </div>

        <div class="space-y-4">
          <div>
            <label for="email" class="block text-sm font-medium text-gray-700">
              Username or Email address
            </label>
            <input
              id="email"
              v-model="email"
              name="email"
              type="text"
              required
              autocomplete="username"
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
              autocomplete="current-password"
              required
              class="mt-1 block w-full px-3 py-2 border border-gray-300 rounded-md shadow-sm focus:outline-none focus:ring-[#4285F4] focus:border-[#4285F4] transition-colors"
            />
          </div>
        </div>

        <button
          type="submit"
          :disabled="isLoading"
          class="w-full flex justify-center py-2 px-4 border border-transparent rounded-md shadow-sm text-sm font-medium text-white bg-[#4285F4] hover:bg-[#2b5cd9] focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-[#4285F4] transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
        >
          <span v-if="isLoading">Signing in...</span>
          <span v-else>Sign in</span>
        </button>
      </form>

      <div class="mt-6">
        <div class="relative">
          <div class="absolute inset-0 flex items-center">
            <div class="w-full border-t border-gray-300" />
          </div>
          <div class="relative flex justify-center text-sm">
            <span class="px-2 bg-white text-gray-500">Or continue with</span>
          </div>
        </div>

        <div class="mt-6">
          <button
            type="button"
            @click="signInWithGoogle"
            class="w-full inline-flex justify-center items-center gap-3 py-2 px-4 border border-gray-300 rounded-md shadow-sm bg-white text-sm font-medium text-gray-500 hover:bg-gray-50 transition-colors"
          >
            <img src="@/assets/img/google.png" alt="Google" class="w-5 h-5" />
            Google
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import axiosInstance from '@/services/api'

const router = useRouter()
const authStore = useAuthStore()

const email = ref('')
const password = ref('')
const error = ref('')
const isLoading = ref(false)

const handleSubmit = async () => {
  try {
    error.value = ''
    isLoading.value = true

    if (!email.value || !password.value) {
      throw new Error('Please fill in all fields')
    }

    // Create form data
    const formData = new FormData()
    formData.append('username', email.value)
    formData.append('password', password.value)

    const response = await axiosInstance.post('/security/login', formData, {
      headers: {
        'Content-Type': 'application/x-www-form-urlencoded'
      }
    })

    const { token, user } = response.data

    if (!token) {
      throw new Error('Login failed')
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
    console.error('Login failed:', err)
  } finally {
    isLoading.value = false
  }
}

const signInWithGoogle = () => {
  // Handle Google sign-in
}
</script>
