<template>
  <div 
    class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50"
    @keydown.esc="emit('close')"
    tabindex="0"
  >
    <div class="bg-white rounded-xl w-full max-w-2xl h-[600px] flex flex-col">
      <!-- Chat Header -->
      <div class="p-4 border-b flex items-center justify-between">
        <div class="flex items-center gap-3">
          <h2 class="text-lg font-medium">Chat with Assistant</h2>
          <button 
            @click="toggleTTS" 
            class="p-2 rounded-lg hover:bg-gray-100"
            :class="{ 'text-blue-500': ttsEnabled }"
          >
            <Volume2 v-if="ttsEnabled" class="w-5 h-5" />
            <VolumeX v-else class="w-5 h-5" />
          </button>
        </div>
        <button @click="handleClose" class="text-gray-500 hover:text-gray-700">
          <X class="w-5 h-5" />
        </button>
      </div>
      
      <!-- Chat Messages -->
      <div ref="chatContainer" class="flex-1 p-4 overflow-y-auto">
        <div v-for="(message, index) in messages" :key="index" 
          :class="['mb-4 flex', message.sender === 'user' ? 'justify-end' : 'justify-start']">
          <div :class="['max-w-[80%]', message.sender === 'user' ? 'items-end' : 'items-start']">
            <div :class="['rounded-lg p-3', 
              message.sender === 'user' 
                ? 'bg-blue-500 text-white' 
                : 'bg-gray-100 text-gray-800']">
              {{ message.content }}
            </div>
            <!-- Add timing display for assistant messages -->
            <div v-if="message.sender === 'assistant' && (message.llmTime || message.ttsTime)" 
              class="text-xs text-gray-500 mt-1 space-y-0.5">
              <div v-if="message.llmTime">
                <span class="font-medium">LLM Response:</span> {{ message.llmTime.toFixed(2) }}s
              </div>
              <div v-if="message.ttsTime">
                <span class="font-medium">First Audio:</span> {{ message.ttsTime.toFixed(2) }}s
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Chat Input -->
      <div class="p-4 border-t">
        <div class="flex gap-2">
          <input 
            v-model="newMessage" 
            @keyup.enter="sendMessage"
            type="text" 
            placeholder="Type your message..." 
            class="flex-1 p-2 border rounded-lg focus:outline-none focus:ring-2 focus:ring-blue-200"
          >
          <button 
            @click="toggleListening"
            class="p-2 rounded-lg hover:bg-gray-100"
            :class="{ 'text-blue-500': isListening, 'animate-pulse': isListening }"
          >
            <Mic class="w-5 h-5" />
          </button>
          <button 
            @click="sendMessage"
            class="p-2 rounded-lg bg-blue-500 text-white hover:bg-blue-600"
          >
            <SendHorizontal class="w-5 h-5" />
          </button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted, onUnmounted } from 'vue'
import { X, Mic, Volume2, VolumeX, SendHorizontal } from 'lucide-vue-next'
import { socket } from '@/services/socket'
import { useAuthStore } from '@/stores/auth'

declare global {
  interface Window {
    AudioContext: typeof AudioContext
    webkitAudioContext: typeof AudioContext
  }
}

const emit = defineEmits<{
  (e: 'close'): void
  (e: 'send', message: string): void
}>()

const props = defineProps<{
  messages: Array<{ sender: string; content: string }>
  assistantId: string
}>()

const newMessage = ref('')
const ttsEnabled = ref(false)
const isListening = ref(false)
const recognition = ref<SpeechRecognition | null>(null)
const synthesis = window.speechSynthesis
const mediaRecorder = ref<MediaRecorder | null>(null)
const audioChunks = ref<BlobEvent[]>([])

const messages = ref<Array<{
  sender: string;
  content: string;
  llmTime?: number;
  ttsTime?: number;
}>>([...props.messages])
const chatContainer = ref<HTMLElement | null>(null)
const audioContext = ref<AudioContext | null>(null)
const currentTime = ref(0)
const lastMessageId = ref<string | null>(null)

// Add these variables to store references to audio resources
const stream = ref<MediaStream | null>(null)
const processor = ref<ScriptProcessorNode | null>(null)
const sourceNode = ref<MediaStreamAudioSourceNode | null>(null)

