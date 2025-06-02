<template>
  <div class="flex-1 h-full overflow-y-auto bg-gray-50 relative">
    <!-- Main content with padding to account for fixed footer -->
    <div class="p-6 pb-16">
      <!-- Loading state -->
      <div v-if="isLoading" class="flex items-center justify-center h-full">
        <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-[#4285F4]"></div>
      </div>

      <!-- Error state -->
      <div v-else-if="error" class="p-4 bg-red-50 text-red-600 rounded-xl">
        {{ error }}
      </div>

      <!-- Content when data is loaded -->
      <div v-else-if="assistant" class="max-w-7xl mx-auto">
        <!-- Header with gradient background -->
        <div class="bg-white shadow-sm rounded-xl mb-8">
          <div class="p-6">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-4">
                <div class="w-10 h-10 bg-[#4285F4]/10 rounded-xl flex items-center justify-center">
                  <Users class="w-5 h-5 text-[#4285F4]" />
                </div>
                <h1 class="text-2xl font-bold text-gray-900">Assistant Settings</h1>
              </div>
              <div class="flex items-center gap-3">
                <button 
                  @click="isCallOpen = true"
                  class="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 text-gray-700 hover:border-[#4285F4] hover:text-[#4285F4] rounded-lg transition-colors"
                >
                  <Mic class="w-4 h-4" />
                  <span class="text-sm font-medium">Talk</span>
                </button>
                <button 
                  @click="isChatOpen = true"
                  class="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 text-gray-700 hover:border-[#4285F4] hover:text-[#4285F4] rounded-lg transition-colors"
                >
                  <MessageSquare class="w-4 h-4" />
                  <span class="text-sm font-medium">Chat</span>
                </button>
                <button 
                  class="flex items-center gap-2 px-4 py-2 bg-[#4285F4] text-white hover:bg-[#3367d6] rounded-lg transition-colors"
                >
                  <Share class="w-4 h-4" />
                  <span class="text-sm font-medium">Publish</span>
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Voice Selector -->
        <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-100 mb-8">
          <div class="flex items-center gap-2 mb-6">
            <div class="w-10 h-10 bg-[#4285F4]/10 rounded-lg flex items-center justify-center">
              <Mic class="w-5 h-5 text-[#4285F4]" />
            </div>
            <h2 class="text-lg font-medium">Voice Configuration</h2>
          </div>
          <VoiceSelector
            v-if="assistant"
            v-model="voiceId"
            :assistantId="Number(assistantId)"
          />
        </div>

        <!-- Prompt -->
        <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-100 mb-8">
          <div class="flex items-center gap-2 mb-6">
            <div class="w-10 h-10 bg-[#4285F4]/10 rounded-lg flex items-center justify-center">
              <MessageSquare class="w-5 h-5 text-[#4285F4]" />
            </div>
            <h2 class="text-lg font-medium">Prompt Configuration</h2>
          </div>
          <textarea
            v-model="prompt"
            placeholder="Enter your prompt..."
            class="w-full h-52 p-4 bg-gray-50 border border-gray-200 rounded-xl text-sm text-gray-800 placeholder-gray-400 resize-none focus:outline-none focus:ring-2 focus:ring-[#4285F4]/20"
          />
        </div>

        <!-- Configuration Section with Tabs -->
        <div class="bg-white rounded-xl p-6 shadow-sm border border-gray-100 mb-8">
          <div class="flex items-center justify-between mb-6">
            <div class="flex items-center gap-2">
              <div class="w-10 h-10 bg-[#4285F4]/10 rounded-lg flex items-center justify-center">
                <Settings class="w-5 h-5 text-[#4285F4]" />
              </div>
              <h2 class="text-lg font-medium">Configuration</h2>
            </div>
            <button 
              @click="isPhoneNumberConfigOpen = true"
              class="flex items-center gap-2 px-4 py-2 bg-white border border-gray-200 text-gray-700 hover:border-[#4285F4] hover:text-[#4285F4] rounded-lg transition-colors"
            >
              <Hash class="w-4 h-4" />
              <span class="font-medium text-sm">Configure Number</span>
            </button>
          </div>

          <!-- Tabs -->
          <div class="flex bg-gray-100 rounded-xl p-1 mb-6">
            <button
              v-for="tab in tabs"
              :key="tab"
              @click="selectedTab = tab"
              :class="[
                'px-4 py-2 text-sm font-medium rounded-lg transition-colors',
                selectedTab === tab 
                  ? 'bg-white text-[#4285F4] shadow-sm' 
                  : 'text-gray-600 hover:text-[#4285F4]'
              ]"
            >
              {{ tab }}
            </button>
          </div>

          <!-- Tab Content -->
          <!-- LLM Settings -->
          <div v-if="selectedTab === 'LLM'" class="space-y-4">
            <div class="flex items-center justify-between p-4 bg-gray-50 rounded-xl border border-gray-200">
              <div>
                <div class="flex items-center justify-between mb-2">
                  <h3 class="text-sm font-medium text-gray-800">Language Model</h3>
                  <div class="flex items-center gap-2">
                    <span v-if="configuredPhoneNumber" class="text-sm text-gray-600">
                      Phone: {{ configuredPhoneNumber }}
                    </span>
                    <span v-else-if="assistant?.phone_number_id" class="text-sm text-gray-600">
                      Loading phone number...
                    </span>
                    <span v-else class="text-sm text-red-600 flex items-center gap-1">
                      <AlertCircle class="w-4 h-4" />
                      No phone number configured
                    </span>
                  </div>
                </div>
                <p class="text-sm text-gray-500 mb-3">Select the AI model for your assistant</p>
                <select
                  v-model="assistant.llm_model"
                  class="w-full p-2 bg-white border border-gray-200 rounded-lg text-sm text-gray-800 focus:border-blue-400 focus:outline-none transition-colors"
                >
                  <option value="llama-3.3-70b-versatile">Llama 3.3 70B Versatile</option>
                  <option value="llama-3.1-8b-instant">Llama 3.1 8B Instant</option>
                  <option value="gemma2-9b-it">Gemma2 9B IT</option>
                  <option value="qwen-2.5-32b">Qwen 2.5 32B</option>
                  <option value="deepseek-r1-distill-qwen-32b">Deepseek R1 Distill Qwen 32B</option>
                  <option value="deepseek-r1-distill-llama-70b">Deepseek R1 Distill Llama 70B</option>
                  <option value="mixtral-8x7b-32768">Mixtral 8x7B 32768</option>
                </select>
              </div>
            </div>

            <!-- Greeting Message section -->
            <div class="flex items-center justify-between p-4 bg-gray-50 rounded-xl border border-gray-200">
              <div class="w-full">
                <h3 class="text-sm font-medium text-gray-800">Greeting Message</h3>
                <p class="text-sm text-gray-500 mb-3">Custom greeting spoken at the beginning of each call</p>
                <textarea
                  v-model="greetingMessage"
                  placeholder="Enter a custom greeting (e.g., 'Hello, I'm your virtual assistant. How can I help you today?')"
                  class="w-full p-2 bg-white border border-gray-200 rounded-lg text-sm text-gray-800 focus:border-blue-400 focus:outline-none transition-colors"
                  rows="3"
                ></textarea>
                <p class="text-xs text-gray-500 mt-2">Leave empty to use the default greeting</p>
              </div>
            </div>

            <div class="flex items-center justify-between p-4 bg-gray-50 rounded-xl border border-gray-200">
              <div class="w-full">
                <h3 class="text-sm font-medium text-gray-800">Temperature</h3>
                <p class="text-sm text-gray-500 mb-3">Control response creativity (0 = focused, 1 = creative)</p>
                <div class="flex items-center gap-4">
                  <input
                    type="range"
                    v-model.number="assistant.llm_temperature"
                    min="0"
                    max="1"
                    step="0.01"
                    class="flex-1 h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
                  />
                  <span class="text-sm font-medium text-gray-600 min-w-[3ch]">
                    {{ (assistant?.llm_temperature || 0).toFixed(2) }}
                  </span>
                </div>
              </div>
            </div>

            <div class="flex items-center justify-between p-4 bg-gray-50 rounded-xl border border-gray-200">
              <div class="w-full">
                <h3 class="text-sm font-medium text-gray-800">Max Tokens</h3>
                <p class="text-sm text-gray-500 mb-3">Maximum length of the generated response</p>
                <input
                  type="number"
                  v-model.number="assistant.llm_max_tokens"
                  min="0"
                  class="w-full p-2 bg-white border border-gray-200 rounded-lg text-sm text-gray-800 focus:border-blue-400 focus:outline-none transition-colors"
                />
              </div>
            </div>
          </div>

          <!-- Tools Settings -->
          <div v-if="selectedTab === 'Tools'" class="space-y-4">
            <div class="flex items-center justify-between p-4 bg-gray-50 rounded-xl border border-gray-200">
              <div>
                <h3 class="text-sm font-medium text-gray-800">Calendar</h3>
                <p class="text-sm text-gray-500">Access and manage calendar events</p>
              </div>
              <label class="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" v-model="enabledTools.calendar" class="sr-only peer">
                <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-[#4285F4]/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#4285F4]"></div>
              </label>
            </div>
            <div class="flex items-center justify-between p-4 bg-gray-50 rounded-xl border border-gray-200">
              <div>
                <h3 class="text-sm font-medium text-gray-800">Notepad</h3>
                <p class="text-sm text-gray-500">Create and edit notes</p>
              </div>
              <label class="relative inline-flex items-center cursor-pointer">
                <input type="checkbox" v-model="enabledTools.notepad" class="sr-only peer">
                <div class="w-11 h-6 bg-gray-200 peer-focus:outline-none peer-focus:ring-4 peer-focus:ring-[#4285F4]/20 rounded-full peer peer-checked:after:translate-x-full peer-checked:after:border-white after:content-[''] after:absolute after:top-[2px] after:left-[2px] after:bg-white after:border-gray-300 after:border after:rounded-full after:h-5 after:w-5 after:transition-all peer-checked:bg-[#4285F4]"></div>
              </label>
            </div>
          </div>

          <!-- Advanced Settings -->
          <div v-if="selectedTab === 'Advanced'" class="space-y-4">
            <!-- Add any additional advanced settings here -->
          </div>
        </div>
      </div>
    </div>

    <!-- Fixed Footer -->
    <div class="fixed bottom-0 right-0 left-[280px] bg-white border-t border-gray-200">
      <div class="w-full mx-auto px-6 py-3 flex justify-end">
        <div class="flex gap-3">
          <button 
            @click="handleDelete"
            class="px-4 py-2 bg-white border border-red-200 text-red-600 rounded-lg text-sm font-medium hover:bg-red-50 transition-colors flex items-center gap-2"
          >
            <Trash2 class="w-4 h-4" />
            Delete Assistant
          </button>
          <button 
            @click="handleSaveAll"
            class="px-4 py-2 bg-green-600 text-white rounded-lg text-sm font-medium hover:bg-green-700 transition-colors flex items-center gap-2"
          >
            <Save class="w-4 h-4" />
            Save Changes
          </button>
        </div>
      </div>
    </div>

    <!-- Modals -->
    <ChatModal
      v-if="isChatOpen"
      :messages="chatMessages"
      :assistantId="assistantId"
      @close="isChatOpen = false"
      @send="handleSendMessage"
    />

    <CallModal
      v-if="isCallOpen"
      @close="isCallOpen = false"
      :assistantId="Number(assistantId)"
    />

    <PhoneNumberConfigModal
      v-if="isPhoneNumberConfigOpen"
      :phoneNumbers="phoneNumbers"
      :selectedPhoneNumber="assistant?.phone_number_id || null"
      @close="isPhoneNumberConfigOpen = false"
      @save="handlePhoneNumberSave"
    />
  </div>
</template> 

<script setup lang="ts">
import { ref, onMounted, watch, computed } from 'vue'
import { ChevronDown, Mic, MessageSquare, MoreVertical, Hash, Save, Share, Phone, Trash2, Users, Settings, AlertCircle } from 'lucide-vue-next'
import VoiceSelector from '@/components/VoiceSelector.vue'
import ChatModal from '@/components/ChatModal.vue'
import CallModal from '@/components/CallModal.vue'
import PhoneNumberConfigModal from '@/components/PhoneNumberConfigModal.vue'
import { useRouter } from 'vue-router'
import { assistantsApi, phoneNumbersApi, testCallsApi } from '@/services/api'
import type { Assistant } from '@/types/assistant'

// Add new interface for PhoneNumber
interface PhoneNumber {
  id: number
  phone_number: string
  assistants: Array<{
    id: string
    name: string
  }>
}

const props = defineProps<{
  assistantId: string
}>()

const router = useRouter()
const prompt = ref('')

// Add new refs for assistant data
const assistant = ref<Assistant | null>(null)
const isLoading = ref(false)
const error = ref('')

// Add this computed property after the other refs
const voiceId = computed({
  get: () => assistant.value?.cartesia_voice_id || '',
  set: (value: string) => {
    if (assistant.value) {
      assistant.value.cartesia_voice_id = value
    }
  }
})

// Add this new ref for the greeting message
const greetingMessage = ref('')

// Add a watch effect to reload data when assistantId changes
watch(() => props.assistantId, async (newId) => {
  if (newId) {
    try {
      isLoading.value = true
      const response = await assistantsApi.getById(newId)
      assistant.value = response
      // Set the prompt value from the fetched assistant
      prompt.value = response.prompt || ''
      // Set the greeting message value
      greetingMessage.value = response.greeting_message || ''
      // Fetch phone numbers when assistant data changes
      if (response.phone_number_id) {
        await fetchPhoneNumbers()
      }
    } catch (err) {
      console.error('Failed to fetch assistant:', err)
      error.value = 'Failed to fetch assistant data'
    } finally {
      isLoading.value = false
    }
  }
}, { immediate: true }) // immediate: true ensures it runs on component mount

// Also watch for changes to the assistant's phone_number_id
watch(() => assistant.value?.phone_number_id, (newPhoneNumberId) => {
  if (newPhoneNumberId) {
    fetchPhoneNumbers()
  }
})

const selectedTab = ref('LLM')

// Stats data
const stats = [
    { label: 'Cost per minute', value: '$0.03', change: '', changeColor: 'text-green-500' },
    { label: 'Latency', value: '700 ms', change: '', changeColor: 'text-blue-500' },
]

// Tabs
const tabs = ['LLM', 'Tools', 'Advanced']

// Tools state
const enabledTools = ref({
  calendar: false,
  notepad: false
})

const isPhoneNumberConfigOpen = ref(false)

// Top level tabs
const topTabs = ['Assistant', 'Calls']
const selectedTopTab = ref('Assistant')

// Chat and Call state
const isChatOpen = ref(false)
const isCallOpen = ref(false)
const chatMessages = ref([
  { sender: 'assistant', content: 'Hello! How can I help you today?' }
])

const phoneNumbers = ref<PhoneNumber[]>([])

const handleSendMessage = (message: string) => {
  // Add user message
  chatMessages.value.push({
    sender: 'user',
    content: message
  })
  
  // Simulate assistant response (replace with actual API call)
  setTimeout(() => {
    chatMessages.value.push({
      sender: 'assistant',
      content: 'I received your message. This is a simulated response.'
    })
  }, 1000)
}

const handleDelete = async () => {
  if (confirm('Are you sure you want to delete this assistant?')) {
    try {
      await assistantsApi.delete(Number(props.assistantId))
      router.push('/')
    } catch (err) {
      console.error('Failed to delete assistant:', err)
      // You might want to add error handling UI here
    }
  }
}

const configuredPhoneNumber = computed(() => {
  if (!assistant.value?.phone_number_id) {
    return null;
  }
  
  // Get phone number from the database query
  const phoneNumberId = Number(assistant.value.phone_number_id);
  const phone = phoneNumbers.value.find((p: PhoneNumber) => p.id === phoneNumberId);
  
  if (!phone) {
    // If we don't have the phone number in our list yet, fetch it again
    fetchPhoneNumbers();
    return null;
  }
  
  return phone.phone_number;
});

const fetchPhoneNumbers = async () => {
  try {
    console.log('Fetching phone numbers...');
    const response = await phoneNumbersApi.getAll();
    console.log('Phone numbers response from phoneNumbersApi:', response);
    
    // Store the phone numbers in the phoneNumbers ref
    phoneNumbers.value = response.map((phone: any) => ({
      id: phone.id,
      phone_number: phone.phone_number,
      assistants: [] // Initialize with empty array since phoneNumbersApi doesn't return assistants
    }));
    
    // If we also need the test call available numbers (which include assistants relationship)
    const testCallResponse = await testCallsApi.getAvailablePhoneNumbers();
    console.log('Phone numbers response from testCallsApi:', testCallResponse);
    
    if (testCallResponse && testCallResponse.status === 'success' && 
        Array.isArray(testCallResponse.phone_numbers)) {
      // Merge in the assistants data from the test call API
      phoneNumbers.value = testCallResponse.phone_numbers;
    }
    
    // Debug logging
    console.log('Current assistant phone_number_id:', assistant.value?.phone_number_id);
    console.log('Available phone numbers:', phoneNumbers.value);
    
    if (assistant.value?.phone_number_id) {
      const phoneNumberId = Number(assistant.value.phone_number_id);
      const matchingPhone = phoneNumbers.value.find(phone => phone.id === phoneNumberId);
      if (matchingPhone) {
        console.log('Found matching phone:', matchingPhone);
      } else {
        console.log('No matching phone found for ID:', phoneNumberId);
      }
    }
  } catch (err) {
    console.error('Failed to fetch phone numbers:', err);
    phoneNumbers.value = [];
  }
};

const handlePhoneNumberSave = async (phoneNumberId: string) => {
  try {
    console.log('Saving phone number ID:', phoneNumberId);
    console.log('Phone number ID type:', typeof phoneNumberId);
    
    const numericPhoneNumberId = Number(phoneNumberId);
    if (isNaN(numericPhoneNumberId)) {
      throw new Error('Invalid phone number ID');
    }
    
    // Let's try sending it as a number instead of a string
    console.log('About to update assistant with phone_number_id:', numericPhoneNumberId);
    const updateResponse = await assistantsApi.update(Number(props.assistantId), { 
      phone_number_id: String(numericPhoneNumberId) // Convert back to string as required by the API
    });
    console.log('Update response:', updateResponse);
    
    // Force a 1-second delay to ensure the database has processed the update
    await new Promise(resolve => setTimeout(resolve, 1000));
    
    // Refresh the assistant data to get the updated phone number
    console.log('Refreshing assistant data...');
    const response = await assistantsApi.getById(props.assistantId);
    console.log('Refreshed assistant data:', response);
    console.log('phone_number_id after refresh:', response.phone_number_id);
    console.log('phone_number_id type after refresh:', typeof response.phone_number_id);
    
    // Additional check to verify if we can find the phone number in our list
    const phoneIdNum = Number(response.phone_number_id);
    const foundPhone = phoneNumbers.value.find((p: PhoneNumber) => p.id === phoneIdNum);
    console.log('Found phone in our list?', foundPhone ? 'Yes' : 'No');
    if (foundPhone) {
      console.log('Found phone details:', foundPhone);
    }
    
    if (response.phone_number_id) {
      alert(`Phone number with ID ${response.phone_number_id} has been configured successfully!`);
    } else {
      alert('Warning: The phone number was not saved properly. Please try again.');
    }
    
    assistant.value = response;
  } catch (err) {
    console.error('Failed to update phone number:', err);
    alert('Error: Failed to update phone number. See console for details.');
  }
}

const handleSaveAll = async () => {
  try {
    // Save LLM settings, prompt, and greeting message together
    await assistantsApi.update(Number(props.assistantId), {
      llm_model: assistant.value?.llm_model,
      llm_temperature: assistant.value?.llm_temperature,
      llm_max_tokens: assistant.value?.llm_max_tokens,
      prompt: prompt.value, // Include prompt in the main update
      greeting_message: greetingMessage.value // Add greeting message
    });

    // Optionally show a success message
    // You could add a toast notification here
  } catch (err) {
    console.error('Failed to save changes:', err);
    // Handle error (e.g., show an error message)
  }
}

onMounted(() => {
  fetchPhoneNumbers()
})
</script>