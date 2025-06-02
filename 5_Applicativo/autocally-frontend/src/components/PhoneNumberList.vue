<script setup lang="ts">
import { ref } from 'vue'
import { BarChart3, ChevronRight, Phone, Bot, Plus } from 'lucide-vue-next'

interface PhoneNumber {
  number: string
  usedBy?: string
  spent: number
  lastCall: string
  totalCalls: number
  avgDuration: string
  successRate: number
}

defineProps<{
  numbers: PhoneNumber[]
}>()

const emit = defineEmits(['addNumber'])

const expandedNumber = ref<string | null>(null)

const toggleExpand = (number: string) => {
  expandedNumber.value = expandedNumber.value === number ? null : number
}

const handleAddNumber = () => {
  emit('addNumber')
}
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- Header -->
    <div class="px-8 pt-6">
      <div class="flex justify-between items-center mb-4">
        <h1 class="text-2xl font-bold text-gray-900">Phone Numbers</h1>
        <div class="flex items-center gap-3">
          <button
            class="px-4 py-2 bg-white border border-gray-200 rounded-xl text-sm font-medium text-gray-600 hover:border-[#4285F4] hover:text-[#4285F4] transition-colors flex items-center gap-2"
          >
            <BarChart3 class="w-4 h-4" />
            View Analytics
          </button>
          <button
            @click="handleAddNumber"
            class="px-4 py-2 bg-[#4285F4] text-white rounded-xl flex items-center gap-2 hover:bg-[#3367d6] transition-colors"
          >
            <Plus class="w-4 h-4" />
            Add New Number
          </button>
        </div>
      </div>
    </div>

    <!-- Numbers List -->
    <div class="flex-1 px-8 overflow-y-auto">
      <div class="space-y-3 py-6">
        <div
          v-for="number in numbers"
          :key="number.number"
          class="bg-white rounded-xl p-4 border border-gray-200 hover:border-[#4285F4] transition-colors cursor-pointer"
        >
          <div
            class="flex items-center justify-between"
            @click="toggleExpand(number.number)"
          >
            <div class="flex items-center gap-4">
              <div class="w-10 h-10 bg-[#4285F4]/10 rounded-full flex items-center justify-center">
                <Phone class="w-5 h-5 text-[#4285F4]" />
              </div>
              <div>
                <p class="font-medium text-gray-900">{{ number.number }}</p>
                <div class="flex items-center gap-2 mt-1">
                  <template v-if="number.usedBy">
                    <div class="flex items-center gap-1.5 px-2 py-0.5 bg-[#4285F4]/10 rounded-full">
                      <Bot class="w-4 h-4 text-[#4285F4]" />
                      <span class="text-xs font-medium text-[#4285F4]">{{ number.usedBy }}</span>
                    </div>
                  </template>
                  <span v-else class="text-xs text-gray-500 px-2 py-0.5 bg-gray-100 rounded-full">
                    Not used
                  </span>
                </div>
              </div>
            </div>
            <div class="flex items-center gap-4">
              <div class="text-right">
                <span class="font-medium text-[#4285F4]">{{ number.spent.toFixed(2) }} CHF</span>
                <p class="text-xs text-gray-500">spent</p>
              </div>
              <ChevronRight
                :class="[
                  'w-5 h-5 text-gray-400 transition-transform',
                  { 'rotate-90': expandedNumber === number.number }
                ]"
              />
            </div>
          </div>

          <!-- Expanded Details -->
          <div v-if="expandedNumber === number.number" class="mt-4 pt-4 border-t border-gray-100">
            <div class="grid grid-cols-2 gap-4">
              <div class="space-y-1">
                <p class="text-sm text-gray-500">Last call</p>
                <p class="text-sm font-medium text-gray-900">{{ number.lastCall }}</p>
              </div>
              <div class="space-y-1">
                <p class="text-sm text-gray-500">Total calls</p>
                <p class="text-sm font-medium text-gray-900">{{ number.totalCalls }}</p>
              </div>
              <div class="space-y-1">
                <p class="text-sm text-gray-500">Average duration</p>
                <p class="text-sm font-medium text-gray-900">{{ number.avgDuration }}</p>
              </div>
              <div class="space-y-1">
                <p class="text-sm text-gray-500">Success rate</p>
                <p class="text-sm font-medium text-gray-900">{{ number.successRate }}%</p>
              </div>
            </div>
            <button
              class="mt-4 w-full px-4 py-2 bg-[#4285F4] text-white text-sm font-medium rounded-lg hover:bg-[#3367d6] transition-colors"
            >
              View Detailed Analytics
            </button>
          </div>
        </div>
      </div>
    </div>
  </div>
</template> 
  