<script setup lang="ts">
import { ref, computed } from 'vue'
import { 
  Phone, Calendar, Clock, PhoneIncoming, PhoneOutgoing, 
  CheckCircle2, XCircle, PhoneOff, Play, Pause, Info,
  AlertTriangle, AlertCircle, X, Sparkles, MessageSquare, Activity
} from 'lucide-vue-next'
import { useRouter } from 'vue-router'

interface Call {
  id: string
  phoneNumber: string
  duration: string
  timestamp: string
  type: 'inbound' | 'outbound'
  agent: {
    name: string
    avatar?: string
  }
  status: 'completed' | 'missed' | 'failed'
  recording?: string
  summary?: string
  transcript: TranscriptEntry[]
  actions: CallAction[]
  date: string
}

interface TranscriptEntry {
  time: string
  speaker: 'agent' | 'customer'
  text: string
}

interface CallAction {
  timestamp: string
  action: string
  details: string
  level: 'info' | 'warning' | 'error'
}

const router = useRouter()
const isPlaying = ref(false)
const progress = ref(0)
const audioRef = ref<HTMLAudioElement | null>(null)
const currentTime = ref(0)
const totalDuration = ref(0)

// For demo purposes, using mock data - in real app this would come from API
const call = ref<Call>({
  id: '1',
  phoneNumber: '+41 78 322 80 31',
  duration: '5m 30s',
  timestamp: '2024-02-04T10:30:00',
  date: '2024-02-04',
  type: 'inbound',
  agent: {
    name: 'Marco'
  },
  status: 'completed',
  recording: '/sample.mp3',
  summary: 'Customer called regarding a recent order issue.',
  transcript: [
    { time: "0:00", speaker: "agent", text: "Hello, thank you for calling. How can I help you today?" },
    { time: "0:05", speaker: "customer", text: "Hi, I'm calling about my recent order." }
  ],
  actions: [
    {
      timestamp: new Date().toISOString(),
      action: "Call Started",
      details: "Initiated inbound call from customer",
      level: "info"
    }
  ]
})

// Add these helper functions
const formatTime = (timeInSeconds: number): string => {
  const minutes = Math.floor(timeInSeconds / 60)
  const seconds = Math.floor(timeInSeconds % 60)
  return `${minutes}:${seconds.toString().padStart(2, '0')}`
}

const convertTimeToSeconds = (timeString: string): number => {
  const [minutes, seconds] = timeString.split(':').map(Number)
  return minutes * 60 + seconds
}

// Reuse all the existing functions from CallDetailsModal
const togglePlay = () => {
  if (audioRef.value) {
    if (isPlaying.value) {
      audioRef.value.pause()
    } else {
      audioRef.value.play()
    }
    isPlaying.value = !isPlaying.value
  }
}

const handleTimeUpdate = () => {
  if (audioRef.value) {
    const time = audioRef.value.currentTime
    progress.value = (time / audioRef.value.duration) * 100
    currentTime.value = time
  }
}

const handleSeek = (e: Event) => {
  if (audioRef.value) {
    const target = e.target as HTMLInputElement
    const time = (Number(target.value) / 100) * audioRef.value.duration
    audioRef.value.currentTime = time
    progress.value = Number(target.value)
  }
}

const handleTimeClick = (time: string) => {
  const [minutes, seconds] = time.split(':').map(Number)
  const timeInSeconds = minutes * 60 + seconds
  currentTime.value = timeInSeconds
  if (audioRef.value) {
    audioRef.value.currentTime = timeInSeconds
    audioRef.value.play()
    isPlaying.value = true
  }
}

const getStatusIcon = (status: string) => {
  switch (status) {
    case 'completed':
      return CheckCircle2
    case 'missed':
      return PhoneOff
    case 'failed':
      return XCircle
    default:
      return null
  }
}

const getStatusColor = (status: string) => {
  switch (status) {
    case 'completed':
      return 'text-green-600'
    case 'missed':
      return 'text-yellow-600'
    case 'failed':
      return 'text-red-600'
    default:
      return ''
  }
}

