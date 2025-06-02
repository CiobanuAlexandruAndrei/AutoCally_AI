<script setup lang="ts">
import { ref, computed } from 'vue'
import { useRouter } from 'vue-router'
import { ChevronLeft, Phone, X, FileText, Search } from 'lucide-vue-next'

const router = useRouter()

const phoneNumber = ref('')
const selectedAssistant = ref('')
const notes = ref('')
const scheduledDateTime = ref('')
const selectedKnowledgeBase = ref<string[]>([])
const website = ref('')
const uploadedFiles = ref<File[]>([])

const assistants = ['Marco', 'Hans', 'Sophie']
const knowledgeBases = ['Sales FAQ', 'Product Manual', 'Company Policies'] // This should come from your database

const websiteInfo = ref<{ title?: string; description?: string } | null>(null)

const fetchWebsiteInfo = async () => {
  if (!website.value) {
    websiteInfo.value = null
    return
  }
  
  try {
    // Replace this with your actual API call
    const response = await fetch(`/api/website-info?url=${encodeURIComponent(website.value)}`)
    websiteInfo.value = await response.json()
  } catch (error) {
    console.error('Failed to fetch website info:', error)
    websiteInfo.value = null
  }
}

const removeFile = (index: number) => {
  uploadedFiles.value.splice(index, 1)
}

const handleFileUpload = (event: Event) => {
  const input = event.target as HTMLInputElement
  if (input.files) {
    uploadedFiles.value.push(...Array.from(input.files))
  }
}

const handleFileDrop = (event: DragEvent) => {
  const files = event.dataTransfer?.files
  if (files) {
    uploadedFiles.value.push(...Array.from(files))
  }
}

const handleSubmit = () => {
  console.log({
    phoneNumber: phoneNumber.value,
    assistant: selectedAssistant.value,
    notes: notes.value,
    scheduledDateTime: scheduledDateTime.value,
    knowledgeBases: selectedKnowledgeBase.value,
    website: website.value,
    files: uploadedFiles.value,
  })
  
  router.push('/calls')
}

// Add new state for wizard
const currentStep = ref(1)
const totalSteps = 2

const nextStep = () => {
  if (currentStep.value < totalSteps) {
    currentStep.value++
  }
}

const prevStep = () => {
  if (currentStep.value > 1) {
    currentStep.value--
  }
}

const knowledgeBaseSearch = ref('')

