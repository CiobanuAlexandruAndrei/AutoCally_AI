<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white rounded-xl w-full max-w-md p-6">
      <div class="flex justify-between items-center mb-6">
        <h2 class="text-lg font-medium">Configure Phone Number</h2>
        <button @click="emit('close')" class="text-gray-400 hover:text-gray-600">
          <X class="w-5 h-5" />
        </button>
      </div>

      <div v-if="phoneNumbers.length === 0" class="text-center py-8">
        <div class="w-16 h-16 bg-blue-50 rounded-full flex items-center justify-center mx-auto mb-4">
          <Hash class="w-8 h-8 text-blue-600" />
        </div>
        <h3 class="text-lg font-medium mb-2">No Phone Numbers Available</h3>
        <p class="text-gray-500 mb-4">You need to import phone numbers first</p>
        <button
          @click="goToPhoneNumbers"
          class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
        >
          Import Phone Numbers
        </button>
      </div>

      <div v-else>
        <div class="mb-6">
          <label class="block text-sm font-medium text-gray-700 mb-2">Select Phone Number</label>
          <select
            v-model="selectedNumber"
            class="w-full px-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="" disabled>Choose a phone number</option>
            <option v-for="number in phoneNumbers" :key="number.id" :value="number.id">
              {{ number.phone_number }}
            </option>
          </select>
        </div>

        <div class="flex justify-end gap-3">
          <button
            @click="emit('close')"
            class="px-4 py-2 text-gray-600 hover:text-gray-900 transition-colors"
          >
            Cancel
          </button>
          <button
            @click="handleSave"
            :disabled="!selectedNumber"
            class="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors disabled:opacity-50"
          >
            Save
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { X, Hash } from 'lucide-vue-next'
import { testCallsApi } from '@/services/api'

interface PhoneNumber {
  id: number;
  phone_number: string;
  assistants: Array<{
    id: string;
    name: string;
  }>;
}

const router = useRouter()
const phoneNumbers = ref<PhoneNumber[]>([])
const selectedNumber = ref('')

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'save', phoneNumberId: string): void
}>()

const goToPhoneNumbers = () => {
  router.push('/phone-numbers')
}

const handleSave = () => {
  emit('save', selectedNumber.value)
  emit('close')
}

onMounted(async () => {
  try {
    const response = await testCallsApi.getAvailablePhoneNumbers()
    if (response.status === 'success' && Array.isArray(response.phone_numbers)) {
      phoneNumbers.value = response.phone_numbers
    } else {
      console.error('Invalid phone numbers response:', response)
      phoneNumbers.value = []
    }
  } catch (error) {
    console.error('Failed to fetch phone numbers:', error)
  }
})

const props = defineProps<{
  phoneNumbers: PhoneNumber[]
  selectedPhoneNumber: string | null
  onClose: () => void
  onSave: (phoneNumberId: string) => void
}>()
</script> 