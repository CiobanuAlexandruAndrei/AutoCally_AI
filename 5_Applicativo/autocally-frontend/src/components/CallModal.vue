<template>
  <div class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
    <div class="bg-white rounded-xl w-full max-w-md p-6">
      <!-- Call Header -->
      <div class="text-center mb-6">
        <div class="w-20 h-20 rounded-full flex items-center justify-center mx-auto mb-4"
             :class="[
               isLoading ? 'bg-gray-100' :
               isListening ? 'bg-green-100 animate-pulse' : 
               isAssistantSpeaking ? 'bg-blue-100 animate-pulse' : 
               'bg-blue-100'
             ]">
          <Phone v-if="!isLoading" class="w-8 h-8" 
                :class="[
                  isListening ? 'text-green-600' : 
                  isAssistantSpeaking ? 'text-blue-600' : 
                  'text-blue-600'
                ]" />
          <div v-else class="animate-spin rounded-full h-8 w-8 border-b-2 border-gray-600"></div>
        </div>
        <h2 class="text-lg font-medium">Voice Call</h2>
        <p class="text-gray-500 text-sm">{{ status }}</p>
      </div>

      <!-- Call Controls -->
      <div class="flex justify-center gap-4">
        <!-- Start Call Button -->
        <button 
          v-if="!callStarted"
          @click="handleStartCall"
          class="p-4 bg-green-100 text-green-600 rounded-full hover:bg-green-200 transition-colors"
          :disabled="isLoading"
        >
          <Phone class="w-6 h-6" />
        </button>

        <!-- End Call Button -->
        <button 
          v-if="callStarted"
          @click="endCall"
          class="p-4 bg-red-100 text-red-600 rounded-full hover:bg-red-200 transition-colors"
          :disabled="isLoading"
        >
          <PhoneOff class="w-6 h-6" />
        </button>

        <!-- Mute Button -->
        <button 
          v-if="callStarted && !isMuted && !isLoading"
          @click="toggleMute"
          class="p-4 bg-gray-100 text-gray-600 rounded-full hover:bg-gray-200 transition-colors"
          :class="{ 'bg-green-100 text-green-600': isListening }"
        >
          <Mic class="w-6 h-6" />
        </button>
        <button 
          v-if="callStarted && isMuted && !isLoading"
          @click="toggleMute"
          class="p-4 bg-gray-100 text-gray-600 rounded-full hover:bg-gray-200 transition-colors"
        >
          <MicOff class="w-6 h-6" />
        </button>
        
        <!-- Debug - Test Audio Button -->
        <button 
          v-if="socket.connected"
          @click="playTestTone"
          class="p-4 bg-yellow-100 text-yellow-600 rounded-full hover:bg-yellow-200 transition-colors"
          title="Play test tone"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-6 h-6">
            <path d="M2 10c0-9 9-9 9-9v7c0 9-9 9-9 9z"></path>
            <path d="M15 8a5 5 0 1 1 0 8"></path>
          </svg>
        </button>
        
        <!-- Debug - Simple Text Ping -->
        <button 
          @click="sendDebugPing"
          class="p-4 bg-purple-100 text-purple-600 rounded-full hover:bg-purple-200 transition-colors"
          title="Send debug ping"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-6 h-6">
            <path d="M12 12m-9 0a9 9 0 1 0 18 0a9 9 0 1 0 -18 0"></path>
            <path d="M12 12m-1 0a1 1 0 1 0 2 0a1 1 0 1 0 -2 0"></path>
          </svg>
        </button>

        <!-- Debug - Basic WebSocket Test -->
        <button 
          @click="simpleSocketTest"
          class="p-4 bg-green-100 text-green-600 rounded-full hover:bg-green-200 transition-colors"
          title="Basic WebSocket Test"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-6 h-6">
            <path d="M22 12h-4l-3 9L9 3l-3 9H2"></path>
          </svg>
        </button>

        <!-- Debug - Connection Test Button -->
        <button 
          @click="diagnosticConnectionTest"
          class="p-4 bg-blue-100 text-blue-600 rounded-full hover:bg-blue-200 transition-colors"
          title="Test WebSocket Connection"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-6 h-6">
            <circle cx="12" cy="12" r="10"></circle>
            <line x1="12" y1="16" x2="12" y2="12"></line>
            <line x1="12" y1="8" x2="12.01" y2="8"></line>
          </svg>
        </button>
        
        <!-- Debug - Request Audio Button -->
        <button 
          v-if="callId"
          @click="requestAudio"
          class="p-4 bg-orange-100 text-orange-600 rounded-full hover:bg-orange-200 transition-colors"
          title="Request Pending Audio"
        >
          <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round" class="w-6 h-6">
            <path d="M14.5 4h-5L7 7H4a2 2 0 0 0-2 2v9a2 2 0 0 0 2 2h16a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-3l-2.5-3z"></path>
            <path d="M12 13.5V17"></path>
            <path d="M12 10h.01"></path>
          </svg>
        </button>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, onBeforeUnmount, computed } from 'vue'
import { Phone, PhoneOff, Mic, MicOff } from 'lucide-vue-next'
import { testCallsApi } from '@/services/api'
import { socket, connectSocket, testConnection, debugSocketConnection } from '@/services/socket'
import { useAuthStore } from '@/stores/auth'
import { assistantsApi } from '@/services/api'

