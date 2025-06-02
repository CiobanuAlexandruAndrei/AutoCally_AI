<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '@/stores/auth'
import {
    Bot,
    Phone,
    Hash,
    FileText,
    Users,
    Bell,
    Settings,
    Wrench,
    Menu,
    X,
    LogOut,
    User
} from 'lucide-vue-next'

const router = useRouter()
const authStore = useAuthStore()
const isSidebarOpen = ref(false)

const handleLogout = () => {
  router.push('/logout')
}

// Navigation items with icon components
const navItems = [
    { icon: Bot, label: 'Assistants', path: '/' },
    { icon: Phone, label: 'Calls', path: '/calls' },
    { icon: Hash, label: 'Phone numbers', path: '/phone-numbers' },
    { icon: FileText, label: 'Knowledge Base', path: '/knowledge-base' },
    {
        icon: Wrench,
        label: 'Tools',
        path: '/tools',
        subItems: [
            { label: 'Notepad', path: '/tools/notepad' },
            { label: 'Calendar', path: '/tools/calendar' },
            { label: 'External services', path: '/tools/external-services' }
        ]
    }
]
</script>

<template>
  <div class="h-full bg-gray-50">
    <div class="flex h-full">
      <!-- Mobile Menu Button -->
      <button 
        @click="isSidebarOpen = !isSidebarOpen"
        class="lg:hidden fixed top-4 left-4 z-50 p-2 rounded-lg bg-white shadow-md text-gray-600 hover:text-blue-600"
      >
        <Menu v-if="!isSidebarOpen" class="w-6 h-6" />
        <X v-else class="w-6 h-6" />
      </button>

      <!-- Left Navigation -->
      <div 
        :class="[
          'fixed top-0 left-0 h-full w-72 bg-white shadow-md transform transition-transform duration-300 ease-in-out z-40',
          isSidebarOpen ? 'translate-x-0' : '-translate-x-full lg:translate-x-0'
        ]"
      >
        <div class="flex flex-col h-full">
          <!-- Top Section -->
          <div class="p-6">
            <div class="flex items-center mb-8">
              <div class="w-32 mx-auto flex flex-col items-center justify-center p-3">
                <img src="@/assets/img/logo.png" alt="AutoCally Logo" class="w-full h-auto" />
                <span class="mt-2 text-lg font-semibold text-gray-800">AutoCally</span>
              </div>
            </div>

            <nav class="space-y-1">
              <div v-for="item in navItems" :key="item.label">
                <router-link 
                  :to="item.path"
                  @click="isSidebarOpen = false"
                  class="w-full px-4 py-3 text-left text-sm text-gray-600 hover:bg-gray-50 hover:text-blue-600 transition-colors flex items-center gap-3 focus:outline-none focus:ring-2 focus:ring-blue-200"
                >
                  <component :is="item.icon" class="w-5 h-5" />
                  {{ item.label }}
                </router-link>
                <!-- Sub-items -->
                <div v-if="item.subItems" class="ml-8 space-y-1 mt-1">
                  <router-link 
                    v-for="subItem in item.subItems" 
                    :key="subItem.label"
                    :to="subItem.path"
                    @click="isSidebarOpen = false"
                    class="w-full px-4 py-2 text-left text-sm text-gray-500 hover:text-blue-600 transition-colors focus:outline-none focus:ring-2 focus:ring-blue-200 block"
                  >
                    {{ subItem.label }}
                  </router-link>
                </div>
              </div>
            </nav>
          </div>

          <!-- Bottom Section -->
          <div class="mt-auto border-t border-gray-100">
            <!-- User Profile Section with Sign Out -->
            <div class="p-4 m-4 bg-gray-50 rounded-xl">
              <div class="flex items-center justify-between">
                <!-- User Info -->
                <div class="flex items-center gap-3">
                  <div class="w-10 h-10 rounded-full bg-blue-100 flex items-center justify-center">
                    <User class="w-5 h-5 text-blue-600" />
                  </div>
                  <div class="flex flex-col">
                    <span class="text-sm font-medium text-gray-900">{{ authStore.username }}</span>
                    <span class="text-xs text-gray-500">User Account</span>
                  </div>
                </div>
                
                <!-- Sign Out Button -->
                <button 
                  @click="handleLogout"
                  class="p-2 text-gray-600 hover:text-red-600 transition-all rounded-lg group"
                >
                  <LogOut class="w-5 h-5 transition-transform group-hover:-translate-x-1" />
                </button>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Overlay -->
      <div 
        v-if="isSidebarOpen" 
        class="fixed inset-0 bg-black bg-opacity-50 z-30 lg:hidden"
        @click="isSidebarOpen = false"
      ></div>

      <!-- Main Content -->
      <div class="flex-1 ml-0 lg:ml-72 h-full overflow-hidden">
        <slot></slot>
      </div>
    </div>
  </div>
</template>