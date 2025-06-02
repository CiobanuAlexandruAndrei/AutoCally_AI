<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { 
  Search, 
  Plus, 
  FileText, 
  Link, 
  ChevronLeft, 
  ChevronRight, 
  Filter,
  Globe,
  File,
  Trash2
} from 'lucide-vue-next'
import { knowledgeBaseApi, assistantsApi } from '../services/api'

interface KnowledgeBaseResponse {
  id: number
  name: string
  description: string
  assistant_ids: string[]
  folder_path: string
  created_at: string
  updated_at: string
  document_count: number
  needs_reload: boolean
  last_loaded?: string
  total_size: number
}

interface Assistant {
  id: string
  name: string
}

interface KnowledgeBase {
  id: number
  name: string
  description: string
  assistant_ids: string[]
  folder_path: string
  created_at: string
  updated_at: string
  document_count: number
  assistant_names?: string[]
  needs_reload: boolean
  last_loaded?: string
  total_size: number
}

interface Document {
  id: string
  title: string
  type: 'file' | 'text' | 'url'
  content: string
  createdAt: string
  size?: string
  url?: string
}

const router = useRouter()
const searchQuery = ref('')
const currentPage = ref(1)
const itemsPerPage = 6
const showFilters = ref(false)
const selectedTimespan = ref('all')
const selectedType = ref('all')

// Replace mock data section with API call
const knowledgeBases = ref<KnowledgeBase[]>([])
const assistants = ref<{id: string, name: string}[]>([])
const isLoading = ref(false)
const error = ref('')
const processingKnowledgeBases = ref(new Set<number>())
const taskStatuses = ref<Record<number, any>>({})

onMounted(async () => {
  try {
    isLoading.value = true
    const [kbResponse, assistantsResponse] = await Promise.all([
      knowledgeBaseApi.getAll(),
      assistantsApi.getAll()
    ])
    
    // Store assistants for reference
    assistants.value = assistantsResponse

    // Map knowledge bases and ensure assistant names are properly set
    knowledgeBases.value = kbResponse.map((kb: KnowledgeBaseResponse) => {
      const assistantIds = Array.isArray(kb.assistant_ids) ? kb.assistant_ids : []
      
      const assistantNames = assistantIds
        .map((id: string) => {
          const assistant = assistantsResponse.find((a: Assistant) => a.id === id)
          return assistant?.name
        })
        .filter(Boolean)

      return {
        ...kb,
        assistant_names: assistantNames.length ? assistantNames : ['Unknown']
      }
    })

    console.log('Knowledge Bases with assistants:', knowledgeBases.value) // For debugging
  } catch (err) {
    console.error('Failed to fetch knowledge bases:', err)
    error.value = 'Failed to fetch knowledge bases'
  } finally {
    isLoading.value = false
  }
})

const timespanOptions = [
  { value: 'all', label: 'All time' },
  { value: 'today', label: 'Today' },
  { value: 'week', label: 'Last 7 days' },
  { value: 'month', label: 'Last 30 days' }
]
  
const typeOptions = [
  { value: 'all', label: 'All types' },
  { value: 'file', label: 'Files' },
  { value: 'text', label: 'Text' },
  { value: 'url', label: 'URLs' }
]

const filteredKnowledgeBases = computed(() => {
  let bases = knowledgeBases.value

  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    bases = bases.filter(kb => 
      kb.name.toLowerCase().includes(query) ||
      kb.description.toLowerCase().includes(query)
    )
  }

  if (selectedTimespan.value !== 'all') {
    const now = new Date()
    
    switch (selectedTimespan.value) {
      case 'today':
        bases = bases.filter(kb => {
          const date = new Date(kb.updated_at)
          return date.toDateString() === now.toDateString()
        })
        break
      case 'week':
        const weekAgo = new Date(now)
        weekAgo.setDate(weekAgo.getDate() - 7)
        bases = bases.filter(kb => {
          const date = new Date(kb.updated_at)
          return date >= weekAgo
        })
        break
      case 'month':
        const monthAgo = new Date(now)
        monthAgo.setDate(monthAgo.getDate() - 30)
        bases = bases.filter(kb => {
          const date = new Date(kb.updated_at)
          return date >= monthAgo
        })
        break
    }
  }

  return bases
})

