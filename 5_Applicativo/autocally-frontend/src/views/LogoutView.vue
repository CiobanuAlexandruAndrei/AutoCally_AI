<script setup lang="ts">
import { onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'

const router = useRouter()
const authStore = useAuthStore()

onMounted(() => {
  // Clear authentication
  authStore.clearAuth()
  
  // Redirect to login after a brief delay
  setTimeout(() => {
    router.push('/login')
  }, 2000)
})
</script>

<template>
  <div class="min-h-screen flex items-center justify-center bg-gradient-to-br from-blue-50 to-blue-100">
    <div class="text-center">
      <div class="w-32 h-32 mx-auto mb-6 relative">
        <img
          src="@/assets/img/logo.png"
          alt="AutoCally Logo"
          class="w-full h-full object-contain"
        />
      </div>
      <h2 class="text-2xl font-semibold text-gray-900 mb-2">
        Logging you out...
      </h2>
      <p class="text-gray-600">
        Thank you for using AutoCally
      </p>
    </div>
  </div>
</template> 