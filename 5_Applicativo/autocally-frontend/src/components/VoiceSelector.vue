<template>
  <div class="mb-8 voice-selector">
    <label class="block text-sm text-gray-500 mb-2">Assistant Voice</label>
    <div class="relative">
      <!-- Loading State -->
      <div v-if="isLoading" class="w-full p-3 bg-white border border-gray-200 rounded-xl text-sm text-gray-400">
        Loading voices...
      </div>
      
      <!-- Error State -->
      <div v-else-if="error" class="w-full p-3 bg-red-50 border border-red-200 rounded-xl text-sm text-red-600">
        {{ error }}
      </div>
      
      <!-- Normal State -->
      <button
        v-else
        @click="isExpanded = !isExpanded"
        class="w-full p-3 bg-white border border-gray-200 rounded-xl text-sm text-gray-800 hover:border-blue-400 transition-colors flex items-center justify-between"
      >
        <span>{{ selectedVoiceData?.name || 'Select a voice' }}</span>
        <ChevronDown 
          class="w-5 h-5 text-gray-400 transition-transform"
          :class="{ 'rotate-180': isExpanded }"
        />
      </button>

      <!-- Dropdown Panel -->
      <div v-if="isExpanded" class="absolute z-50 w-full mt-2 bg-white border border-gray-200 rounded-xl shadow-lg">
        <!-- Search and Filters -->
        <div class="p-3 border-b border-gray-100">
          <div class="relative mb-3">
            <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-gray-400" />
            <input
              type="text"
              placeholder="Search..."
              class="w-full pl-9 pr-4 py-2 bg-gray-50 border border-gray-200 rounded-lg text-sm text-gray-800 placeholder-gray-400 focus:outline-none focus:ring-2 focus:ring-blue-100"
              v-model="voiceSearch"
            />
          </div>
          <div class="flex gap-2">
            <select
              v-model="selectedGender"
              class="flex-1 px-3 py-1.5 bg-gray-50 border border-gray-200 rounded-lg text-sm"
            >
              <option value="">Any gender</option>
              <option value="masculine">Male</option>
              <option value="feminine">Female</option>
            </select>
            <select
              v-model="selectedLanguage"
              :disabled="isLoadingLanguages"
              class="flex-1 px-3 py-1.5 bg-gray-50 border border-gray-200 rounded-lg text-sm"
            >
              <option value="">{{ isLoadingLanguages ? 'Loading languages...' : 'Any language' }}</option>
              <option v-for="lang in languages" :key="lang" :value="lang">
                {{ lang.toUpperCase() }}
              </option>
            </select>
          </div>
        </div>

        <!-- Voice List -->
        <div 
          class="max-h-64 overflow-y-auto"
          ref="voiceListRef"
        >
          <div
            v-for="voice in filteredVoices"
            :key="voice.id"
            class="flex items-center justify-between p-3 hover:bg-gray-50 cursor-pointer"
            @click="selectVoice(voice.id)"
          >
            <div class="flex-1">
              <div class="text-sm font-medium text-gray-800">{{ voice.name }}</div>
              <div class="text-xs text-gray-500">
                {{ voice.description }} • {{ voice.language.toUpperCase() }}
              </div>
            </div>
            <input
              type="radio"
              :value="voice.id"
              v-model="selectedVoice"
              class="w-4 h-4 text-blue-600 bg-white border-gray-300 focus:ring-blue-500"
            />
          </div>
          <div v-if="isLoadingMore" class="p-3 text-center text-sm text-gray-500">
            Loading more voices...
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onUnmounted, nextTick } from 'vue'
import { Search, ChevronDown } from 'lucide-vue-next'
import { assistantsApi } from '@/services/api'

interface Voice {
  id: string
  name: string
  description: string
  gender: string
  language: string
}

const props = defineProps<{
  modelValue: string
  assistantId: number
}>()

const emit = defineEmits(['update:modelValue'])

const voiceSearch = ref('')
const selectedGender = ref('')
const selectedLanguage = ref('')
const selectedVoice = ref(props.modelValue)
const isExpanded = ref(false)
const isLoading = ref(false)
const isLoadingMore = ref(false)
const error = ref('')
const voices = ref<Voice[]>([])
const languages = ref<string[]>([])
const page = ref(1)
const hasMore = ref(true)
const voiceListRef = ref<HTMLElement | null>(null)
const isLoadingLanguages = ref(false)
const searchTimeout = ref<ReturnType<typeof setTimeout> | null>(null)

const fetchVoices = async () => {
  try {
    if (!isLoading.value) {  // Prevent multiple simultaneous calls
      isLoading.value = true
      isLoadingLanguages.value = true

      const response = await assistantsApi.getVoices()
      
      if (Array.isArray(response)) {
        voices.value = response
        const uniqueLanguages = [...new Set(response.map(voice => voice.language))]
        languages.value = uniqueLanguages.sort()
      } else if (response.voices) {
        voices.value = response.voices
        const uniqueLanguages = [...new Set(response.voices.map(voice => voice.language))]
        languages.value = uniqueLanguages.sort()
      }

      // Set the initial selected voice if one is provided
      if (props.modelValue) {
        selectedVoice.value = props.modelValue
      }
    }
  } catch (err) {
    console.error('Failed to fetch voices:', err)
    error.value = 'Failed to load voices'
  } finally {
    isLoading.value = false
    isLoadingLanguages.value = false
  }
}

const handleScroll = async (event: Event) => {
  const element = event.target as HTMLElement
  if (
    !isLoadingMore.value &&
    hasMore.value &&
    element.scrollHeight - element.scrollTop <= element.clientHeight + 100
  ) {
    page.value++
    await fetchVoices()
  }
}

// Filter voices locally with normalized case comparison
const filteredVoices = computed(() => {
  return voices.value.filter(voice => {
    const searchTerm = voiceSearch.value.toLowerCase()
    const matchesSearch = !voiceSearch.value || 
      voice.name.toLowerCase().includes(searchTerm) ||
      voice.description.toLowerCase().includes(searchTerm)
    
    const matchesGender = !selectedGender.value || 
      voice.gender === selectedGender.value
    
    const matchesLanguage = !selectedLanguage.value || 
      voice.language === selectedLanguage.value
    
    return matchesSearch && matchesGender && matchesLanguage
  })
})

const selectedVoiceData = computed(() => {
  return voices.value.find(voice => voice.id === selectedVoice.value)
})

const selectVoice = async (voiceId: string) => {
  try {
    // Call API to update assistant's voice
    await assistantsApi.updateVoiceID(props.assistantId, {
      cartesia_voice_id: voiceId
    })
    
    selectedVoice.value = voiceId
    isExpanded.value = false
    emit('update:modelValue', voiceId)
  } catch (err) {
    console.error('Failed to update voice:', err)
    error.value = 'Failed to update voice'
  }
}

watch(() => props.modelValue, (newValue) => {
  selectedVoice.value = newValue
})

watch(selectedVoice, (newValue) => {
  emit('update:modelValue', newValue)
})

onMounted(() => {
  nextTick(() => {
    fetchVoices()
  })
  
  document.addEventListener('click', (event: MouseEvent) => {
    const target = event.target as HTMLElement
    if (!target.closest('.voice-selector')) {
      isExpanded.value = false
    }
  })
})

onUnmounted(() => {
  if (searchTimeout.value) {
    clearTimeout(searchTimeout.value)
  }
})
</script> 