// Initialize speech recognition
const initSpeechRecognition = async () => {
  try {
    // Request microphone access
    const mediaStream = await navigator.mediaDevices.getUserMedia({ audio: true })
    stream.value = mediaStream
    
    // Create audio context if not exists
    if (!audioContext.value) {
      audioContext.value = new (window.AudioContext || window.webkitAudioContext)()
    }
    
    if (!audioContext.value || !stream.value) {
      throw new Error('Failed to initialize audio context or stream')
    }
    
    // Create source node
    sourceNode.value = audioContext.value.createMediaStreamSource(stream.value)
    
    // Create processor node
    processor.value = audioContext.value.createScriptProcessor(2048, 1, 1)
    
    if (!sourceNode.value || !processor.value) {
      throw new Error('Failed to create audio nodes')
    }
    
    // Connect nodes
    sourceNode.value.connect(processor.value)
    processor.value.connect(audioContext.value.destination)
    
    // Rest of your existing processor setup code...
    processor.value.onaudioprocess = (e: AudioProcessingEvent) => {
      const inputData = e.inputBuffer.getChannelData(0)
      const resampledData = betterResampleAudio(inputData, audioContext.value?.sampleRate || 44100, 16000)
      
      // Convert Float32Array to Int16Array (16-bit PCM)
      const int16Data = new Int16Array(resampledData.length)
      
      for (let i = 0; i < resampledData.length; i++) {
        // Better float32 to int16 conversion with proper scaling
        const s = Math.max(-1, Math.min(1, resampledData[i]))
        int16Data[i] = s < 0 ? s * 0x8000 : s * 0x7FFF
      }
      
      // Send buffer to server with explicit format information
      socket.emit('stt_audio_chunk', {
        assistant_id: props.assistantId,
        audio: int16Data,
        sample_rate: 16000,
        format: 'linear16'
      })
    }

    // Initialize socket-based STT
    socket.emit('start_stt', {
      assistant_id: props.assistantId
    })
    
    return true
  } catch (error) {
    console.error('Error initializing speech recognition:', error)
    return false
  }
}

// Better audio resampling function
const betterResampleAudio = (
  audioData: Float32Array,
  originalSampleRate: number,
  targetSampleRate: number
): Float32Array => {
  if (originalSampleRate === targetSampleRate) {
    return audioData;
  }

  const ratio = originalSampleRate / targetSampleRate;
  const newLength = Math.round(audioData.length / ratio);
  const result = new Float32Array(newLength);
  
  // Improved resampling with anti-aliasing
  for (let i = 0; i < newLength; i++) {
    const position = i * ratio;
    const index = Math.floor(position);
    const fraction = position - index;
    
    // Apply a simple low-pass filter to prevent aliasing
    let sum = 0;
    let count = 0;
    
    // Use a small window for filtering
    const windowSize = Math.min(4, Math.ceil(ratio));
    for (let j = 0; j < windowSize; j++) {
      if (index + j < audioData.length) {
        sum += audioData[index + j];
        count++;
      }
    }
    
    if (count > 0) {
      // Blend between simple averaging and linear interpolation
      const filtered = sum / count;
      if (index + 1 < audioData.length) {
        const interpolated = audioData[index] * (1 - fraction) + audioData[index + 1] * fraction;
        result[i] = (filtered + interpolated) * 0.5;
      } else {
        result[i] = filtered;
      }
    } else {
      result[i] = 0;
    }
  }
  
  return result;
};

// Toggle speech recognition
const toggleSpeechRecognition = async () => {
  try {
    if (isListening.value) {
      await stopSpeechRecognition();
      isListening.value = false;
    } else {
      const success = await initSpeechRecognition();
      isListening.value = success;
      if (!success) {
        console.error('Failed to initialize speech recognition');
      }
    }
  } catch (error) {
    console.error('Error toggling speech recognition:', error);
    isListening.value = false;
  }
};

// Toggle TTS
const toggleTTS = () => {
  ttsEnabled.value = !ttsEnabled.value
}

// Watch for new assistant messages and speak them if TTS is enabled
watch(() => messages.value, (newMessages, oldMessages) => {
  if (ttsEnabled.value && newMessages.length > (oldMessages?.length ?? 0)) {
    const lastMessage = newMessages[newMessages.length - 1]
    if (lastMessage.sender === 'assistant' && lastMessage.content.trim()) {
      const utterance = new SpeechSynthesisUtterance(lastMessage.content)
      utterance.onend = () => {
        console.log('TTS finished speaking')
      }
      utterance.onerror = (event) => {
        console.error('TTS error:', event)
      }
      synthesis.speak(utterance)
    }
  }
}, { deep: true })