// Add TypeScript interface for window's audioNodesRef
declare global {
  interface Window {
    AudioContext: typeof AudioContext
    webkitAudioContext: typeof AudioContext
    audioNodesRef: {
      [key: string]: {
        sourceNode: MediaStreamAudioSourceNode
        processor: ScriptProcessorNode
      }
    }
  }
}

const props = defineProps<{
  assistantId?: string | number
}>()

const emit = defineEmits<{
  (e: 'close'): void
}>()

const isMuted = ref(false)
const status = ref('Connecting...')
const isLoading = ref(true)
const callId = ref<number | null>(null)
const phoneNumberId = ref<number | null>(null)
const audioContext = ref<AudioContext | null>(null)
const audioQueue = ref<Uint8Array[]>([])
const isPlaying = ref(false)
const isListening = ref(false)
const isAssistantSpeaking = ref(false)
const mediaRecorder = ref<MediaRecorder | null>(null)
const isRecording = computed(() => mediaRecorder.value?.state === 'recording')
const callStarted = ref(false)
const currentTime = ref(0)

// Add connection monitoring and heartbeat
const connectionStatus = ref('disconnected');
const lastHeartbeat = ref(Date.now());
const connectionMonitor = ref<number | null>(null);

const processedGreetings = ref(new Set())

const resampleAudio = (audioData: Float32Array, fromSampleRate: number, toSampleRate: number): Float32Array => {
  if (fromSampleRate === toSampleRate) {
    return audioData
  }
  
  const ratio = fromSampleRate / toSampleRate
  const newLength = Math.round(audioData.length / ratio)
  const result = new Float32Array(newLength)
  
  for (let i = 0; i < newLength; i++) {
    const position = i * ratio
    const index = Math.floor(position)
    const fraction = position - index
    
    let sum = 0
    let count = 0
    
    const windowSize = Math.min(4, Math.ceil(ratio))
    for (let j = 0; j < windowSize; j++) {
      if (index + j < audioData.length) {
        sum += audioData[index + j]
        count++
      }
    }
    
    if (count > 0) {
      const filtered = sum / count
      if (index + 1 < audioData.length) {
        const interpolated = audioData[index] * (1 - fraction) + audioData[index + 1] * fraction
        result[i] = (filtered + interpolated) * 0.5
      } else {
        result[i] = filtered
      }
    } else {
      result[i] = 0
    }
  }
  
  return result
}

const toggleMute = () => {
  isMuted.value = !isMuted.value
  
  if (socket.connected && callId.value) {
    const muteEvent: SetMuteEvent = {
      call_id: callId.value.toString(),
      muted: isMuted.value
    };
    socket.emit('set_mute', muteEvent);
  }
}

interface PhoneNumber {
  id: number;
  phone_number: string;
  assistants: Array<{
    id: string;
    name: string;
  }>;
}

interface CallStartedEvent {
  call_id: string;
  phone_number_id?: string | undefined;
}

interface AudioDataEvent {
  call_id: string;
  audio: string;
}

interface SetMuteEvent {
  call_id: string;
  muted: boolean;
}

interface AudioChunkResponse {
  call_id: string;
  audio?: {
    data: string | Uint8Array;
    format: 'base64' | 'raw';
    encoding?: string;
    sample_rate?: number;
  } | null;
  final?: boolean;
  first_chunk_time?: number;
  is_greeting?: boolean;
  chunks_sent?: number;
}

interface CallReadyResponse {
  call_id: string;
  phone_number_id?: string;
}

interface CallEndedResponse {
  call_id: string;
}

interface ErrorResponse {
  message: string;
}

interface TranscriptChunkResponse {
  call_id: string;
  transcript?: string;
}

const startConnectionMonitoring = () => {
  connectionStatus.value = socket.connected ? 'connected' : 'disconnected';
  
  // Clear any existing monitor
  if (connectionMonitor.value) {
    window.clearInterval(connectionMonitor.value);
  }
  
  // Start the heartbeat pinger
  const heartbeatInterval = window.setInterval(() => {
    if (socket.connected && callId.value) {
      try {
        // Send a heartbeat ping
        socket.emit('simple_test', { 
          type: 'heartbeat', 
          timestamp: Date.now(),
          call_id: callId.value.toString()
        });
        lastHeartbeat.value = Date.now();
      } catch (error) {
        console.error('❌ [ERROR] Failed to send heartbeat:', error);
      }
    }
  }, 5000); // Send heartbeat every 5 seconds
  
  // Start the monitor
  connectionMonitor.value = window.setInterval(() => {
    const currentStatus = socket.connected ? 'connected' : 'disconnected';
    
    // Check if status changed
    if (currentStatus !== connectionStatus.value) {
      console.log(`🔌 [SOCKET] Connection status changed: ${connectionStatus.value} -> ${currentStatus}`);
      connectionStatus.value = currentStatus;
      
      // If reconnected, try to reinitialize the call
      if (currentStatus === 'connected' && callId.value && callStarted.value) {
        console.log('🔌 [SOCKET] Reconnected during active call, attempting recovery');
        recoverCall();
      }
    }
    
    // Check heartbeat age if we think we're connected
    if (socket.connected) {
      const heartbeatAge = Date.now() - lastHeartbeat.value;
      if (heartbeatAge > 15000) { // 15 seconds without heartbeat response
        console.warn(`🔌 [SOCKET] No heartbeat for ${heartbeatAge}ms, connection may be stale`);
        
        // Force reconnection
        socket.disconnect();
        setTimeout(() => {
          console.log('🔌 [SOCKET] Attempting reconnection after stale connection');
          socket.connect();
        }, 1000);
      }
    }
  }, 2000); // Check every 2 seconds
  
  console.log('🔌 [SOCKET] Started connection monitoring');
};

