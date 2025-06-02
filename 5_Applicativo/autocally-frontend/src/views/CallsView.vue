<script setup lang="ts">
import { ref } from 'vue'
import { ArrowUpRight, ArrowDownLeft, ChevronLeft, ChevronRight, Search, Filter, Plus } from 'lucide-vue-next'
import { computed } from 'vue'
import { useRouter } from 'vue-router'

interface Call {
  id: string
  phoneNumber: string
  duration: string
  timestamp: string
  type: 'inbound' | 'outbound'
  agent: string
  status: 'completed' | 'missed' | 'failed'
  recording?: string
  summary?: string
}

// Add agent stats
interface AgentStats {
  name: string
  callCount: number
}

const agentStats: AgentStats[] = [
  { name: 'Marco', callCount: 145 },
  { name: 'Hans', callCount: 89 },
  { name: 'Sophie', callCount: 234 }
]

const mockCalls: Call[] = [
  {
    id: '1',
    phoneNumber: '+41 78 322 80 31',
    duration: '5m 30s',
    timestamp: '2024-02-04T10:30:00',
    type: 'inbound',
    agent: 'Marco',
    status: 'completed',
    recording: '/sample.mp3',
    summary: 'Customer called regarding a recent order issue.'
  },
  {
    id: '2',
    phoneNumber: '+41 79 444 55 66',
    duration: '3m 45s',
    timestamp: '2024-02-04T09:15:00',
    type: 'outbound',
    agent: 'Hans',
    status: 'completed'
  },
  {
    id: '3',
    phoneNumber: '+41 76 999 88 77',
    duration: '8m 20s',
    timestamp: '2024-02-04T08:45:00',
    type: 'inbound',
    agent: 'Sophie',
    status: 'completed'
  },
  {
    id: '4',
    phoneNumber: '+41 75 111 22 33',
    duration: '2m 10s',
    timestamp: '2024-02-04T08:30:00',
    type: 'outbound',
    agent: 'Marco',
    status: 'completed'
  },
  {
    id: '5',
    phoneNumber: '+41 77 888 99 00',
    duration: '6m 15s',
    timestamp: '2024-02-04T07:50:00',
    type: 'inbound',
    agent: 'Hans',
    status: 'completed'
  }
]

const activeTab = ref<'inbound' | 'outbound'>('inbound')
const currentPage = ref(1)
const itemsPerPage = 6
const searchQuery = ref('')
const showFilters = ref(false)

// Filter states
const selectedTimespan = ref('all')
const selectedAssistant = ref('all')
const dateRange = ref({
  start: '',
  end: '',
  startTime: '',
  endTime: ''
})

const timespanOptions = [
  { value: 'all', label: 'All time' },
  { value: 'today', label: 'Today' },
  { value: 'yesterday', label: 'Yesterday' },
  { value: 'week', label: 'Last 7 days' },
  { value: 'month', label: 'Last 30 days' },
  { value: 'custom', label: 'Custom range' }
]

const uniqueAssistants = computed(() => 
  Array.from(new Set(mockCalls.map(call => call.agent)))
)

const filteredCalls = computed(() => {
  let calls = mockCalls.filter(call => call.type === activeTab.value)
  
  // Search filter
  if (searchQuery.value) {
    const query = searchQuery.value.toLowerCase()
    calls = calls.filter(call => 
      call.phoneNumber.toLowerCase().includes(query) ||
      call.agent.toLowerCase().includes(query)
    )
  }
  
  // Assistant filter
  if (selectedAssistant.value !== 'all') {
    calls = calls.filter(call => call.agent === selectedAssistant.value)
  }

  // Timespan filter
  if (selectedTimespan.value !== 'all') {
    const now = new Date()
    
    switch (selectedTimespan.value) {
      case 'today':
        calls = calls.filter(call => {
          const date = new Date(call.timestamp)
          return date.toDateString() === now.toDateString()
        })
        break
      case 'yesterday':
        const yesterday = new Date(now)
        yesterday.setDate(yesterday.getDate() - 1)
        calls = calls.filter(call => {
          const date = new Date(call.timestamp)
          return date.toDateString() === yesterday.toDateString()
        })
        break
      case 'week':
        const weekAgo = new Date(now)
        weekAgo.setDate(weekAgo.getDate() - 7)
        calls = calls.filter(call => {
          const date = new Date(call.timestamp)
          return date >= weekAgo
        })
        break
      case 'month':
        const monthAgo = new Date(now)
        monthAgo.setDate(monthAgo.getDate() - 30)
        calls = calls.filter(call => {
          const date = new Date(call.timestamp)
          return date >= monthAgo
        })
        break
      case 'custom':
        if (dateRange.value.start && dateRange.value.end) {
          const start = new Date(`${dateRange.value.start}T${dateRange.value.startTime || '00:00'}`)
          const end = new Date(`${dateRange.value.end}T${dateRange.value.endTime || '23:59'}`)
          calls = calls.filter(call => {
            const date = new Date(call.timestamp)
            return date >= start && date <= end
          })
        }
        break
    }
  }
  
  return calls
})

const totalPages = computed(() => Math.ceil(filteredCalls.value.length / itemsPerPage))
const displayedCalls = computed(() => {
  const startIndex = (currentPage.value - 1) * itemsPerPage
  return filteredCalls.value.slice(startIndex, startIndex + itemsPerPage)
})

