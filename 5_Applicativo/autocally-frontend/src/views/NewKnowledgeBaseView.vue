<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { X, FileText, Users } from 'lucide-vue-next'
import { knowledgeBaseApi, assistantsApi } from '@/services/api'

interface Assistant {
  id: string
  name: string
}

const router = useRouter()
const name = ref('')
const description = ref('')
const selectedAssistants = ref<string[]>([])
const isLoading = ref(false)
const error = ref('')
const assistants = ref<Assistant[]>([])
const isLoadingAssistants = ref(false)

// Fetch assistants on component mount
onMounted(async () => {
  try {
    isLoadingAssistants.value = true
    const response = await assistantsApi.getAll()
    assistants.value = response
  } catch (err) {
    console.error('Failed to fetch assistants:', err)
    error.value = 'Failed to fetch assistants'
  } finally {
    isLoadingAssistants.value = false
  }
})

const handleSubmit = async () => {
  try {
    isLoading.value = true
    error.value = ''

    if (!selectedAssistants.value.length) {
      throw new Error('Please select at least one assistant')
    }

    const response = await knowledgeBaseApi.create({
      name: name.value.trim(),
      description: description.value.trim(),
      assistant_ids: selectedAssistants.value
    })

    router.push(`/knowledge-base/${response.base_knowledge.id}`)
  } catch (err) {
    error.value = err instanceof Error ? err.message : 'Failed to create knowledge base'
    console.error('Failed to create knowledge base:', err)
  } finally {
    isLoading.value = false
  }
}
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
          <h1 class="ml-2 text-xl font-semibold">New Knowledge Base</h1>
        </div>
      </div>
    </div>

    <!-- Content -->
    <div class="max-w-3xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
      <div class="bg-white rounded-lg p-6">
        <div class="flex items-center gap-2 mb-6">
          <div class="w-10 h-10 bg-[#4285F4]/10 rounded-lg flex items-center justify-center">
            <FileText class="w-5 h-5 text-[#4285F4]" />
          </div>
          <h2 class="text-lg font-medium">Knowledge Base Details</h2>
        </div>

        <div class="space-y-6">
          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Name</label>
            <input
              v-model="name"
              type="text"
              placeholder="Enter knowledge base name..."
              class="w-full px-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#4285F4]"
            />
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Description</label>
            <textarea
              v-model="description"
              rows="3"
              placeholder="Describe the purpose of this knowledge base..."
              class="w-full px-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#4285F4]"
            ></textarea>
          </div>

          <div>
            <label class="block text-sm font-medium text-gray-700 mb-2">Assign Assistants</label>
            <div class="space-y-3">
              <div class="max-h-[240px] overflow-y-auto rounded-lg border border-gray-200">
                <div v-if="isLoadingAssistants" class="p-4 text-center text-sm text-gray-500">
                  Loading assistants...
                </div>
                <div v-else class="divide-y divide-gray-100">
                  <label 
                    v-for="assistant in assistants" 
                    :key="assistant.id" 
                    class="flex items-center p-3 hover:bg-gray-50 transition-colors cursor-pointer"
                  >
                    <div class="flex items-center flex-1 min-w-0">
                      <input
                        type="checkbox"
                        :value="assistant.id"
                        v-model="selectedAssistants"
                        class="w-4 h-4 text-[#4285F4] border-gray-300 rounded focus:ring-[#4285F4]"
                      />
                      <span class="ml-3 text-sm text-gray-700">{{ assistant.name }}</span>
                    </div>
                  </label>
                </div>
                <div v-if="!isLoadingAssistants && assistants.length === 0" class="p-4 text-center text-sm text-gray-500">
                  No assistants found
                </div>
              </div>
            </div>
          </div>
        </div>

        <!-- Add this after the form fields, before the footer -->
        <div v-if="error" class="mt-4 p-4 bg-red-50 text-red-600 rounded-lg text-sm">
          {{ error }}
        </div>

        <!-- Footer -->
        <div class="mt-8 flex justify-end gap-3">
          <button
            @click="router.back()"
            class="px-4 py-2 border border-gray-200 rounded-lg text-sm font-medium hover:border-gray-300 transition-colors"
          >
            Cancel
          </button>
          <button
            @click="handleSubmit"
            :disabled="!name.trim() || isLoading"
            class="px-4 py-2 bg-[#4285F4] text-white rounded-lg text-sm font-medium hover:bg-[#3367d6] transition-colors disabled:opacity-50 disabled:hover:bg-[#4285F4] flex items-center gap-2"
          >
            <span v-if="isLoading">Creating...</span>
            <span v-else>Create Knowledge Base</span>
          </button>
        </div>
      </div>
    </div>
  </div>
</template> 