const recoverCall = () => {
  console.log('🔌 [SOCKET] Attempting call recovery')
  
  // Re-emit call_started to trigger server-side recovery
  if (callId.value) {
    const callStartedEvent: CallStartedEvent = {
      call_id: callId.value.toString(),
      phone_number_id: phoneNumberId.value?.toString()
    };
    
    console.log('🔌 [SOCKET] Re-emitting call_started for recovery:', callStartedEvent);
    socket.emit('call_started', callStartedEvent);
    
    // Request any pending audio after a short delay
    setTimeout(() => {
      console.log('🔌 [SOCKET] Requesting any pending audio after recovery');
      requestAudio();
    }, 500);
    
    status.value = 'Reconnected - Recovering call state...';
  }
};

// Simplify socket connection and event handlers
const setupSocketHandlers = () => {
  console.log('Setting up socket handlers')
  
  // First remove any existing handlers to avoid duplicates
  socket.off('audio_chunk')
  socket.off('call_ready') 
  socket.off('call_ended')
  socket.off('error')
  socket.off('transcript_chunk')
  socket.off('connection_established')
  socket.off('disconnect')
  socket.off('connect_error')
  socket.off('simple_test_response')
  socket.off('debug_pong')
  socket.off('stt_transcript')
  socket.off('transcript')
  
  // Basic socket connection events
  socket.on('connect', () => {
    console.log('Socket connected with ID:', socket.id)
    status.value = 'Connected to server'
    
    // If we have an active call, re-emit call_started
    if (callId.value && callStarted.value) {
      console.log('Re-emitting call_started after reconnection')
      socket.emit('call_started', {
        call_id: callId.value.toString(),
        phone_number_id: phoneNumberId.value?.toString()
      })
    }
  })
  
  socket.on('connection_established', (data) => {
    console.log('🔌 [SOCKET] Connection established, details:', data)
    status.value = 'Connection established'
    
    // If we have an active call, request any pending audio
    if (callId.value) {
      // Use a short delay to ensure server is ready
      setTimeout(() => {
        console.log('🔌 [SOCKET] Requesting any pending audio after connection established')
        requestAudio()
      }, 300)
    }
    
    // Wait a short time to allow events to be registered
    setTimeout(() => {
      testSocketConnection()
    }, 500)
    
    // Try again in 2 seconds
    setTimeout(() => {
      console.log('🔌 [SOCKET] Sending second test ping after 2 seconds')
      testSocketConnection()
    }, 2000)
  })
  
  socket.on('disconnect', (reason) => {
    console.warn(`Socket disconnected: ${reason}`)
    status.value = `Disconnected: ${reason}`
    
    if (reason === 'io server disconnect') {
      socket.connect()
    }
  })
  
  socket.on('connect_error', (error) => {
    console.error('Socket connection error:', error)
    status.value = `Connection error: ${error.message}`
  })
  
  // Call-specific events
  socket.on('call_ready', (data) => {
    console.log('Call ready event received:', data)
    if (!callId.value || data.call_id !== callId.value.toString()) {
      console.warn('Call ready event for different call ID')
      return
    }
    
    status.value = 'Connected - Ready to talk'
    isListening.value = true
    
    // Start STT process
    socket.emit('start_stt', { call_id: callId.value.toString() })
  })
  
  socket.on('call_ended', (data) => {
    console.log('Call ended event received:', data)
    if (!callId.value) {
      setTimeout(() => emit('close'), 1000)
      return
    }
    
    status.value = 'Call ended'
    isListening.value = false
    isAssistantSpeaking.value = false
    callStarted.value = false
    
    cleanupCall()
    setTimeout(() => emit('close'), 1500)
  })
  
  socket.on('error', (data) => {
    console.error('Socket error:', data)
    status.value = `Error: ${data.message}`
    isListening.value = false
    isAssistantSpeaking.value = false
  })
  
  socket.on('transcript_chunk', (data) => {
    console.log('Received transcript_chunk:', data.transcript)
    if (!callId.value || data.call_id !== callId.value.toString()) return
    
    isListening.value = true
    isAssistantSpeaking.value = false
    
    if (data.transcript) {
      status.value = `You: ${data.transcript}`
    }
  })
  
  // Add handler for stt_transcript events
  socket.on('stt_transcript', (data) => {
    console.log('Received stt_transcript:', data)
    if (!callId.value || data.call_id !== callId.value.toString()) return
    
    isListening.value = true
    isAssistantSpeaking.value = false
    
    if (data.transcript) {
      status.value = `You: ${data.transcript}`
    }
    
    // If this is a final transcript, show a visual indicator
    if (data.final === true) {
      console.log('Final transcript received - waiting for assistant response')
      status.value = `You: ${data.transcript} (processing...)`
    }
  })
  
  // Add handler for transcript events (assistant responses)
  socket.on('transcript', (data) => {
    console.log('Received assistant transcript:', data)
    if (!callId.value || data.call_id !== callId.value.toString()) return
    
    isListening.value = false
    
    if (data.text) {
      status.value = `Assistant: ${data.text.substring(0, 80)}${data.text.length > 80 ? '...' : ''}`
    }
  })
  
  // Audio handling event
  socket.on('audio_chunk', async (data) => {
    try {
      console.log('Received audio chunk:', {
        hasData: !!data,
        callId: data?.call_id,
        expectedCallId: callId.value,
        hasAudioData: !!data?.audio?.data,
        isTestTone: data?.is_test_tone,
        isGreeting: data?.is_greeting,
        encoding: data?.audio?.encoding,
        isFinal: !!data.final
      })

      // Track audio reception time
      if (data && !data.is_test_tone) {
        localStorage.setItem('lastAudioReceived', Date.now().toString())
      }

      // Skip if not for this call (unless it's a test tone)
      if (!data?.is_test_tone && (!data || !data.call_id || data.call_id !== callId.value?.toString())) {
        console.warn('Skipping audio chunk - not for this call')
        return
      }

      // Handle final marker
      if (data.final) {
        console.log(`Audio playback complete: ${data.chunks_sent} chunks played`)
        isAssistantSpeaking.value = false
        
        // If this was a greeting, update the UI
        if (data.is_greeting) {
          status.value = 'Call connected - Waiting for your voice input'
        }
        return
      }

      // Skip if no audio data
      if (!data.audio?.data) {
        console.warn('Received empty audio chunk')
        return
      }
      
      // For greeting chunks, check if we've already processed this greeting for this call
      if (data.is_greeting) {
        // Create a unique identifier for the greeting
        const greetingId = `greeting-${data.call_id}`
        
        // If we have a first chunk and have already seen this greeting, skip it
        if (data.first_chunk_time && processedGreetings.value.has(greetingId)) {
          console.log('Skipping duplicate greeting for call', data.call_id)
          return
        }
        
        // Mark that we're processing this greeting
        if (data.first_chunk_time) {
          processedGreetings.value.add(greetingId)
          status.value = 'Playing greeting...'
        }
      }

      // Set speaking state
      isAssistantSpeaking.value = true

      // Ensure audio context is ready
      if (!audioContext.value) {
        console.log('Creating new AudioContext for playback')
        const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext
        audioContext.value = new AudioContextClass()
      }

      // Resume context if suspended
      if (audioContext.value.state === 'suspended') {
        console.log('Resuming suspended audio context')
        await audioContext.value.resume()
      }
      
      // Check if audio context is ready now
      if (audioContext.value.state !== 'running') {
        console.error(`Audio context not ready: ${audioContext.value.state}`)
        return
      }

      // Process and play audio data
      let rawData
      
      // Handle raw binary data (most common case)
      if (data.audio.data instanceof Uint8Array) {
        rawData = data.audio.data
      } else if (typeof data.audio.data === 'string') {
        // Try to convert string to binary
        const binaryString = atob(data.audio.data)
        rawData = new Uint8Array(binaryString.length)
        for (let i = 0; i < binaryString.length; i++) {
          rawData[i] = binaryString.charCodeAt(i)
        }
        console.log(`Converted string data to Uint8Array, length: ${rawData.length}`)
      } else if (data.audio.data instanceof ArrayBuffer) {
        rawData = new Uint8Array(data.audio.data)
      } else {
        // Try as array-like
        rawData = new Uint8Array(data.audio.data)
      }
      
      // Log data size to help debugging
      console.log(`Processing audio chunk, size: ${rawData.length} bytes, encoding: ${data.audio.encoding}, greeting: ${data.is_greeting}`)
      
      // Handle the audio based on encoding format
      // Check for PCM_F32LE format
      if (data.audio.encoding === 'pcm_f32le') {
        // For PCM_F32LE (32-bit float), we need to convert the Uint8Array to Float32Array
        // Each sample is 4 bytes (32 bits)
        const float32Data = new Float32Array(rawData.buffer)
        const audioBuffer = audioContext.value.createBuffer(1, float32Data.length, 22050)
        const channelData = audioBuffer.getChannelData(0)
        
        // Copy the float32 data directly
        for (let i = 0; i < float32Data.length; i++) {
          channelData[i] = float32Data[i]
        }
        
        // Create and play the audio source
        const source = audioContext.value.createBufferSource()
        source.buffer = audioBuffer
        source.connect(audioContext.value.destination)
        source.start()
        
        // For debugging, log the expected duration
        const duration = float32Data.length / 22050
        console.log(`Started playback of PCM_F32LE audio chunk, duration: ${duration.toFixed(2)}s`)
      } else {
        // Default handling for int16 (or other formats)
        try {
          const audioData = new Int16Array(rawData.buffer)
          const audioBuffer = audioContext.value.createBuffer(1, audioData.length, 22050)
          const channelData = audioBuffer.getChannelData(0)
          
          // Convert Int16 to Float32
          for (let i = 0; i < audioData.length; i++) {
            channelData[i] = audioData[i] / 32768.0
          }
    
          // Create and play source
          const source = audioContext.value.createBufferSource()
          source.buffer = audioBuffer
          source.connect(audioContext.value.destination)
          source.start()
          
          // For debugging, log the expected duration
          const duration = audioData.length / 22050
          console.log(`Started playback of int16 audio chunk, duration: ${duration.toFixed(2)}s`)
        } catch (error) {
          console.warn('Failed direct buffer conversion, trying manual conversion', error)
          // Fallback method - manual conversion
          const audioData = new Int16Array(Math.floor(rawData.length / 2))
          for (let i = 0; i < rawData.length; i += 2) {
            if (i + 1 < rawData.length) {
              audioData[i / 2] = (rawData[i] | (rawData[i + 1] << 8))
            } else {
              audioData[i / 2] = rawData[i]
            }
          }
          
          // Create audio buffer
          const audioBuffer = audioContext.value.createBuffer(1, audioData.length, 22050)
          const channelData = audioBuffer.getChannelData(0)
          
          // Convert Int16 to Float32
          for (let i = 0; i < audioData.length; i++) {
            channelData[i] = audioData[i] / 32768.0
          }
    
          // Create and play source
          const source = audioContext.value.createBufferSource()
          source.buffer = audioBuffer
          source.connect(audioContext.value.destination)
          source.start()
          
          // For debugging, log the expected duration
          const duration = audioData.length / 22050
          console.log(`Started playback of manually converted audio chunk, duration: ${duration.toFixed(2)}s`)
        }
      }

    } catch (error) {
      console.error('Error processing audio chunk:', error)
      isAssistantSpeaking.value = false
    }
  })
  
  // Test event handlers
  socket.on('debug_pong', (data) => {
    console.log('Received debug pong:', data)
    status.value = `Debug pong received: ${data.text}`
  })
  
  socket.on('simple_test_response', (data) => {
    console.log('Received simple test response:', data)
    status.value = `Simple test response: ${data.text}`
  })
  
  // Add handler for server ping messages
  socket.on('server_ping', (data) => {
    console.log('🔌 [SOCKET] Received server ping:', data)
    
    // Respond with a pong to confirm connection is active
    if (socket.connected && data.call_id) {
      socket.emit('client_pong', {
        call_id: data.call_id,
        timestamp: Date.now(),
        received_ping_timestamp: data.timestamp,
        ping_latency: Date.now() - data.timestamp
      })
      
      // If we have pending audio, request it (server pings are a good time to check)
      if (callId.value && data.call_id === callId.value.toString()) {
        // Only trigger audio request if it's been at least 3 seconds since last one
        const lastAudioRequestTime = localStorage.getItem('lastAudioRequest') || 0
        const now = Date.now()
        if (now - Number(lastAudioRequestTime) > 3000) {
          console.log('🔌 [SOCKET] Requesting audio after server ping')
          requestAudio()
          localStorage.setItem('lastAudioRequest', now.toString())
        }
      }
    }
  })
}