const filteredKnowledgeBases = computed(() => {
  if (!knowledgeBaseSearch.value) return knowledgeBases
  return knowledgeBases.filter(kb => 
    kb.toLowerCase().includes(knowledgeBaseSearch.value.toLowerCase())
  )
})
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Header -->
    <div class="bg-white border-b border-gray-200">
      <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center h-16">
          <button
            @click="router.back()"
            class="p-2 -ml-2 text-gray-400 hover:text-gray-500"
          >
            <X class="w-5 h-5" />
          </button>
          <h1 class="ml-2 text-xl font-semibold">Make New Call</h1>
        </div>
      </div>
    </div>

    <!-- Progress bar -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-6">
      <div class="relative mb-2">
        <div class="flex items-center">
          <div class="w-8 h-8 rounded-full bg-blue-500 flex items-center justify-center text-white">
            1
          </div>
          <div class="flex-1 h-[2px] bg-blue-500"></div>
          <div class="w-8 h-8 rounded-full border-2 border-gray-300 flex items-center justify-center text-gray-400"
               :class="{ 'bg-blue-500 border-blue-500 text-white': currentStep === 2 }">
            2
          </div>
        </div>
      </div>
      <div class="flex justify-between text-sm">
        <span class="text-blue-500">Contact Details</span>
        <span :class="currentStep === 2 ? 'text-blue-500' : 'text-gray-400'">Call Content</span>
      </div>
    </div>

    <!-- Content -->
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
      <form @submit.prevent="handleSubmit">
        <!-- Step 1 -->
        <div v-if="currentStep === 1" class="bg-white rounded-lg p-6">
          <div class="flex items-center gap-2 mb-6">
            <div class="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center">
              <Phone class="w-5 h-5 text-blue-500" />
            </div>
            <h2 class="text-lg font-medium">Contact Details</h2>
          </div>

          <div class="space-y-6">
            <div>
              <label class="block text-sm mb-2">Phone Number</label>
              <input
                v-model="phoneNumber"
                type="tel"
                required
                placeholder="+41 XX XXX XX XX"
                class="w-full px-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label class="block text-sm mb-2">Schedule Call (Optional)</label>
              <input
                v-model="scheduledDateTime"
                type="datetime-local"
                class="w-full px-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>

            <div>
              <label class="block text-sm mb-2">Assistant</label>
              <select
                v-model="selectedAssistant"
                required
                class="w-full px-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              >
                <option value="" disabled>Select an assistant</option>
                <option v-for="assistant in assistants" :key="assistant" :value="assistant">
                  {{ assistant }}
                </option>
              </select>
            </div>
          </div>
        </div>

        <!-- Step 2 -->
        <div v-if="currentStep === 2" class="bg-white rounded-lg p-6">
          <div class="flex items-center gap-2 mb-6">
            <div class="w-10 h-10 bg-blue-50 rounded-lg flex items-center justify-center">
              <FileText class="w-5 h-5 text-blue-500" />
            </div>
            <h2 class="text-lg font-medium">Call Content</h2>
          </div>

          <div class="space-y-6">
            <div>
              <label class="block text-sm mb-2">Notes</label>
              <textarea
                v-model="notes"
                rows="4"
                placeholder="Add any additional information about the call..."
                class="w-full px-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              ></textarea>
            </div>

            <div>
              <label class="block text-sm mb-2">Knowledge Bases (Optional)</label>
              <div class="space-y-3">
                <!-- Search input -->
                <div class="relative">
                  <div class="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                    <Search class="h-4 w-4 text-gray-400" />
                  </div>
                  <input
                    type="text"
                    v-model="knowledgeBaseSearch"
                    placeholder="Search knowledge bases..."
                    class="w-full pl-10 pr-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
                  />
                </div>

                <!-- Selected count -->
                <div v-if="selectedKnowledgeBase.length" class="text-sm text-gray-600">
                  {{ selectedKnowledgeBase.length }} selected
                </div>

                <!-- Scrollable checkbox list -->
                <div class="max-h-[240px] overflow-y-auto rounded-lg border border-gray-200">
                  <div class="divide-y divide-gray-100">
                    <label 
                      v-for="kb in filteredKnowledgeBases" 
                      :key="kb" 
                      class="flex items-center p-3 hover:bg-gray-50 transition-colors cursor-pointer"
                    >
                      <div class="flex items-center flex-1 min-w-0">
                        <input
                          type="checkbox"
                          :value="kb"
                          v-model="selectedKnowledgeBase"
                          class="w-4 h-4 text-blue-500 border-gray-300 rounded focus:ring-blue-500"
                        />
                        <span class="ml-3 text-sm text-gray-700 truncate">{{ kb }}</span>
                      </div>
                      <span v-if="selectedKnowledgeBase.includes(kb)" class="ml-3 text-xs text-blue-500">
                        Selected
                      </span>
                    </label>
                  </div>

                  <!-- Empty state -->
                  <div 
                    v-if="filteredKnowledgeBases.length === 0" 
                    class="p-4 text-center text-sm text-gray-500"
                  >
                    No knowledge bases found
                  </div>
                </div>

                <!-- Clear selection button -->
                <button
                  v-if="selectedKnowledgeBase.length"
                  @click="selectedKnowledgeBase = []"
                  type="button"
                  class="text-sm text-gray-600 hover:text-gray-900"
                >
                  Clear selection
                </button>
              </div>
            </div>

            <div>
              <label class="block text-sm mb-2">Upload Files (Optional)</label>
              <div 
                class="relative border-2 border-dashed border-gray-200 rounded-lg p-6 hover:border-blue-500 transition-colors"
                @dragover.prevent
                @drop.prevent="handleFileDrop"
              >
                <input
                  type="file"
                  multiple
                  @change="handleFileUpload"
                  class="absolute inset-0 w-full h-full opacity-0 cursor-pointer"
                />
                <div class="text-center">
                  <div class="flex justify-center mb-3">
                    <div class="p-2 bg-blue-50 rounded-lg">
                      <FileText class="w-5 h-5 text-blue-500" />
                    </div>
                  </div>
                  <p class="text-sm text-gray-600">
                    Drag and drop files here, or <span class="text-blue-500">browse</span>
                  </p>
                  <p class="text-xs text-gray-400 mt-1">PDF, DOC, DOCX up to 10MB</p>
                </div>
              </div>
              
              <!-- File list -->
              <div v-if="uploadedFiles.length" class="mt-3 space-y-2">
                <div
                  v-for="(file, index) in uploadedFiles"
                  :key="index"
                  class="flex items-center justify-between p-2 bg-gray-50 rounded-lg text-sm"
                >
                  <div class="flex items-center gap-2">
                    <FileText class="w-4 h-4 text-gray-400" />
                    <span class="text-gray-700">{{ file.name }}</span>
                  </div>
                  <button
                    @click="removeFile(index)"
                    class="p-1 text-gray-400 hover:text-red-500 transition-colors"
                  >
                    <X class="w-4 h-4" />
                  </button>
                </div>
              </div>
            </div>

            <div>
              <label class="block text-sm mb-2">Reference Website (Optional)</label>
              <input
                v-model="website"
                type="url"
                placeholder="https://example.com"
                @blur="fetchWebsiteInfo"
                class="w-full px-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
              />
            </div>
          </div>
        </div>

        <!-- Navigation -->
        <div class="mt-6">
          <button
            v-if="currentStep === 1"
            type="button"
            @click="nextStep"
            class="w-full px-4 py-2.5 bg-blue-500 text-white rounded-lg hover:bg-blue-600 transition-colors"
          >
            Continue
          </button>
          <div v-else class="flex gap-4">
            <button
              type="button"
              @click="prevStep"
              class="flex-1 px-4 py-2.5 border border-gray-200 rounded-lg hover:bg-gray-50"
            >
              Back
            </button>
            <button
              type="submit"
              class="flex-1 px-4 py-2.5 bg-blue-500 text-white rounded-lg hover:bg-blue-600"
            >
              Start Call
            </button>
          </div>
        </div>
      </form>
    </div>
  </div>
</template> 