const setCurrentPage = (page: number) => {
  currentPage.value = page
}

const resetFilters = () => {
  selectedTimespan.value = 'all'
  selectedAssistant.value = 'all'
  dateRange.value = { start: '', end: '', startTime: '', endTime: '' }
}

const router = useRouter()

const openNewCall = () => {
  router.push('/calls/new')
}
</script>

<template>
  <div class="flex flex-col h-full">
    <!-- Top Tabs - Full Width -->
    <div class="px-8 pt-6">
      <div class="flex justify-between items-center mb-4">
        <div class="flex bg-gray-100 rounded-xl p-1 flex-1">
          <button
            v-for="tab in ['inbound', 'outbound']"
            :key="tab"
            @click="activeTab = tab as 'inbound' | 'outbound'"
            :class="[
              'flex-1 px-4 py-2 text-sm font-medium rounded-lg transition-colors',
              activeTab === tab 
                ? 'bg-white text-[#4285F4] shadow-sm' 
                : 'text-gray-600 hover:text-[#4285F4]'
            ]"
          >
            {{ tab.charAt(0).toUpperCase() + tab.slice(1) }}
          </button>
        </div>
        <button
          @click="openNewCall"
          class="ml-4 px-4 py-2 bg-[#4285F4] text-white rounded-xl flex items-center gap-2 hover:bg-[#3367d6] transition-colors"
        >
          <Plus class="w-4 h-4" />
          Make Call
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
            placeholder="Search by phone number or agent..."
            v-model="searchQuery"
            class="w-full pl-10 pr-4 py-2 bg-white border border-gray-200 rounded-xl text-sm placeholder-gray-400 focus:outline-none focus:border-[#4285F4] transition-colors"
          />
        </div>
        <button
          @click="showFilters = !showFilters"
          :class="[
            'px-4 py-2 bg-white border border-gray-200 rounded-xl text-sm font-medium transition-colors flex items-center gap-2',
            showFilters || selectedTimespan !== 'all' || selectedAssistant !== 'all'
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
          <!-- Time Span -->
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
            
            <!-- Custom Date Range with Time -->
            <div v-if="selectedTimespan === 'custom'" class="mt-3 space-y-3">
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="block text-sm text-gray-600 mb-1">Start date</label>
                  <input
                    type="date"
                    v-model="dateRange.start"
                    class="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-[#4285F4] transition-colors"
                  />
                </div>
                <div>
                  <label class="block text-sm text-gray-600 mb-1">Start time</label>
                  <input
                    type="time"
                    v-model="dateRange.startTime"
                    class="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-[#4285F4] transition-colors"
                  />
                </div>
              </div>
              <div class="grid grid-cols-2 gap-3">
                <div>
                  <label class="block text-sm text-gray-600 mb-1">End date</label>
                  <input
                    type="date"
                    v-model="dateRange.end"
                    class="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-[#4285F4] transition-colors"
                  />
                </div>
                <div>
                  <label class="block text-sm text-gray-600 mb-1">End time</label>
                  <input
                    type="time"
                    v-model="dateRange.endTime"
                    class="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-[#4285F4] transition-colors"
                  />
                </div>
              </div>
            </div>
          </div>

          <!-- Assistant -->
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Assistant</label>
            <select
              v-model="selectedAssistant"
              class="w-full px-3 py-2 bg-white border border-gray-200 rounded-lg text-sm focus:outline-none focus:border-[#4285F4] transition-colors"
            >
              <option value="all">All assistants</option>
              <option v-for="assistant in uniqueAssistants" :key="assistant" :value="assistant">
                {{ assistant }}
              </option>
            </select>
          </div>
        </div>
      </div>
    </div>

    <!-- Calls List -->
    <div class="flex-1 px-8 overflow-y-auto">
      <div class="space-y-3">
        <div
          v-for="call in displayedCalls"
          :key="call.id"
          @click="router.push(`/calls/${call.id}`)"
          class="bg-white rounded-xl p-4 border border-gray-200 hover:border-[#4285F4] transition-colors cursor-pointer"
        >
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-4">
              <div
                :class="[
                  'w-10 h-10 rounded-full flex items-center justify-center',
                  call.type === 'inbound' 
                    ? 'bg-green-50 text-green-600' 
                    : 'bg-[#4285F4]/10 text-[#4285F4]'
                ]"
              >
                <ArrowDownLeft v-if="call.type === 'inbound'" class="w-5 h-5" />
                <ArrowUpRight v-else class="w-5 h-5" />
              </div>
              <div>
                <p class="font-medium text-gray-900">{{ call.phoneNumber }}</p>
                <p class="text-sm text-gray-500">
                  {{ new Date(call.timestamp).toLocaleTimeString() }} • {{ call.duration }}
                </p>
              </div>
            </div>
            <div>
              <span
                :class="[
                  'px-3 py-1 rounded-full text-xs font-medium cursor-help',
                  {
                    'bg-[#4285F4]/10 text-[#4285F4]': call.agent === 'Marco',
                    'bg-yellow-50 text-yellow-700': call.agent === 'Hans',
                    'bg-purple-50 text-purple-700': call.agent === 'Sophie'
                  }
                ]"
                :title="`${agentStats.find(a => a.name === call.agent)?.callCount || 0} calls made`"
              >
                {{ call.agent }}
              </span>
            </div>
          </div>
        </div>
      </div>

      <!-- Pagination - Moved Higher -->
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