const startCall = async () => {
  try {
    console.log('Starting call...')
    isLoading.value = true
    status.value = 'Connecting...'
    
    if (!props.assistantId) {
      console.error('Missing assistant ID')
      status.value = 'Missing assistant ID'
      return
    }
    
    const assistantResponse = await assistantsApi.getById(props.assistantId)
    
    if (!assistantResponse.phone_number_id) {
      console.error('Assistant has no configured phone number')
      status.value = 'Assistant has no configured phone number'
      isLoading.value = false
      return
    }
    
    phoneNumberId.value = Number(assistantResponse.phone_number_id)
    
    // Start test call with the API
    const response = await testCallsApi.startTestCall(phoneNumberId.value)
    
    if (response.status === 'success' && response.call_id) {
      callId.value = response.call_id
      status.value = 'Connecting to server...'
      
      const authStore = useAuthStore()
      
      if (!authStore.token) {
        console.error('Authentication error: No token available')
        status.value = 'Authentication error: No token available'
        return
      }
      
      // Simplified socket connection
      // Set up socket handlers first
      setupSocketHandlers()
      
      // Connect socket with auth token and parameters
      const callIdStr = callId.value?.toString() || ''
      const phoneNumberIdStr = phoneNumberId.value?.toString() || ''
      
      connectSocket(authStore.token, {
        call_id: callIdStr,
        phone_number_id: phoneNumberIdStr
      })
      
      // Wait for connection
      await new Promise<void>((resolve, reject) => {
        const timeout = setTimeout(() => {
          reject(new Error('Socket connection timeout'))
        }, 10000)
        
        // Listen for successful connection
        socket.once('connect', () => {
          clearTimeout(timeout)
          resolve()
        })
        
        // Listen for connection error
        socket.once('connect_error', (error) => {
          clearTimeout(timeout)
          reject(error)
        })
      })
      
      // Send call_started event to start the actual call
      console.log('Emitting call_started event')
      socket.emit('call_started', {
        call_id: callId.value?.toString() ?? '',
        phone_number_id: phoneNumberId.value?.toString()
      })
      
      status.value = 'Connected - Waiting for greeting'
      callStarted.value = true
      
    } else {
      status.value = 'Failed to start call: ' + (response.error || 'Unknown error')
    }
  } catch (error) {
    console.error('Error starting call:', error)
    status.value = 'Error starting call'
    if (callId.value) {
      await endCall()
    }
  } finally {
    isLoading.value = false
  }
}

