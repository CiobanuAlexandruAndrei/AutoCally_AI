<script setup lang="ts">
import { ref, onMounted } from 'vue'
import PhoneNumberEmptyState from '@/components/PhoneNumberEmptyState.vue'
import TwilioConfigForm from '@/components/TwilioConfigForm.vue'
import PhoneNumberList from '@/components/PhoneNumberList.vue'
import { phoneNumbersApi } from '@/services/api'

interface TwilioConfig {
  accountSid: string
  authToken: string
  phoneNumber: string
}

interface PhoneNumber {
  number: string
  usedBy?: string
  spent: number
  lastCall: string
  totalCalls: number
  avgDuration: string
  successRate: number
}

/*
const numbers = ref<PhoneNumber[]>([
  {
    number: '+41 79 123 45 67',
    usedBy: 'Italian Assistant',
    spent: 125.50,
    lastCall: '2024-03-15 14:30',
    totalCalls: 1250,
    avgDuration: '2m 45s',
    successRate: 98.5
  },
  {
    number: '+41 78 987 65 43',
    spent: 85.75,
    lastCall: '2024-03-14 16:15',
    totalCalls: 850,
    avgDuration: '3m 10s',
    successRate: 95.2
  },
  {
    number: '+41 76 555 44 33',
    usedBy: 'German Assistant',
    spent: 250.25,
    lastCall: '2024-03-15 09:45',
    totalCalls: 2100,
    avgDuration: '1m 55s',
    successRate: 99.1
  }
])*/

const numbers = ref<PhoneNumber[]>([])
const isLoading = ref(true)
const error = ref<string | null>(null)

const isImporting = ref(false)
const showConfigForm = ref(false)

const handleImport = () => {
  showConfigForm.value = true
}

const handleCancel = () => {
  showConfigForm.value = false
}

const handleSave = async (config: TwilioConfig) => {
  isImporting.value = true
  try {
    const response = await phoneNumbersApi.importFromTwilio(config)
    numbers.value.push({
      number: response.phone_number,
      spent: 0,
      lastCall: '-',
      totalCalls: 0,
      avgDuration: '0m 0s',
      successRate: 0
    })
    showConfigForm.value = false
  } catch (error) {
    console.error('Failed to import numbers:', error)
    // You might want to add error handling UI here
  } finally {
    isImporting.value = false
  }
}

onMounted(async () => {
  try {
    const response = await phoneNumbersApi.getAll()
    numbers.value = response.map((phone: any) => ({
      number: phone.phone_number,
      spent: 0,
      lastCall: '-',
      totalCalls: 0,
      avgDuration: '0m 0s',
      successRate: 0
    }))
  } catch (err) {
    console.error('Failed to fetch phone numbers:', err)
    error.value = 'Failed to load phone numbers'
  } finally {
    isLoading.value = false
  }
})
</script>

<template>
  <template v-if="isLoading">
    <div class="h-full flex items-center justify-center">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-[#4285F4]"></div>
    </div>
  </template>
  <template v-else-if="error">
    <div class="h-full flex items-center justify-center">
      <div class="text-red-500">{{ error }}</div>
    </div>
  </template>
  <template v-else-if="showConfigForm">
    <TwilioConfigForm :onSave="handleSave" :onCancel="handleCancel" />
  </template>
  <template v-else-if="numbers.length === 0">
    <PhoneNumberEmptyState :onImport="handleImport" :isImporting="isImporting" />
  </template>
  <template v-else>
    <PhoneNumberList :numbers="numbers" @addNumber="handleImport" />
  </template>
</template> 