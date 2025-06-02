<script setup lang="ts">
defineProps<{
  onImport: () => void
  isImporting: boolean
}>()
</script>

<template>
  <div class="h-full w-full flex items-start justify-center bg-white pt-40">
    <div class="relative w-full max-w-5xl mx-auto px-6">
      <div class="bg-gradient-to-br from-gray-50 to-white py-20 rounded-2xl border border-gray-100 shadow-sm">
        <div class="flex flex-col items-center justify-center space-y-8">
          <div class="relative w-24 h-24 mb-4">
            <div class="absolute inset-0 bg-blue-50 rounded-3xl rotate-6 transform-gpu transition-transform group-hover:rotate-12" />
            <div class="absolute inset-0 bg-[#4285F4]/10 rounded-3xl -rotate-6 transform-gpu transition-transform group-hover:-rotate-12" />
            <div class="relative w-full h-full flex items-center justify-center">
              <img src="@/assets/img/twilio.png" alt="" class="w-12 h-12 transform-gpu transition-transform hover:scale-110" />
            </div>
          </div>

          <div class="text-center space-y-4">
            <h1 class="text-2xl font-semibold text-gray-900">No phone numbers imported</h1>
            <p class="text-gray-500 max-w-md mx-auto">
              Import your Twilio phone numbers to start making calls and managing your communication
            </p>
          </div>

          <button
            @click="onImport"
            :disabled="isImporting"
            class="group relative inline-flex items-center gap-2 px-6 py-3 bg-white border border-gray-200 rounded-xl text-sm font-medium text-gray-700 hover:border-gray-300 hover:shadow-lg hover:shadow-blue-50/50 transition-all duration-300 disabled:opacity-50"
          >
            <div class="relative w-5 h-5">
              <img
                src="@/assets/img/twilio.png"
                alt=""
                class="w-5 h-5 opacity-80 group-hover:opacity-100 transition-opacity"
              />
            </div>
            <span class="relative">{{ isImporting ? 'Importing...' : 'Import from Twilio' }}</span>
            <span
              class="absolute inset-0 rounded-xl bg-gradient-to-r from-[#4285F4]/0 via-[#4285F4]/5 to-[#4285F4]/0 opacity-0 group-hover:opacity-100 blur transition-opacity"
            />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<style scoped>
/* Remove the slide animation as it's no longer needed */
</style> 