const endCall = async () => {
  try {
    if (callId.value) {
      status.value = 'Ending call...'
      console.log('Ending call...')
      
      if (!callStarted.value) {
        console.log('Call not started, just closing')
        emit('close')
        return
      }
      
      // Clear the processed greetings set
      processedGreetings.value.clear();
      
      // Cleanup resources
      if (mediaRecorder.value && mediaRecorder.value.state === 'recording') {
        mediaRecorder.value.stop()
      }
      
      if (audioContext.value) {
        try {
        await audioContext.value.close()
        } catch (err) {
          console.error('Error closing audio context:', err)
        }
        audioContext.value = null
      }
      
      audioQueue.value = []
      callStarted.value = false
      
      await testCallsApi.endTestCall(callId.value)
      
      socket.off('audio_chunk')
      socket.off('call_ready')
      socket.off('call_ended')
      socket.off('error')
      socket.off('transcript_chunk')
      
      emit('close')
    } else {
      emit('close')
    }
  } catch (error) {
    console.error('Error ending call:', error)
    status.value = 'Error ending call'
    
    setTimeout(() => {
      emit('close')
    }, 2000)
  }
}

const unlockAudioContext = async () => {
  try {
    // Create audio context if it doesn't exist
    if (!audioContext.value) {
      const AudioContextClass = window.AudioContext || window.webkitAudioContext;
      audioContext.value = new AudioContextClass();
      console.log('🔊 [AUDIO] Created new AudioContext with sample rate:', audioContext.value.sampleRate);
    }

    // Check if context is suspended
    if (audioContext.value.state === 'suspended') {
      console.log('🔊 [AUDIO] Resuming suspended audio context');
      await audioContext.value.resume();
      
      // Play a silent buffer to unlock the audio
      const buffer = audioContext.value.createBuffer(1, 1, 22050);
      const source = audioContext.value.createBufferSource();
      source.buffer = buffer;
      source.connect(audioContext.value.destination);
      source.start();
      
      // Play a short beep to confirm audio system is active
      const beepBuffer = audioContext.value.createBuffer(1, 1000, 22050);
      const beepData = beepBuffer.getChannelData(0);
      for (let i = 0; i < beepData.length; i++) {
        beepData[i] = Math.sin(i * 0.05) * 0.1; // Low volume sine wave
      }
      const beepSource = audioContext.value.createBufferSource();
      beepSource.buffer = beepBuffer;
      beepSource.connect(audioContext.value.destination);
      beepSource.start();
    }

    console.log('🔊 [AUDIO] Audio context state:', audioContext.value.state);
    return true;
  } catch (error) {
    console.error('❌ [ERROR] Failed to unlock audio context:', error);
    return false;
  }
};

