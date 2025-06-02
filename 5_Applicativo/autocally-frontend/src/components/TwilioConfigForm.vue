<script setup lang="ts">
import { ref } from 'vue'

interface TwilioConfig {
  accountSid: string
  authToken: string
  phoneNumber: string
}

const props = defineProps<{
  onSave: (config: TwilioConfig) => void
  onCancel: () => void
}>()

const config = ref<TwilioConfig>({
  accountSid: '',
  authToken: '',
  phoneNumber: ''
})

const handleSubmit = (e: Event) => {
  e.preventDefault()
  props.onSave(config.value)
}
</script>

<template>
  <div class="min-h-screen bg-gradient-to-br from-gray-50 to-white flex items-center justify-center p-6">
    <div class="relative w-full max-w-md">
      <div class="absolute inset-0 bg-[#4285F4] rounded-2xl blur-2xl opacity-5 transform rotate-3" />
      <div class="relative bg-white border border-gray-200 rounded-2xl shadow-xl shadow-blue-50/50 p-8">
        <div class="flex items-center justify-between border-b border-gray-100 pb-6 mb-6">
          <div class="space-y-1">
            <h2 class="text-xl font-semibold text-gray-900">Import from Twilio</h2>
            <p class="text-sm text-gray-500">Enter your Twilio credentials</p>
          </div>
          <div class="relative w-12 h-12">
            <div class="absolute inset-0 bg-blue-50 rounded-xl rotate-6" />
            <div class="absolute inset-0 bg-[#4285F4]/10 rounded-xl -rotate-6" />
            <div class="relative w-full h-full flex items-center justify-center">
              <img src="@/assets/img/twilio.png" alt="" class="w-8 h-8 opacity-80" />
            </div>
          </div>
        </div>

        <form @submit="handleSubmit" class="space-y-5">
          <div class="space-y-1">
            <label class="block text-sm font-medium text-gray-700">Account SID</label>
            <input
              v-model="config.accountSid"
              type="text"
              placeholder="AC123..."
              class="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:border-[#4285F4] focus:ring-2 focus:ring-[#4285F4]/20 transition-all"
              required
            />
          </div>

          <div class="space-y-1">
            <label class="block text-sm font-medium text-gray-700">Auth Token</label>
            <input
              v-model="config.authToken"
              type="password"
              placeholder="••••••••"
              class="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:border-[#4285F4] focus:ring-2 focus:ring-[#4285F4]/20 transition-all"
              required
            />
          </div>

          <div class="space-y-1">
            <label class="block text-sm font-medium text-gray-700">Phone Number</label>
            <input
              v-model="config.phoneNumber"
              type="tel"
              placeholder="+1234567890"
              class="w-full px-4 py-2.5 bg-gray-50 border border-gray-200 rounded-xl text-sm focus:outline-none focus:border-[#4285F4] focus:ring-2 focus:ring-[#4285F4]/20 transition-all"
              required
            />
          </div>

          <div class="flex justify-end gap-3 pt-2">
            <button
              type="button"
              @click="onCancel"
              class="px-5 py-2.5 text-sm font-medium text-gray-600 hover:text-gray-900 transition-colors"
            >
              Cancel
            </button>
            <button
              type="submit"
              class="group relative px-5 py-2.5 bg-[#4285F4] text-sm font-medium text-white rounded-xl hover:bg-[#3367d6] transition-colors"
            >
              Import
              <span
                class="absolute inset-0 rounded-xl bg-white opacity-0 group-hover:opacity-10 blur transition-opacity"
              />
            </button>
          </div>
        </form>
      </div>
    </div>
  </div>
</template> 