const getLevelIcon = (level: string) => {
  switch (level) {
    case 'info':
      return Info
    case 'warning':
      return AlertTriangle
    case 'error':
      return AlertCircle
    default:
      return null
  }
}
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header with gradient background -->
    <div class="bg-white shadow-sm">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="py-6">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-4">
              <button
                @click="router.back()"
                class="p-2 text-gray-500 hover:text-black transition-colors"
              >
                <X class="w-6 h-6" />
              </button>
              <div>
                <h1 class="text-2xl font-bold ">Call Analysis</h1>
                
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>

    <!-- Content -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="space-y-8">
        <!-- Call Info Card -->
        <div class="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
          <div class="flex items-center gap-4">
            <div class="p-3 rounded-xl bg-blue-50">
              <PhoneIncoming v-if="call.type === 'inbound'" class="w-6 h-6 text-blue-600" />
              <PhoneOutgoing v-else class="w-6 h-6 text-blue-600" />
            </div>
            <div class="flex-1">
              <div class="flex items-center gap-3">
                <h2 class="text-xl font-bold text-gray-900">{{ call.phoneNumber }}</h2>
                <span 
                  :class="[
                    'px-2 py-1 rounded-full text-xs font-medium',
                    getStatusColor(call.status).replace('text', 'bg') + '/10',
                    getStatusColor(call.status)
                  ]"
                >
                  {{ call.status }}
                </span>
              </div>
              <div class="flex items-center gap-4 text-sm text-gray-600 mt-2">
                <div class="flex items-center gap-1.5">
                  <Calendar class="w-4 h-4" />
                  <span>{{ call.date }}</span>
                </div>
                <div class="flex items-center gap-1.5">
                  <Clock class="w-4 h-4" />
                  <span>{{ call.duration }}</span>
                </div>
                <div class="flex items-center gap-1.5">
                  <Phone class="w-4 h-4" />
                  <span>Handled by {{ call.agent.name }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- AI Summary Section -->
        <div class="bg-cyan-50 rounded-2xl p-6 shadow-sm border-l-4 border-blue-500">
          <h3 class="flex items-center gap-2 text-lg font-semibold text-gray-900 mb-3">
            <Sparkles class="w-5 h-5 text-blue-600" />
            AI Analysis Summary
          </h3>
          <p class="text-gray-700 leading-relaxed bg-white p-4 rounded-xl shadow-sm">
            {{ call.summary || 'Generating AI insights...' }}
          </p>
        </div>

        <!-- Enhanced Audio Player -->
        <div class="bg-white rounded-lg p-6">
          <div class="flex items-center gap-2 mb-10">
            <div class="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center">
              <MessageSquare class="w-5 h-5 text-blue-500" />
            </div>
            <h2 class="text-lg font-medium">Call Recording</h2>
          </div>

          <div class="space-y-4">
            <!-- Audio Controls -->
            <div class="flex items-center gap-4">
              <button
                @click="togglePlay"
                class="w-12 h-12 rounded-lg bg-blue-50 flex items-center justify-center hover:bg-blue-100 transition-colors"
              >
                <component 
                  :is="isPlaying ? Pause : Play" 
                  class="w-5 h-5 text-blue-500"
                />
              </button>
              
              <div class="flex-1">
                <input
                  type="range"
                  min="0"
                  max="100"
                  :value="progress"
                  @input="handleSeek"
                  class="w-full accent-blue-500 cursor-pointer h-1.5 rounded-full bg-gray-200"
                />
                <div class="flex justify-between mt-2">
                  <span class="text-sm text-gray-500">{{ formatTime(currentTime) }}</span>
                  <span class="text-sm text-gray-500">{{ formatTime(totalDuration) }}</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Conversation Insights -->
        <div class="grid lg:grid-cols-2 gap-8">
          <!-- Enhanced Transcript -->
          <div class="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
            <h3 class="flex items-center gap-2 text-lg font-semibold text-gray-900 mb-4">
              <MessageSquare class="w-5 h-5 text-blue-600" />
              Conversation Timeline
              <span class="text-sm font-normal text-gray-500">
                ({{ call.transcript.length }} interactions)
              </span>
            </h3>
            <div class="space-y-4">
              <div
                v-for="(entry, index) in call.transcript"
                :key="index"
                class="group flex gap-4 p-4 rounded-xl transition-all"
                :class="{
                  'bg-blue-50 border border-blue-100 shadow-sm': 
                    Math.abs(convertTimeToSeconds(entry.time) - currentTime) < 1,
                  'hover:bg-gray-50': Math.abs(convertTimeToSeconds(entry.time) - currentTime) >= 1
                }"
              >
                <button
                  @click="() => handleTimeClick(entry.time)"
                  class="text-sm text-gray-500 hover:text-blue-600 transition-colors whitespace-nowrap pt-1"
                >
                  {{ entry.time }}
                </button>
                <div class="flex-1">
                  <div class="flex items-center gap-2 mb-1">
                    <span
                      :class="[
                        'text-sm font-semibold',
                        entry.speaker === 'agent' ? 'text-blue-600' : 'text-gray-700'
                      ]"
                    >
                      {{ entry.speaker === 'agent' ? 'AI Agent' : 'Customer' }}
                    </span>
                    <span class="text-xs text-gray-400">•</span>
                    <span class="text-xs text-gray-500">
                      {{ entry.speaker === 'agent' ? 'Automated Response' : 'Incoming Call' }}
                    </span>
                  </div>
                  <p class="text-gray-700 text-sm leading-relaxed">
                    {{ entry.text }}
                  </p>
                </div>
              </div>
            </div>
          </div>

          <!-- System Diagnostics -->
          <div class="bg-white rounded-2xl p-6 shadow-sm border border-gray-100">
            <h3 class="flex items-center gap-2 text-lg font-semibold text-gray-900 mb-4">
              <Activity class="w-5 h-5 text-blue-600" />
              System Diagnostics
              <span class="text-sm font-normal text-gray-500">
                ({{ call.actions.length }} events)
              </span>
            </h3>
            <div class="space-y-3">
              <div
                v-for="(action, index) in call.actions"
                :key="index"
                class="flex items-start gap-3 p-3 rounded-xl border transition-all"
                :class="{
                  'border-blue-100 bg-blue-50': action.level === 'info',
                  'border-yellow-100 bg-yellow-50': action.level === 'warning',
                  'border-red-100 bg-red-50': action.level === 'error'
                }"
              >
                <component
                  :is="getLevelIcon(action.level)"
                  class="w-5 h-5 mt-1 flex-shrink-0"
                  :class="{
                    'text-blue-500': action.level === 'info',
                    'text-yellow-500': action.level === 'warning',
                    'text-red-500': action.level === 'error'
                  }"
                />
                <div class="flex-1">
                  <div class="flex items-center gap-2 mb-1">
                    <span class="text-sm font-medium text-gray-900">{{ action.action }}</span>
                    <span class="text-xs text-gray-400">{{ new Date(action.timestamp).toLocaleTimeString() }}</span>
                  </div>
                  <p class="text-sm text-gray-600 leading-relaxed">
                    {{ action.details }}
                  </p>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template> 