const handleStartCall = async () => {
  try {
    console.log('📞 [CALL] Starting call initialization...');
    
    // Clear the processed greetings set when starting a new call
    processedGreetings.value.clear();
    
    // Try to unlock audio first, as this needs user interaction
    await unlockAudioContext();
    
    await initializeMicrophone();
    await startCall();
    callStarted.value = true;
    
    // TEST SOCKET CONNECTION IMMEDIATELY AFTER CALL START
    testSocketConnection();
  } catch (error) {
    console.error('❌ [ERROR] Failed to start call:', error);
    status.value = 'Failed to start call: ' + (error instanceof Error ? error.message : String(error));
  }
};

const testSocketConnection = () => {
  if (!socket.connected || !callId.value) {
    console.warn('🔌 [SOCKET] Cannot test - socket disconnected or no call ID')
    return
  }

  // Request pending audio first
  requestAudio()

  // Send a test ping with timestamp and call ID
  const testData = {
    timestamp: Date.now(),
    message: 'Testing socket connection and audio delivery',
    call_id: callId.value.toString()
  }

  console.log('🔌 [SOCKET] Sending test ping to trigger audio delivery:', testData)
  socket.emit('test_ping', testData)

  // Log current socket listeners
  console.log('🔌 [SOCKET] Current socket listeners:', {
    audioChunk: socket.hasListeners('audio_chunk'),
    callReady: socket.hasListeners('call_ready'),
    callEnded: socket.hasListeners('call_ended'),
    error: socket.hasListeners('error'),
    transcriptChunk: socket.hasListeners('transcript_chunk')
  })

  // Log socket connection details
  console.log('🔌 [SOCKET] Connection details:', {
    connected: socket.connected,
    id: socket.id,
    callId: callId.value,
    audioContext: {
      exists: !!audioContext.value,
      state: audioContext.value?.state,
      sampleRate: audioContext.value?.sampleRate
    }
  })
}

