<script setup lang="ts">
import { ref, computed } from 'vue'
import { 
  Phone, Calendar, Clock, PhoneIncoming, PhoneOutgoing, 
  CheckCircle2, XCircle, PhoneOff, Play, Pause, Info,
  AlertTriangle, AlertCircle, X
} from 'lucide-vue-next'

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

const props = defineProps<{
  call: Call
  onClose: () => void
}>()

const isPlaying = ref(false)
const progress = ref(0)
const audioRef = ref<HTMLAudioElement | null>(null)
const currentTime = ref(0)

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

const mockCalls: Call[] = [
  {
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
  }
  // ... other calls
]

</script>

<template>
  <div class="fixed inset-0 bg-gray-900/50 backdrop-blur-sm z-50 flex items-center justify-center p-6">
    <div class="bg-white rounded-2xl w-full max-w-5xl max-h-[90vh] overflow-hidden shadow-sm border border-gray-100">
      <!-- Header -->
      <div class="px-8 py-6 border-b border-gray-100">
        <div class="flex items-center justify-between">
          <div class="space-y-2">
            <div class="flex items-center gap-3">
              <div
                :class="[
                  'w-10 h-10 rounded-xl flex items-center justify-center',
                  call.type === 'inbound' 
                    ? 'bg-green-50 text-green-600' 
                    : 'bg-[#4285F4]/10 text-[#4285F4]'
                ]"
              >
                <PhoneIncoming v-if="call.type === 'inbound'" class="w-5 h-5" />
                <PhoneOutgoing v-else class="w-5 h-5" />
              </div>
              <h2 class="text-xl font-semibold text-gray-900">{{ call.phoneNumber }}</h2>
              <component
                :is="getStatusIcon(call.status)"
                class="w-5 h-5"
                :class="getStatusColor(call.status)"
              />
            </div>
            <div class="flex items-center gap-4 text-sm text-gray-500">
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
                <span>Agent: {{ call.agent.name }}</span>
              </div>
            </div>
          </div>
          <button
            @click="onClose"
            class="p-2 text-gray-400 hover:text-gray-600 transition-colors rounded-lg hover:bg-gray-50"
          >
            <X class="w-5 h-5" />
          </button>
        </div>
      </div>

      <!-- Content -->
      <div class="px-8 py-6 overflow-y-auto max-h-[calc(90vh-200px)]">
        <div class="space-y-6">
          <!-- Summary -->
          <div class="bg-white rounded-xl p-4 border border-gray-200">
            <h3 class="font-medium text-gray-900 mb-2">Call Summary</h3>
            <p class="text-gray-600 text-sm">{{ call.summary }}</p>
          </div>

          <!-- Audio Player -->
          <div class="bg-white rounded-xl p-4 border border-gray-200">
            <div class="flex items-center gap-4">
              <button
                @click="togglePlay"
                class="h-10 w-10 flex items-center justify-center rounded-xl bg-[#4285F4] text-white hover:bg-[#3367d6] transition-colors"
              >
                <component :is="isPlaying ? Pause : Play" class="w-5 h-5" />
              </button>
              <div class="flex-1">
                <input
                  type="range"
                  min="0"
                  max="100"
                  :value="progress"
                  @input="handleSeek"
                  class="w-full accent-[#4285F4] cursor-pointer"
                />
              </div>
              <audio
                ref="audioRef"
                :src="call.recording"
                @timeupdate="handleTimeUpdate"
                class="hidden"
              />
            </div>
          </div>

          <!-- Two Columns -->
          <div class="grid md:grid-cols-2 gap-6">
            <!-- Transcript -->
            <div class="bg-white rounded-xl p-6 border border-gray-200">
              <h3 class="font-medium text-gray-900 mb-4">
                Transcript
                <span class="text-sm font-normal text-gray-500">
                  ({{ call.transcript.length }} messages)
                </span>
              </h3>
              <div class="space-y-3">
                <div
                  v-for="(entry, index) in call.transcript"
                  :key="index"
                  class="flex gap-4 p-3 rounded-lg hover:bg-gray-50 transition-colors"
                  :class="{
                    'bg-[#4285F4]/5 border border-[#4285F4]/10': 
                      Math.abs(Number(entry.time.split(':')[0]) * 60 + 
                      Number(entry.time.split(':')[1]) - currentTime) < 1
                  }"
                >
                  <button
                    @click="() => handleTimeClick(entry.time)"
                    class="text-sm text-gray-500 hover:text-[#4285F4] transition-colors whitespace-nowrap"
                  >
                    {{ entry.time }}
                  </button>
                  <div>
                    <span
                      :class="[
                        'text-sm font-medium',
                        entry.speaker === 'agent' ? 'text-[#4285F4]' : 'text-gray-600'
                      ]"
                    >
                      {{ entry.speaker === 'agent' ? 'Agent' : 'Customer' }}:
                    </span>
                    <span class="text-gray-700 ml-2">{{ entry.text }}</span>
                  </div>
                </div>
              </div>
            </div>

            <!-- Actions -->
            <div class="bg-white rounded-xl p-6 border border-gray-200">
              <h3 class="font-medium text-gray-900 mb-4">
                System Logs
                <span class="text-sm font-normal text-gray-500">
                  ({{ call.actions.length }} entries)
                </span>
              </h3>
              <div class="space-y-3">
                <div
                  v-for="(action, index) in call.actions"
                  :key="index"
                  class="flex items-start gap-3 p-3 rounded-lg bg-gray-50"
                >
                  <component
                    :is="getLevelIcon(action.level)"
                    class="w-4 h-4 mt-0.5"
                    :class="{
                      'text-[#4285F4]': action.level === 'info',
                      'text-yellow-500': action.level === 'warning',
                      'text-red-500': action.level === 'error'
                    }"
                  />
                  <div>
                    <span class="font-medium text-gray-900">{{ action.action }}:</span>
                    <span class="text-gray-600 ml-1">{{ action.details }}</span>
                    <div class="text-xs text-gray-400 mt-1">
                      {{ new Date(action.timestamp).toLocaleTimeString() }}
                    </div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>