// Add this function to handle scrolling
const scrollToBottom = () => {
  if (chatContainer.value) {
    chatContainer.value.scrollTop = chatContainer.value.scrollHeight
  }
}

// Handle socket events
onMounted(() => {
  socket.connect()
  
  socket.on('stt_started', (data) => {
    if (data.assistant_id === props.assistantId) {
      console.log('STT started successfully');
      isListening.value = true;
    }
  });

  socket.on('stt_transcript', (data) => {
    if (data.assistant_id === props.assistantId) {
      newMessage.value = data.transcript;
      if (data.final) {
        sendMessage();
        newMessage.value = '';
      }
    }
  });

  socket.on('stt_stopped', (data) => {
    if (data.assistant_id === props.assistantId) {
      console.log('STT stopped');
      isListening.value = false;
    }
  });

  socket.on('chat_response', (data) => {
    if (data.assistant_id === props.assistantId) {
      const lastMessage = messages.value[messages.value.length - 1]
      lastMessage.content = data.content
      if (data.llm_response_time) {
        lastMessage.llmTime = data.llm_response_time
      }
      scrollToBottom()
    }
  })

  socket.on('audio_chunk', (data) => {
    if (data.assistant_id === props.assistantId && !data.final && ttsEnabled.value) {
      // Reset timing when we receive the first chunk (data.first_chunk_time exists)
      if (data.first_chunk_time) {
        currentTime.value = audioContext.value?.currentTime || 0
        const lastMessage = messages.value[messages.value.length - 1]
        lastMessage.ttsTime = data.first_chunk_time
      }
      
      try {
        // Validate audio data
        if (!data.audio || data.audio.length === 0) {
          console.warn('Skipping empty audio chunk')
          return
        }

        // Create audio context lazily if it doesn't exist
        if (!audioContext.value) {
          const AudioContextClass = window.AudioContext || window.webkitAudioContext
          audioContext.value = new AudioContextClass()
          currentTime.value = audioContext.value.currentTime
        }

        // Convert the incoming audio data to Float32Array if it isn't already
        const audioArray = data.audio instanceof Float32Array 
          ? data.audio 
          : new Float32Array(data.audio)

        // Create an audio buffer with correct sample rate
        const audioBuffer = audioContext.value.createBuffer(
          1,                // mono channel
          audioArray.length,
          22050            // match backend sample rate
        )

        // Copy the audio data
        audioBuffer.copyToChannel(audioArray, 0)

        // Create and play source
        const source = audioContext.value.createBufferSource()
        source.buffer = audioBuffer
        source.connect(audioContext.value.destination)
        
        // Schedule the chunk to play at the correct time
        source.start(currentTime.value)
        
        // Update the current time for the next chunk
        currentTime.value += audioBuffer.duration

      } catch (err) {
        console.error('Error processing audio chunk:', err)
      }
    }
  })

  socket.on('error', (error) => {
    console.error('Socket error:', error)
    messages.value.push({ 
      sender: 'assistant', 
      content: 'Sorry, there was an error processing your message.' 
    })
    scrollToBottom()
  })

  socket.on('transcript', (data) => {
    console.log('Received transcript event:', {
      data,
      messagesLength: messages.value.length,
      currentMessages: messages.value
    });
    
    const { text, assistant_id, final } = data;
    
    if (assistant_id === props.assistantId) {
      // Update the last assistant message with the new transcript
      const lastMessage = messages.value[messages.value.length - 1];
      console.log('Last message:', lastMessage);
      
      if (lastMessage && lastMessage.sender === 'assistant') {
        console.log('Updating last message content:', text);
        lastMessage.content = text;
        scrollToBottom();
      } else {
        console.log('No suitable message found to update');
      }
    } else {
      console.log('Assistant ID mismatch:', {
        received: assistant_id,
        expected: props.assistantId
      });
    }
  });

  document.addEventListener('keydown', handleEscape)
})