// Function to explicitly request any pending audio from the server
const requestAudio = () => {
  if (!socket.connected || !callId.value) {
    console.warn('Cannot request audio: socket disconnected or no call ID')
    return
  }
  
  console.log('Explicitly requesting pending audio for call:', callId.value)
  socket.emit('request_audio', {
    call_id: callId.value.toString(),
    timestamp: Date.now()
  })
  
  // Track this request time
  localStorage.setItem('lastAudioRequest', Date.now().toString())
  
  // Set a timeout to try again if we don't receive a response
  setTimeout(() => {
    // Check if we've received audio since our request
    const lastAudioRequestTime = Number(localStorage.getItem('lastAudioRequest') || 0)
    const now = Date.now()
    
    // If it's been more than 5 seconds without audio, try again
    if (now - lastAudioRequestTime > 5000 && socket.connected && callId.value) {
      console.log('🔌 [SOCKET] No audio received after 5s, retrying request')
      socket.emit('request_audio', {
        call_id: callId.value.toString(),
        timestamp: Date.now(),
        retry: true
      })
    }
  }, 5000)
}

// Add test_audio_result handler
socket.on('test_audio_result', (data) => {
  console.log('Received audio request result:', data)
  if (data.success) {
    status.value = `Found ${data.chunks_pending} audio chunks, delivering...`
    // Record time for success to compare against actual delivery
    localStorage.setItem('audioRequestSuccess', Date.now().toString())
    localStorage.setItem('expectedChunks', data.chunks_pending.toString())
  } else {
    console.warn(`Audio request unsuccessful: ${data.message}`)
    status.value = `No pending audio found: ${data.message}`
    
    // If there's an error with the call ID or no chunks, make sure we still have a good connection
    if (data.message === 'Call not found' || data.message === 'No pending audio found') {
      // Verify connection with a simple ping
      socket.emit('simple_test', { message: 'Connection verification after audio request failure' })
    }
  }
})

const initializeMicrophone = async () => {
  try {
    console.log('🎤 [MIC] Requesting microphone permissions...');
    const stream = await navigator.mediaDevices.getUserMedia({ audio: true });
    console.log('🎤 [MIC] Microphone access granted');
    
    // Create AudioContext - Add check to see if it's already created
    if (!audioContext.value) {
      try {
        console.log('🔊 [AUDIO] Creating new AudioContext');
        const AudioContextClass = window.AudioContext || (window as any).webkitAudioContext;
        if (!AudioContextClass) {
          throw new Error('Web Audio API not supported in this browser');
        }
        audioContext.value = new AudioContextClass();
        console.log('🔊 [AUDIO] AudioContext created with sample rate:', audioContext.value.sampleRate);
        
        // Check if context is suspended and try to resume it
        if (audioContext.value.state === 'suspended') {
          console.log('🔊 [AUDIO] AudioContext is suspended, attempting to resume...');
          await audioContext.value.resume();
          console.log('🔊 [AUDIO] AudioContext resumed, new state:', audioContext.value.state);
        }
      } catch (err: any) {
        console.error('❌ [ERROR] Failed to create AudioContext:', err);
        throw new Error('Failed to initialize audio system: ' + err.message);
      }
    } else {
      console.log('🔊 [AUDIO] Using existing AudioContext');
      // Check if context is suspended and try to resume it
      if (audioContext.value.state === 'suspended') {
        console.log('🔊 [AUDIO] AudioContext is suspended, attempting to resume...');
        await audioContext.value.resume();
        console.log('🔊 [AUDIO] AudioContext resumed, new state:', audioContext.value.state);
      }
    }
    
    const sourceNode = audioContext.value.createMediaStreamSource(stream);
    
    const processor = audioContext.value.createScriptProcessor(2048, 1, 1);
    
    sourceNode.connect(processor);
    processor.connect(audioContext.value.destination);
    
    // Store references to audio nodes to properly clean up later
    const audioNodes = {
      sourceNode,
      processor
    };
    
    // Keep reference for cleanup
    if (!window.audioNodesRef) {
      window.audioNodesRef = {};
    }
    window.audioNodesRef[callId.value?.toString() || 'default'] = audioNodes;
    
    // Also set up mediaRecorder for backward compatibility
    mediaRecorder.value = new MediaRecorder(stream);
    mediaRecorder.value.start(100);
    
    // Handle microphone stream processing with ScriptProcessor
    processor.onaudioprocess = (e: AudioProcessingEvent) => {
      // Skip processing if muted or no connection
      if (isMuted.value || !callId.value || !socket.connected) return;
      
      // Get raw audio data from microphone
      const inputData = e.inputBuffer.getChannelData(0);
      
      // Resample to 16kHz for STT processing
      const resampledData = resampleAudio(inputData, audioContext.value?.sampleRate || 44100, 16000);
      
      // Convert Float32Array to Int16Array (16-bit PCM)
      const int16Data = new Int16Array(resampledData.length);
      for (let i = 0; i < resampledData.length; i++) {
        // Better float32 to int16 conversion with proper scaling
        const s = Math.max(-1, Math.min(1, resampledData[i]));
        int16Data[i] = s < 0 ? s * 0x8000 : s * 0x7FFF;
      }
      
      // Send audio chunk to server for processing
      // Make sure to match the expected format in socket_events.py
      socket.emit('stt_audio_chunk', {
        call_id: callId.value.toString(),
        audio: int16Data,
        sample_rate: 16000,
        format: 'linear16'
      });
      
      // Visual indicator that we're sending audio
      isListening.value = true;
    };
    
    console.log('🎤 [MIC] Microphone setup complete with continuous streaming');
    status.value = 'Microphone activated - Ready to talk';
  } catch (error) {
    console.error('❌ [ERROR] Failed to initialize microphone:', error);
    status.value = 'Failed to initialize microphone. Please check permissions.';
    throw error;
  }
};