const totalPages = computed(() => Math.ceil(filteredKnowledgeBases.value.length / itemsPerPage))
const displayedKnowledgeBases = computed(() => {
  const startIndex = (currentPage.value - 1) * itemsPerPage
  return filteredKnowledgeBases.value.slice(startIndex, startIndex + itemsPerPage)
})

const setCurrentPage = (page: number) => {
  currentPage.value = page
}

const resetFilters = () => {
  selectedTimespan.value = 'all'
  selectedType.value = 'all'
}

const createKnowledgeBase = () => {
  router.push('/knowledge-base/new')
}

const openKnowledgeBase = (id: string) => {
  router.push(`/knowledge-base/${id}`)
}

const formatDate = (dateString: string) => {
  const date = new Date(dateString)
  return date.toLocaleDateString('en-GB') // This will format as dd/mm/yyyy
}

const handleReload = async (kb: KnowledgeBase) => {
  try {
    processingKnowledgeBases.value.add(kb.id)
    const response = await knowledgeBaseApi.startProcessing(kb.id)
    
    // Start polling for task status
    const pollStatus = async () => {
      const status = await knowledgeBaseApi.getTaskStatus(response.task_id)
      taskStatuses.value[kb.id] = status

      if (status.status !== 'COMPLETED' && status.status !== 'FAILED') {
        setTimeout(pollStatus, 2000) // Poll every 2 seconds
      } else {
        processingKnowledgeBases.value.delete(kb.id)
        // Refresh the knowledge base list
        const kbResponse = await knowledgeBaseApi.getAll()
        knowledgeBases.value = kbResponse
      }
    }

    pollStatus()
  } catch (err) {
    console.error('Failed to reload knowledge base:', err)
    processingKnowledgeBases.value.delete(kb.id)
    error.value = 'Failed to reload knowledge base'
  }
}
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- Header -->
    <div class="px-8 pt-6">
      <div class="flex justify-between items-center mb-4">
        <h1 class="text-xl font-semibold text-gray-900">Knowledge Base</h1>
        <button
          @click="createKnowledgeBase"
          class="px-4 py-2 bg-[#4285F4] text-white rounded-xl flex items-center gap-2 hover:bg-[#3367d6] transition-colors"
        >
          <Plus class="w-4 h-4" />
          New Knowledge Base
        </button>
      </div>
    </div>

    <!-- Search and Filters -->
    <div class="px-8 pt-6 pb-4">
      <div class="flex gap-3">
        <div class="flex-1 relative">
          <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
          <input
            type="text"
            placeholder="Search knowledge bases..."
            v-model="searchQuery"
            class="w-full pl-10 pr-4 py-2 bg-white border border-gray-200 rounded-xl text-sm placeholder-gray-400 focus:outline-none focus:border-[#4285F4] transition-colors"
          />
        </div>
        <button
          @click="showFilters = !showFilters"
          :class="[
            'px-4 py-2 bg-white border border-gray-200 rounded-xl text-sm font-medium transition-colors flex items-center gap-2',
            showFilters || selectedTimespan !== 'all' || selectedType !== 'all'
              ? 'border-[#4285F4] text-[#4285F4]'
              : 'text-gray-600 hover:border-[#4285F4] hover:text-[#4285F4]'
          ]"
        >
          <Filter class="w-4 h-4" />
          Filters
        </button>
      </div>

      <!-- Filters Dropdown -->
      <div v-if="showFilters" class="mt-4 p-4 bg-white border border-gray-200 rounded-xl shadow-lg">
        <div class="flex justify-between items-center mb-4">
          <h3 class="font-medium text-gray-900">Filters</h3>
          <button
            @click="resetFilters"
            class="text-sm text-[#4285F4] hover:text-[#3367d6] transition-colors"
          >
            Reset all
          </button>
        </div>
        
        <div class="space-y-4">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Time span</label>
            <select
              v-model="selectedTimespan"
              class="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-[#4285F4] transition-colors"
            >
              <option v-for="option in timespanOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Content Type</label>
            <select
              v-model="selectedType"
              class="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-[#4285F4] transition-colors"
            >
              <option v-for="option in typeOptions" :key="option.value" :value="option.value">
                {{ option.label }}
              </option>
            </select>
          </div>
        </div>
      </div>
    </div>

    <!-- Add before Knowledge Base List -->
    <div v-if="isLoading" class="flex-1 flex items-center justify-center">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-[#4285F4]"></div>
    </div>

    <div v-else-if="error" class="flex-1 px-8">
      <div class="p-4 bg-red-50 text-red-600 rounded-xl">
        {{ error }}
      </div>
    </div>

    <!-- Knowledge Base List -->
    <div class="flex-1 px-8 overflow-y-auto">
      <div class="space-y-3">
        <div
          v-for="kb in displayedKnowledgeBases"
          :key="kb.id"
          @click="openKnowledgeBase(kb.id.toString())"
          class="bg-white rounded-xl p-4 border border-gray-200 hover:border-[#4285F4] transition-colors cursor-pointer"
        >
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-4">
              <div class="w-10 h-10 rounded-full bg-[#4285F4]/10 text-[#4285F4] flex items-center justify-center">
                <FileText class="w-5 h-5" />
              </div>
              <div>
                <p class="font-medium text-gray-900">{{ kb.name }}</p>
                <p class="text-sm text-gray-500">
                  {{ kb.document_count }} documents • Last updated {{ formatDate(kb.updated_at) }}
                </p>
              </div>
            </div>
            <div class="flex items-center gap-4">
              <div class="flex gap-1">
                <span 
                  v-for="assistantName in kb.assistant_names" 
                  :key="assistantName"
                  class="px-2 py-1 rounded-full text-xs font-medium bg-[#4285F4]/10 text-[#4285F4]"
                >
                  {{ assistantName }}
                </span>
              </div>
              <button 
                v-if="kb.needs_reload"
                @click.stop="handleReload(kb)"
                :disabled="processingKnowledgeBases.has(kb.id)"
                class="px-3 py-1.5 text-sm bg-yellow-100 text-yellow-800 rounded-lg hover:bg-yellow-200 transition-colors flex items-center gap-2"
              >
                <template v-if="processingKnowledgeBases.has(kb.id)">
                  <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-yellow-800"></div>
                  {{ taskStatuses[kb.id]?.progress_percentage?.toFixed(0) }}%
                </template>
                <template v-else>
                  Reload
                </template>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Pagination -->
      <div class="py-6 flex justify-center">
        <div class="flex items-center gap-1">
          <button
            @click="setCurrentPage(Math.max(1, currentPage - 1))"
            :disabled="currentPage === 1"
            class="p-2 rounded-lg bg-white border border-gray-200 text-gray-600 hover:border-[#4285F4] hover:text-[#4285F4] disabled:opacity-50 disabled:hover:border-gray-200 disabled:hover:text-gray-600 transition-colors"
          >
            <ChevronLeft class="w-5 h-5" />
          </button>
          <button
            v-for="page in totalPages"
            :key="page"
            @click="setCurrentPage(page)"
            :class="[
              'w-8 h-8 rounded-lg flex items-center justify-center text-sm font-medium transition-colors',
              currentPage === page
                ? 'bg-[#4285F4] text-white'
                : 'bg-white border border-gray-200 text-gray-600 hover:border-[#4285F4] hover:text-[#4285F4]'
            ]"
          >
            {{ page }}
          </button>
          <button
            @click="setCurrentPage(Math.min(totalPages, currentPage + 1))"
            :disabled="currentPage === totalPages"
            class="p-2 rounded-lg bg-white border border-gray-200 text-gray-600 hover:border-[#4285F4] hover:text-[#4285F4] disabled:opacity-50 disabled:hover:border-gray-200 disabled:hover:text-gray-600 transition-colors"
          >
            <ChevronRight class="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template> 