onUnmounted(() => {
  // Clean up socket listeners
  socket.off('chat_response')
  socket.off('audio_chunk')
  socket.off('error')
  socket.off('stt_started')
  socket.off('stt_transcript')
  socket.off('stt_stopped')
  socket.off('transcript')
  socket.off('connect')
  socket.off('disconnect')
  
  // Clean up event listeners
  document.removeEventListener('keydown', handleEscape)
  
  // Clean up audio context
  if (audioContext.value) {
    audioContext.value.close().catch(console.error)
  }
  
  // Clean up media recorder
  cleanupMediaRecorder()
  
  // Clean up TTS
  if (synthesis && synthesis.speaking) {
    synthesis.cancel()
  }

  if (isListening.value) {
    stopSpeechRecognition();
  }
})

const sendMessage = async () => {
  if (!newMessage.value.trim()) return
  
  try {
    const messageText = newMessage.value
    messages.value.push({ sender: 'user', content: messageText })
    newMessage.value = ''
    scrollToBottom()

    const assistantIdNumber = Number(props.assistantId)
    if (isNaN(assistantIdNumber)) {
      throw new Error('Invalid assistant ID')
    }

    messages.value.push({ sender: 'assistant', content: '' })
    
    // Send message through socket
    socket.emit('chat_message', {
      assistant_id: assistantIdNumber,
      question: messageText,
      use_tts: ttsEnabled.value
    })

  } catch (error) {
    console.error('Error sending message:', error)
    messages.value.push({ 
      sender: 'assistant', 
      content: 'Sorry, there was an error processing your message.' 
    })
    scrollToBottom()
  }
}

// Handle escape key for the entire document
const handleEscape = (event: KeyboardEvent) => {
  if (event.key === 'Escape') {
    handleClose()
  }
}

const cleanupMediaRecorder = () => {
  if (mediaRecorder.value) {
    mediaRecorder.value.stop();
    mediaRecorder.value.stream.getTracks().forEach(track => track.stop());
    mediaRecorder.value = null;
  }
  if (audioContext.value) {
    audioContext.value.close();
    audioContext.value = null;
  }
  isListening.value = false;
};

const stopSpeechRecognition = async () => {
  try {
    console.log('Stopping speech recognition resources')
    
    // Disconnect and clean up processor
    if (processor.value) {
      try {
        processor.value.disconnect()
        processor.value.onaudioprocess = null // Remove event listener
      } catch (err) {
        console.warn('Error disconnecting processor:', err)
      }
      processor.value = null
    }
    
    // Disconnect source node
    if (sourceNode.value) {
      try {
        sourceNode.value.disconnect()
      } catch (err) {
        console.warn('Error disconnecting source node:', err)
      }
      sourceNode.value = null
    }
    
    // Close audio context
    if (audioContext.value) {
      try {
        await audioContext.value.close()
        audioContext.value = null
      } catch (err) {
        console.warn('Error closing audio context:', err)
      }
    }
    
    // Stop all media tracks
    if (stream.value) {
      stream.value.getTracks().forEach((track: MediaStreamTrack) => {
        track.stop()
      })
      stream.value = null
    }
    
    // Tell backend to stop STT
    socket.emit('stop_stt', {
      assistant_id: props.assistantId
    })
    
    isListening.value = false
    return true
  } catch (error) {
    console.error('Error stopping speech recognition:', error)
    return false
  }
}

const startSpeechRecognition = async () => {
  try {
    const success = await initSpeechRecognition();
    if (success) {
      console.log('Speech recognition started');
      return true;
    } else {
      console.error('Failed to start speech recognition');
      return false;
    }
  } catch (error) {
    console.error('Error starting speech recognition:', error);
    return false;
  }
};

const toggleListening = async () => {
  try {
    if (isListening.value) {
      await stopSpeechRecognition();
    } else {
      await startSpeechRecognition();
    }
  } catch (error) {
    console.error('Error toggling microphone:', error);
    isListening.value = false;
  }
};

const handleClose = async () => {
  // Stop speech recognition if active
  if (isListening.value) {
    await stopSpeechRecognition()
  }
  
  // Clean up media recorder
  cleanupMediaRecorder()
  
  // Cancel any ongoing TTS
  if (synthesis && synthesis.speaking) {
    synthesis.cancel()
  }

  // Emit custom cleanup event with assistant ID
  socket.emit('chat_cleanup', {
    assistant_id: props.assistantId
  })
  
  // Close the modal
  emit('close')
}
</script> 