const cleanupCall = () => {
  console.log('Executing call cleanup procedure');
  
  // Clean up audio nodes
  if (window.audioNodesRef && window.audioNodesRef[callId.value?.toString() || 'default']) {
    try {
      const nodes = window.audioNodesRef[callId.value?.toString() || 'default'];
      if (nodes.processor) {
        nodes.processor.onaudioprocess = null;
        nodes.processor.disconnect();
      }
      
      if (nodes.sourceNode) {
        nodes.sourceNode.disconnect();
      }
      
      delete window.audioNodesRef[callId.value?.toString() || 'default'];
    } catch (error) {
      console.error('Error cleaning up audio nodes:', error);
    }
  }
  
  if (mediaRecorder.value) {
    try {
      if (mediaRecorder.value.state === 'recording') {
        console.log('Stopping active media recorder');
        mediaRecorder.value.stop();
      }
      if (mediaRecorder.value.stream) {
        console.log('Stopping media recorder tracks');
        mediaRecorder.value.stream.getTracks().forEach(track => {
          track.stop();
        });
      }
    } catch (error) {
      console.error('Error stopping media recorder:', error);
    }
    mediaRecorder.value = null;
  }
  
  if (audioContext.value) {
    try {
      console.log('Closing audio context');
      audioContext.value.close();
    } catch (error) {
      console.error('Error closing audio context:', error);
    }
    audioContext.value = null;
  }
  
  audioQueue.value = [];
  isPlaying.value = false;
  
  isListening.value = false;
  isAssistantSpeaking.value = false;
  isMuted.value = false;
  
  // Clear the processed greetings set
  processedGreetings.value.clear();
  
  try {
    console.log('Removing socket event listeners');
    socket.off('audio_chunk');
    socket.off('call_ready');
    socket.off('call_ended');
    socket.off('error');
    socket.off('transcript_chunk');
    socket.off('connection_established');
    socket.off('stt_started');
    socket.off('stt_stopped');
    socket.off('stt_transcript');
    socket.off('transcript');
  } catch (error) {
    console.error('Error removing socket listeners:', error);
  }
  
  console.log('Call cleanup completed');
}

onMounted(async () => {
  status.value = 'Ready to start call'
  isLoading.value = false
})

onBeforeUnmount(() => {
  if (callId.value) {
    endCall()
  }
  
  if (audioContext.value) {
    audioContext.value.close()
  }
  
  if (mediaRecorder.value && mediaRecorder.value.state === 'recording') {
    mediaRecorder.value.stop()
  }
  
  // Clean up connection monitor
  if (connectionMonitor.value) {
    window.clearInterval(connectionMonitor.value)
    connectionMonitor.value = null
  }
  
  // Clear the processed greetings set
  processedGreetings.value.clear()
  
  socket.off('audio_chunk')
  socket.off('call_ready')
  socket.off('call_ended')
  socket.off('error')
  socket.off('transcript_chunk')
  socket.off('simple_test_response')
})

// Simple test functions
const playTestTone = () => {
  console.log('Requesting test tone')
  
  // Ensure audio context is active
  if (audioContext.value?.state === 'suspended') {
    audioContext.value.resume().then(() => {
      socket.emit('direct_test_audio')
    })
  } else {
    socket.emit('direct_test_audio')
  }
  
  status.value = 'Playing test tone...'
}

const sendDebugPing = () => {
  console.log('Sending debug ping')
  
  if (!socket.connected) {
    socket.connect()
    socket.once('connect', () => {
      emitDebugPing()
    })
    return
  }
  
  emitDebugPing()
}

const emitDebugPing = () => {
  socket.emit('debug_ping', {
    timestamp: Date.now(),
    message: 'Debug ping message',
    browser: navigator.userAgent
  })
  
  status.value = 'Sent debug ping...'
}

const simpleSocketTest = () => {
  console.log('Sending simple test message')
  
  if (!socket.connected) {
    socket.connect()
    socket.once('connect', () => {
      sendSimpleTest()
    })
    return
  }
  
  sendSimpleTest()
}

const sendSimpleTest = () => {
  socket.emit('simple_test', {
    message: 'Simple test message',
    timestamp: Date.now()
  })
  
  status.value = 'Sent simple test...'
}

// Simplified diagnostic test - just checks basic connection
const diagnosticConnectionTest = () => {
  console.log('Testing WebSocket connection')
  status.value = 'Testing connection...'
  
  // Send a simple test message
  socket.emit('simple_test', {
    message: 'Diagnostic test',
    timestamp: Date.now()
  })
  
  status.value = 'Connection test sent...'
}
</script> 