<script setup lang="ts">
import { ref, computed, onMounted, watch, onUnmounted } from 'vue'
import { 
  FileText, 
  Link, 
  Globe, 
  File, 
  X, 
  Upload,
  Plus,
  Search,
  Trash2,
  ExternalLink,
  AlertCircle,
  Users,
  Download,
  RefreshCw
} from 'lucide-vue-next'
import { useRouter, useRoute } from 'vue-router'
import { knowledgeBaseApi, assistantsApi } from '@/services/api'

interface Document {
  id: string
  title: string
  type: 'file' | 'text' | 'url'
  content: string
  createdAt: string
  size?: string
  url?: string
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
  needs_reload: boolean
  last_loaded?: string
  total_size?: number
}

interface KnowledgeBaseFile {
  id: string
  name: string
  file_path: string
  file_type: string
  file_size: number
  created_at: string
  updated_at: string
}

interface Assistant {
  id: string;
  name: string;
}

const router = useRouter()
const route = useRoute()
const showAddContent = ref(false)
const contentType = ref<'file' | 'text' | 'url' | null>(null)
const searchQuery = ref('')
const newDocument = ref({
  title: '',
  content: '',
  url: ''
})
const uploadedFiles = ref<File[]>([])
const activeTab = ref('Documents')
const isLoading = ref(true)
const error = ref('')

const knowledgeBase = ref<KnowledgeBase | null>(null)
const assistants = ref<{id: string, name: string}[]>([])
const files = ref<KnowledgeBaseFile[]>([])
const editedName = ref('')
const editedDescription = ref('')
const allAssistants = ref<{id: string, name: string}[]>([])
const showAssistantModal = ref(false)
const selectedNewAssistants = ref<string[]>([])
const showEditModal = ref(false)
const editingFile = ref<KnowledgeBaseFile | null>(null)
const editedContent = ref('')
const editedTitle = ref('')
const showPdfPreview = ref(false)
const pdfUrl = ref('')
const previewFile = ref<KnowledgeBaseFile | null>(null)
const processingKnowledgeBase = ref(false)
const taskStatus = ref<{
  task_id: string
  status: string
  progress: number
  total_steps: number
  progress_percentage: number
  status_message: string
  result: string
  error: string
  created_at: string
  updated_at: string
}>()

const statusPollingInterval = ref<number | null>(null)

const availableAssistants = computed(() => {
  const currentIds = new Set(assistants.value.map(a => a.id))
  return allAssistants.value.filter(a => !currentIds.has(a.id))
})

const formattedContentType = computed(() => {
  if (!contentType.value) return ''
  return contentType.value.charAt(0).toUpperCase() + contentType.value.slice(1)
})

watch(knowledgeBase, (newValue) => {
  if (newValue) {
    editedName.value = newValue.name
    editedDescription.value = newValue.description || ''
  }
}, { immediate: true })

// Fetch knowledge base data on mount
onMounted(async () => {
  const id = parseInt(route.params.id as string)
  if (!id) {
    error.value = 'Invalid knowledge base ID'
    return
  }

  try {
    isLoading.value = true
    const [kbResponse, assistantsResponse, filesResponse] = await Promise.all([
      knowledgeBaseApi.getById(id),
      assistantsApi.getAll(),
      knowledgeBaseApi.getFiles(id)
    ])

    knowledgeBase.value = kbResponse
    files.value = filesResponse
    allAssistants.value = assistantsResponse
    
    // Map assistant IDs to full assistant objects
    assistants.value = assistantsResponse.filter((assistant: Assistant) =>
      knowledgeBase.value?.assistant_ids.includes(assistant.id)
    )

    // Start status polling if we're on the Status tab
    if (activeTab.value === 'Status') {
      await startStatusPolling()
    }

  } catch (err) {
    console.error('Failed to fetch knowledge base:', err)
    error.value = 'Failed to fetch knowledge base details'
  } finally {
    isLoading.value = false
  }
})

const filteredDocuments = computed(() => {
  if (!searchQuery.value) return files.value

  const query = searchQuery.value.toLowerCase()
  return files.value.filter(file => 
    file.name.toLowerCase().includes(query)
  )
})

const handleAddContent = (type: 'file' | 'text' | 'url') => {
  contentType.value = type
  showAddContent.value = true
  newDocument.value = {
    title: '',
    content: '',
    url: ''
  }
}

const handleFileUpload = (event: Event) => {
  const input = event.target as HTMLInputElement
  if (input.files) {
    uploadedFiles.value.push(...Array.from(input.files))
  }
}

const handleFileDrop = (event: DragEvent) => {
  event.preventDefault()
  const files = event.dataTransfer?.files
  if (files) {
    uploadedFiles.value.push(...Array.from(files))
  }
}

const removeFile = (index: number) => {
  uploadedFiles.value.splice(index, 1)
}

const saveDocument = async () => {
  try {
    if (!knowledgeBase.value?.id) return

    if (contentType.value === 'file') {
      // Handle file uploads
      const results = await Promise.all(
        uploadedFiles.value.map(file =>
          knowledgeBaseApi.uploadFile(knowledgeBase.value!.id, file)
        )
      )
      
      // Add new files to the list
      files.value.push(...results.map(r => r.file))
      
    } else if (contentType.value === 'text') {
      // Handle text document creation
      const response = await knowledgeBaseApi.createTextDocument(
        knowledgeBase.value.id,
        {
          title: newDocument.value.title,
          content: newDocument.value.content
        }
      )
      
      files.value.push(response.file)
    }

    // Reset form
    showAddContent.value = false
    contentType.value = null
    newDocument.value = { title: '', content: '', url: '' }
    uploadedFiles.value = []

  } catch (err) {
    console.error('Failed to save document:', err)
    error.value = 'Failed to save document'
  }
}

const deleteDocument = async (fileId: string) => {
  if (!knowledgeBase.value?.id) return
  
  if (!confirm('Are you sure you want to delete this document?')) return

  try {
    await knowledgeBaseApi.deleteFile(knowledgeBase.value.id, parseInt(fileId))
    
    // Remove file from local state
    files.value = files.value.filter(file => file.id !== fileId)
  } catch (err) {
    console.error('Failed to delete document:', err)
    error.value = 'Failed to delete document'
  }
}

const downloadDocument = async (fileId: string) => {
  if (!knowledgeBase.value?.id) return

  try {
    const blob = await knowledgeBaseApi.downloadFile(knowledgeBase.value.id, parseInt(fileId))
    
    // Create download link
    const url = window.URL.createObjectURL(blob)
    const link = document.createElement('a')
    link.href = url
    
    // Get file name from files list
    const file = files.value.find(f => f.id === fileId)
    link.download = file?.name || 'download'
    
    document.body.appendChild(link)
    link.click()
    document.body.removeChild(link)
    window.URL.revokeObjectURL(url)
  } catch (err) {
    console.error('Failed to download document:', err)
    error.value = 'Failed to download document'
  }
}

const formatFileSize = (bytes?: number): string => {
  if (bytes === undefined) return 'Unknown'
  
  const units = ['B', 'KB', 'MB', 'GB']
  let size = bytes
  let unitIndex = 0
  
  while (size >= 1024 && unitIndex < units.length - 1) {
    size /= 1024
    unitIndex++
  }
  
  return `${size.toFixed(1)} ${units[unitIndex]}`
}

const handleAddAssistant = async (assistantId: string) => {
  try {
    if (!knowledgeBase.value?.id) return
    
    const response = await knowledgeBaseApi.addAssistant(knowledgeBase.value.id, assistantId)
    
    // Update the local state
    knowledgeBase.value = {
      ...knowledgeBase.value,
      assistant_ids: response.assistant_ids
    }
    
    // Refresh assistants list
    const assistantsResponse = await assistantsApi.getAll()
    assistants.value = assistantsResponse.filter((assistant: Assistant) => 
      response.assistant_ids.includes(assistant.id)
    )
  } catch (err) {
    console.error('Failed to add assistant:', err)
    error.value = 'Failed to add assistant'
  }
}

const handleRemoveAssistant = async (assistantId: string) => {
  try {
    if (!knowledgeBase.value?.id) return
    
    if (!confirm('Are you sure you want to remove this assistant?')) return
    
    const response = await knowledgeBaseApi.removeAssistant(knowledgeBase.value.id, assistantId)
    
    // Update the local state
    knowledgeBase.value = {
      ...knowledgeBase.value,
      assistant_ids: response.assistant_ids
    }
    
    // Remove from assistants list
    assistants.value = assistants.value.filter(a => a.id !== assistantId)
  } catch (err) {
    console.error('Failed to remove assistant:', err)
    error.value = 'Failed to remove assistant'
  }
}

const handleUpdateKnowledgeBase = async (data: { name?: string; description?: string }) => {
  try {
    if (!knowledgeBase.value?.id) return
    
    const response = await knowledgeBaseApi.update(knowledgeBase.value.id, data)
    knowledgeBase.value = response
  } catch (err) {
    console.error('Failed to update knowledge base:', err)
    error.value = 'Failed to update knowledge base'
  }
}

const handleDeleteKnowledgeBase = async () => {
  try {
    if (!knowledgeBase.value?.id) return
    
    if (!confirm('Are you sure you want to delete this knowledge base? This action cannot be undone.')) return
    
    await knowledgeBaseApi.delete(knowledgeBase.value.id)
    router.push('/knowledge-base')
  } catch (err) {
    console.error('Failed to delete knowledge base:', err)
    error.value = 'Failed to delete knowledge base'
  }
}

const openAssistantModal = () => {
  showAssistantModal.value = true
  selectedNewAssistants.value = []
}

const handleAddAssistants = async () => {
  try {
    if (!knowledgeBase.value?.id || !selectedNewAssistants.value.length) return
    
    const results = await Promise.all(
      selectedNewAssistants.value.map(assistantId =>
        knowledgeBaseApi.addAssistant(knowledgeBase.value!.id, assistantId)
      )
    )
    
    // Update local state with the last response (contains all assistant IDs)
    const lastResponse = results[results.length - 1]
    knowledgeBase.value = {
      ...knowledgeBase.value,
      assistant_ids: lastResponse.assistant_ids
    }
    
    // Update assistants list
    assistants.value = allAssistants.value.filter((assistant: Assistant) => 
      lastResponse.assistant_ids.includes(assistant.id)
    )
    
    showAssistantModal.value = false
  } catch (err) {
    console.error('Failed to add assistants:', err)
    error.value = 'Failed to add assistants'
  }
}

const formatDate = (dateString: string) => {
  return new Date(dateString).toLocaleDateString()
}

const getFileIcon = (fileType: string) => {
  switch (fileType.toLowerCase()) {
    case 'pdf':
      return FileText
    case 'doc':
    case 'docx':
      return File
    case 'txt':
      return FileText
    default:
      return File
  }
}

const openEditModal = async (file: KnowledgeBaseFile) => {
  if (file.file_type !== 'txt') return
  
  try {
    const response = await knowledgeBaseApi.getFileContent(knowledgeBase.value!.id, parseInt(file.id))
    editingFile.value = file
    editedContent.value = response.content
    editedTitle.value = file.name
    showEditModal.value = true
  } catch (err) {
    console.error('Failed to get file content:', err)
    error.value = 'Failed to load file content'
  }
}

const saveTextFile = async () => {
  if (!editingFile.value || !knowledgeBase.value?.id) return
  
  try {
    const response = await knowledgeBaseApi.updateTextFile(
      knowledgeBase.value.id,
      parseInt(editingFile.value.id),
      {
        title: editedTitle.value,
        content: editedContent.value
      }
    )
    
    // Update file in local state
    const index = files.value.findIndex(f => f.id === editingFile.value?.id)
    if (index !== -1) {
      files.value[index] = response.file
    }
    
    showEditModal.value = false
    editingFile.value = null
  } catch (err) {
    console.error('Failed to update file:', err)
    error.value = 'Failed to update file'
  }
}

const openPdfPreview = async (file: KnowledgeBaseFile) => {
  if (file.file_type.toLowerCase() !== 'pdf') return
  
  try {
    const blob = await knowledgeBaseApi.downloadFile(knowledgeBase.value!.id, parseInt(file.id))
    pdfUrl.value = URL.createObjectURL(blob)
    previewFile.value = file
    showPdfPreview.value = true
  } catch (err) {
    console.error('Failed to load PDF:', err)
    error.value = 'Failed to load PDF preview'
  }
}

// Cleanup URL when modal closes
watch(showPdfPreview, (newValue) => {
  if (!newValue && pdfUrl.value) {
    URL.revokeObjectURL(pdfUrl.value)
    pdfUrl.value = ''
    previewFile.value = null
  }
})

const handleReload = async () => {
  if (!knowledgeBase.value?.id) return
  
  try {
    processingKnowledgeBase.value = true
    const response = await knowledgeBaseApi.startProcessing(knowledgeBase.value.id)
    
    // Start polling for task status
    const pollStatus = async () => {
      const status = await knowledgeBaseApi.getTaskStatus(response.task_id)
      taskStatus.value = status

      if (status.status !== 'COMPLETED' && status.status !== 'FAILED') {
        setTimeout(pollStatus, 2000) // Poll every 2 seconds
      } else {
        processingKnowledgeBase.value = false
        // Refresh the knowledge base data
        const [kbResponse, filesResponse] = await Promise.all([
          knowledgeBaseApi.getById(knowledgeBase.value!.id),
          knowledgeBaseApi.getFiles(knowledgeBase.value!.id)
        ])
        knowledgeBase.value = kbResponse
        files.value = filesResponse
      }
    }

    pollStatus()
  } catch (err) {
    console.error('Failed to reload knowledge base:', err)
    processingKnowledgeBase.value = false
    error.value = 'Failed to reload knowledge base'
  }
}

// Function to check status periodically
const startStatusPolling = async () => {
  // Clear any existing interval
  if (statusPollingInterval.value) {
    clearInterval(statusPollingInterval.value)
  }
  
  // Only poll if we're on the Status tab
  if (activeTab.value === 'Status') {
    await checkStatus()
    // Poll every 10 seconds when on the Status tab
    statusPollingInterval.value = setInterval(checkStatus, 10000)
  }
}

// Function to check knowledge base status
const checkStatus = async () => {
  if (!knowledgeBase.value?.id) return
  
  try {
    // Fetch the latest knowledge base data to get status
    const [kbResponse, lastTaskStatus] = await Promise.all([
      knowledgeBaseApi.getById(knowledgeBase.value.id),
      knowledgeBaseApi.getLastTaskStatus(knowledgeBase.value.id)
    ])
    
    knowledgeBase.value = kbResponse
    
    // If there's a task status and it's not completed/failed, show processing state
    if (lastTaskStatus && ['PENDING', 'PROCESSING', 'STARTED'].includes(lastTaskStatus.status)) {
      processingKnowledgeBase.value = true
      taskStatus.value = lastTaskStatus
    } else {
      processingKnowledgeBase.value = false
      if (lastTaskStatus) {
        taskStatus.value = lastTaskStatus
      }
    }
  } catch (err) {
    console.error('Failed to check knowledge base status:', err)
  }
}

watch(activeTab, (newTab) => {
  if (newTab === 'Status') {
    startStatusPolling()
  } else {
    if (statusPollingInterval.value) {
      clearInterval(statusPollingInterval.value)
      statusPollingInterval.value = null
    }
  }
})

onUnmounted(() => {
  if (statusPollingInterval.value) {
    clearInterval(statusPollingInterval.value)
  }
})
</script>

<template>
  <div class="min-h-screen bg-gray-50">
    <!-- Loading State -->
    <div v-if="isLoading" class="flex items-center justify-center h-screen">
      <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-[#4285F4]"></div>
    </div>

    <!-- Error State -->
    <div v-else-if="error" class="flex items-center justify-center h-screen">
      <div class="p-4 bg-red-50 text-red-600 rounded-xl max-w-md text-center">
        {{ error }}
      </div>
    </div>

    <!-- Content when data is loaded -->
    <template v-else-if="knowledgeBase">
      <!-- Header -->
      <div class="bg-white shadow-sm">
        <div class="w-full">
          <div class="py-6 px-8">
            <div class="flex items-center justify-between">
              <div class="flex items-center gap-4">
                <button
                  @click="router.back()"
                  class="p-2 text-gray-500 hover:text-black transition-colors"
                >
                  <X class="w-6 h-6" />
                </button>
                <div>
                  <h1 class="text-2xl font-bold">{{ knowledgeBase.name }}</h1>
                  <p class="text-sm text-gray-500">
                    {{ knowledgeBase.document_count }} documents • Last updated 
                    {{ new Date(knowledgeBase.updated_at).toLocaleDateString() }}
                  </p>
                </div>
              </div>
              
              <!-- Add the reload button here -->
              <button 
                @click="handleReload"
                :disabled="processingKnowledgeBase"
                class="px-4 py-2 text-sm bg-white border border-gray-200 hover:border-[#4285F4] hover:text-[#4285F4] rounded-lg transition-colors flex items-center gap-2"
              >
                <template v-if="processingKnowledgeBase">
                  <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-[#4285F4]"></div>
                  {{ taskStatus?.progress_percentage?.toFixed(0) }}%
                </template>
                <template v-else>
                  <RefreshCw class="w-4 h-4" />
                  Update Knowledge Base
                </template>
              </button>
            </div>
          </div>
        </div>
      </div>

      <!-- Needs Reload Notification -->
      <div class="px-8 pt-6">
        <div v-if="knowledgeBase?.needs_reload" class="bg-yellow-50 border border-yellow-100 rounded-xl p-4 mb-6">
          <div class="flex items-center justify-between">
            <div class="flex items-center gap-2 text-yellow-800">
              <AlertCircle class="w-5 h-5" />
              <p class="text-sm">
                This knowledge base needs to be reloaded to update the assistants.
              </p>
            </div>
            <button 
              @click="handleReload"
              :disabled="processingKnowledgeBase"
              class="px-4 py-2 text-sm bg-yellow-100 text-yellow-800 rounded-lg hover:bg-yellow-200 transition-colors flex items-center gap-2"
            >
              <template v-if="processingKnowledgeBase">
                <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-yellow-800"></div>
                {{ taskStatus?.progress_percentage?.toFixed(0) }}%
              </template>
              <template v-else>
                Reload Knowledge Base
              </template>
            </button>
          </div>
        </div>

        <!-- Tabs -->
        <div class="flex bg-gray-100 rounded-xl p-1">
          <button
            v-for="tab in ['Documents', 'Assistants', 'Settings', 'Status']"
            :key="tab"
            @click="activeTab = tab"
            :class="[
              'px-4 py-2 text-sm font-medium rounded-lg transition-colors',
              activeTab === tab 
                ? 'bg-white text-[#4285F4] shadow-sm' 
                : 'text-gray-600 hover:text-[#4285F4]'
            ]"
          >
            {{ tab }}
          </button>
        </div>
      </div>

      <!-- Description and Stats Section -->
      <div class="px-8 pt-6">
        <div class="bg-white rounded-xl p-5 border border-gray-200">
          <div class="flex flex-col gap-4">
            <div class="flex items-center gap-6">
              <div class="flex-1">
                <h3 class="text-sm font-medium text-gray-700 mb-2">Description</h3>
                <p class="text-sm text-gray-600 leading-relaxed">
                  {{ knowledgeBase.description }}
                </p>
              </div>
              <div class="flex items-center gap-6 border-l border-gray-100 pl-6">
                <div class="flex items-center gap-3">
                  <div class="w-8 h-8 rounded-lg bg-[#4285F4]/10 flex items-center justify-center">
                    <FileText class="w-4 h-4 text-[#4285F4]" />
                  </div>
                  <div class="min-w-[60px]">
                    <div class="font-medium text-gray-900">{{ files.length || 0 }}</div>
                    <div class="text-xs text-gray-500">Documents</div>
                  </div>
                </div>

                <div class="flex items-center gap-3">
                  <div class="w-8 h-8 rounded-lg bg-[#4285F4]/10 flex items-center justify-center">
                    <File class="w-4 h-4 text-[#4285F4]" />
                  </div>
                  <div class="min-w-[60px]">
                    <div class="font-medium text-gray-900">{{ formatFileSize(knowledgeBase.total_size) }}</div>
                    <div class="text-xs text-gray-500">Total Size</div>
                  </div>
                </div>

                <div class="flex items-center gap-3">
                  <div class="w-8 h-8 rounded-lg bg-[#4285F4]/10 flex items-center justify-center">
                    <Users class="w-4 h-4 text-[#4285F4]" />
                  </div>
                  <div class="min-w-[60px]">
                    <div class="font-medium text-gray-900">{{ assistants.length }}</div>
                    <div class="text-xs text-gray-500">Assistants</div>
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Content based on active tab -->
      <div class="px-8 pt-6">
        <!-- Documents Tab -->
        <div v-if="activeTab === 'Documents'">
          <!-- Search and Add Document -->
          <div class="flex justify-between items-center mb-6">
            <div class="relative flex-1 max-w-md">
              <Search class="absolute left-3 top-1/2 -translate-y-1/2 w-5 h-5 text-gray-400" />
              <input
                type="text"
                v-model="searchQuery"
                placeholder="Search documents..."
                class="w-full pl-10 pr-4 py-2 bg-white border border-gray-200 rounded-xl text-sm focus:outline-none focus:ring-2 focus:ring-[#4285F4]"
              />
            </div>
            <div class="flex gap-2">
              <button
                v-for="type in ['text', 'url', 'file']"
                :key="type"
                @click="handleAddContent(type as 'text' | 'url' | 'file')"
                class="px-4 py-2 bg-white border border-gray-200 rounded-xl text-sm font-medium hover:border-[#4285F4] hover:text-[#4285F4] transition-colors flex items-center gap-2"
              >
                <component :is="type === 'file' ? Upload : type === 'url' ? Globe : FileText" class="w-4 h-4" />
                Add {{ type.charAt(0).toUpperCase() + type.slice(1) }}
              </button>
            </div>
          </div>

          <!-- Documents List -->
          <div class="space-y-4">
            <div
              v-for="file in filteredDocuments"
              :key="file.id"
              class="bg-white rounded-xl p-4 border border-gray-200"
            >
              <div class="flex items-center justify-between">
                <div class="flex items-center gap-4">
                  <div class="w-10 h-10 rounded-lg bg-[#4285F4]/10 text-[#4285F4] flex items-center justify-center">
                    <component :is="getFileIcon(file.file_type)" class="w-5 h-5" />
                  </div>
                  <div>
                    <div class="flex items-center gap-2">
                      <h3 
                        class="font-medium text-gray-900 cursor-pointer hover:text-[#4285F4]" 
                        @click="file.file_type.toLowerCase() === 'txt' ? openEditModal(file) : file.file_type.toLowerCase() === 'pdf' ? openPdfPreview(file) : null"
                      >
                        {{ file.name }}
                      </h3>
                    </div>
                    <p class="text-sm text-gray-500">
                      Added {{ formatDate(file.created_at) }} • {{ formatFileSize(file.file_size) }}
                    </p>
                  </div>
                </div>
                <div class="flex items-center gap-2">
                  <button
                    @click.stop="downloadDocument(file.id)"
                    class="p-2 text-gray-400 hover:text-[#4285F4] transition-colors"
                  >
                    <Download class="w-5 h-5" />
                  </button>
                  <button
                    @click.stop="deleteDocument(file.id)"
                    class="p-2 text-gray-400 hover:text-red-500 transition-colors"
                  >
                    <Trash2 class="w-5 h-5" />
                  </button>
                </div>
              </div>
            </div>

            <!-- Empty State -->
            <div
              v-if="filteredDocuments.length === 0"
              class="bg-white rounded-xl p-8 border border-gray-200 text-center"
            >
              <div class="w-12 h-12 rounded-lg bg-gray-100 text-gray-400 flex items-center justify-center mx-auto mb-4">
                <AlertCircle class="w-6 h-6" />
              </div>
              <h3 class="text-gray-900 font-medium mb-1">No documents found</h3>
              <p class="text-gray-500 text-sm">
                {{ searchQuery ? 'Try adjusting your search terms' : 'Start by adding a document, URL, or text content' }}
              </p>
            </div>
          </div>
        </div>
        
        <!-- Assistants Tab -->
        <div v-else-if="activeTab === 'Assistants'" class="space-y-6">
          <div class="bg-white rounded-xl p-5 border border-gray-200">
            <div class="flex justify-between items-center mb-4">
              <h3 class="text-lg font-medium">Current Assistants</h3>
              <button 
                @click="openAssistantModal"
                class="px-3 py-1.5 bg-[#4285F4] text-white text-sm font-medium rounded-lg hover:bg-[#4285F4]/90 transition-colors flex items-center gap-2"
              >
                <Plus class="w-4 h-4" />
                Add Assistant
              </button>
            </div>
            <div class="space-y-3">
              <div v-for="assistant in assistants" :key="assistant.id" 
                class="flex items-center justify-between p-3 bg-gray-50 rounded-lg">
                <div class="flex items-center gap-3">
                  <div class="w-8 h-8 rounded-lg bg-[#4285F4]/10 flex items-center justify-center">
                    <Users class="w-4 h-4 text-[#4285F4]" />
                  </div>
                  <span class="font-medium">{{ assistant.name }}</span>
                </div>
                <button @click="handleRemoveAssistant(assistant.id)"
                  class="p-2 text-gray-400 hover:text-red-500 transition-colors">
                  <Trash2 class="w-4 h-4" />
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Settings Tab -->
        <div v-else-if="activeTab === 'Settings'" class="space-y-6">
          <div class="bg-white rounded-xl p-5 border border-gray-200">
            <h3 class="text-lg font-medium mb-4">Knowledge Base Settings</h3>
            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">Name</label>
                <input
                  v-model="editedName"
                  type="text"
                  class="w-full px-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#4285F4]"
                  placeholder="Enter knowledge base name"
                />
              </div>
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">Description</label>
                <textarea
                  v-model="editedDescription"
                  rows="3"
                  class="w-full px-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#4285F4]"
                  placeholder="Enter knowledge base description"
                ></textarea>
              </div>
              <div class="flex justify-between items-center pt-4">
                <button @click="handleDeleteKnowledgeBase"
                  class="px-4 py-2 text-sm font-medium text-red-600 hover:bg-red-50 rounded-lg transition-colors">
                  Delete Knowledge Base
                </button>
                <button @click="handleUpdateKnowledgeBase({ name: editedName, description: editedDescription })"
                  class="px-4 py-2 bg-[#4285F4] text-white text-sm font-medium rounded-lg hover:bg-[#4285F4]/90 transition-colors">
                  Save Changes
                </button>
              </div>
            </div>
          </div>
        </div>

        <!-- Status Tab -->
        <div v-else-if="activeTab === 'Status'" class="space-y-6">
          <div class="bg-white rounded-xl p-5 border border-gray-200">
            <h3 class="text-lg font-medium mb-4">Knowledge Base Status</h3>
            <div class="space-y-4">
              <!-- Processing status -->
              <div v-if="processingKnowledgeBase" class="p-4 bg-blue-50 rounded-lg">
                <div class="flex items-center gap-3">
                  <div class="animate-spin rounded-full h-5 w-5 border-b-2 border-[#4285F4]"></div>
                  <div>
                    <p class="font-medium text-[#4285F4]">Processing Knowledge Base</p>
                    <p class="text-sm text-gray-600">
                      {{ taskStatus?.status_message || 'Preparing your knowledge base...' }}
                    </p>
                    <div class="mt-2 bg-gray-200 h-2 rounded-full overflow-hidden">
                      <div 
                        class="h-full bg-[#4285F4]" 
                        :style="`width: ${taskStatus?.progress_percentage || 0}%`">
                      </div>
                    </div>
                    <p class="text-xs text-gray-500 mt-1">
                      {{ taskStatus?.progress_percentage?.toFixed(0) || 0 }}% complete
                    </p>
                  </div>
                </div>
              </div>
              
              <!-- Last updated info -->
              
              
              <!-- Needs reload status -->
              <div v-if="knowledgeBase?.needs_reload" class="p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
                <div class="flex items-center gap-2">
                  <AlertCircle class="w-5 h-5 text-yellow-600" />
                  <p class="text-sm text-yellow-800">
                    This knowledge base needs to be reloaded to update the assistants.
                  </p>
                </div>
              </div>
              
              <!-- Status refresh button -->
              <div class="flex justify-end">
                <button 
                  @click="handleReload"
                  :disabled="processingKnowledgeBase"
                  class="px-4 py-2 bg-[#4285F4] text-white rounded-lg text-sm font-medium hover:bg-[#4285F4]/90 transition-colors flex items-center gap-2"
                >
                  <template v-if="processingKnowledgeBase">
                    <div class="animate-spin rounded-full h-4 w-4 border-b-2 border-white"></div>
                    Processing...
                  </template>
                  <template v-else>
                    <RefreshCw class="w-4 h-4" />
                    Process Knowledge Base
                  </template>
                </button>
              </div>

              <!-- Last task information -->
              <div v-if="taskStatus" class="p-4 bg-gray-50 rounded-lg">
                <h4 class="font-medium mb-2">Last Processing Task</h4>
                <div class="space-y-2">
                  <div class="flex justify-between text-sm">
                    <span class="text-gray-600">Status</span>
                    <span :class="{
                      'text-green-600': taskStatus.status === 'COMPLETED',
                      'text-red-600': taskStatus.status === 'FAILED',
                      'text-blue-600': ['PENDING', 'PROCESSING', 'STARTED'].includes(taskStatus.status)
                    }">{{ taskStatus.status }}</span>
                  </div>
                  <div class="flex justify-between text-sm">
                    <span class="text-gray-600">Started</span>
                    <span>{{ new Date(taskStatus.created_at).toLocaleString() }}</span>
                  </div>
                  <div class="flex justify-between text-sm">
                    <span class="text-gray-600">Last Updated</span>
                    <span>{{ new Date(taskStatus.updated_at).toLocaleString() }}</span>
                  </div>
                  <div v-if="taskStatus.error" class="mt-2 p-2 bg-red-50 text-red-600 rounded text-sm">
                    {{ taskStatus.error }}
                  </div>
                </div>
              </div>
            </div>
          </div>
        </div>
      </div>

      <!-- Add Content Modal -->
      <Teleport to="body">
        <div v-if="showAddContent" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div class="bg-white rounded-xl max-w-2xl w-full p-6">
            <div class="flex justify-between items-center mb-6">
              <h2 class="text-lg font-medium">
                Add {{ formattedContentType }}
              </h2>
              <button @click="showAddContent = false" class="text-gray-400 hover:text-gray-600">
                <X class="w-5 h-5" />
              </button> 
            </div>

            <div class="space-y-4">
              <div v-if="contentType !== 'file'">
                <label class="block text-sm font-medium text-gray-700 mb-2">Title</label>
                <input
                  v-model="newDocument.title"
                  type="text"
                  class="w-full px-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#4285F4]"
                  placeholder="Enter document title"
                />
              </div>

              <template v-if="contentType === 'text'">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">Content</label>
                  <textarea
                    v-model="newDocument.content"
                    rows="8"
                    class="w-full px-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#4285F4]"
                    placeholder="Enter your content here..."
                  ></textarea>
                </div>
              </template>

              <template v-else-if="contentType === 'url'">
                <div>
                  <label class="block text-sm font-medium text-gray-700 mb-2">URL</label>
                  <input
                    v-model="newDocument.url"
                    type="url"
                    class="w-full px-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#4285F4]"
                    placeholder="https://example.com"
                  />
                </div>
              </template>

              <template v-else-if="contentType === 'file'">
                <div
                  class="border-2 border-dashed border-gray-200 rounded-lg p-6 hover:border-[#4285F4] transition-colors"
                  @dragover.prevent
                  @drop.prevent="handleFileDrop"
                >
                  <div class="relative">
                    <input
                      type="file"
                      multiple
                      @change="handleFileUpload"
                      class="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
                    />
                    <div class="text-center">
                      <Upload class="w-8 h-8 text-gray-400 mx-auto mb-2" />
                      <p class="text-sm text-gray-600">
                        Drag and drop files here, or <span class="text-[#4285F4]">browse</span>
                      </p>
                      <p class="text-xs text-gray-400 mt-1">PDF, DOC, DOCX up to 10MB</p>
                    </div>
                  </div>
                </div>

                <!-- File list -->
                <div v-if="uploadedFiles.length" class="space-y-2">
                  <div
                    v-for="(file, index) in uploadedFiles"
                    :key="index"
                    class="flex items-center justify-between p-2 bg-gray-50 rounded-lg text-sm"
                  >
                    <div class="flex items-center gap-2">
                      <File class="w-4 h-4 text-gray-400" />
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
              </template>

              <div class="flex justify-end gap-2 mt-6">
                <button
                  @click="showAddContent = false"
                  class="px-4 py-2 border border-gray-200 rounded-lg text-sm font-medium hover:border-gray-300 transition-colors"
                >
                  Cancel
                </button>
                <button
                  @click="saveDocument"
                  class="px-4 py-2 bg-[#4285F4] text-white rounded-lg text-sm font-medium hover:bg-[#3367d6] transition-colors"
                >
                  Save
                </button>
              </div>
            </div>
          </div>
        </div>
      </Teleport>

      <!-- Assistant Modal -->
      <Teleport to="body">
        <div v-if="showAssistantModal" 
          class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div class="bg-white rounded-xl w-full max-w-md p-6">
            <div class="flex justify-between items-center mb-4">
              <h3 class="text-lg font-medium">Add Assistants</h3>
              <button @click="showAssistantModal = false" class="text-gray-400 hover:text-gray-600">
                <X class="w-5 h-5" />
              </button>
            </div>
            
            <div class="space-y-4">
              <div class="max-h-[240px] overflow-y-auto">
                <div v-for="assistant in availableAssistants" :key="assistant.id" 
                  class="flex items-center p-3 hover:bg-gray-50 transition-colors">
                  <input
                    type="checkbox"
                    :value="assistant.id"
                    v-model="selectedNewAssistants"
                    class="w-4 h-4 text-[#4285F4] border-gray-300 rounded focus:ring-[#4285F4]"
                  />
                  <span class="ml-3 text-sm text-gray-700">{{ assistant.name }}</span>
                </div>
              </div>
              
              <div class="flex justify-end gap-3 pt-4 border-t">
                <button 
                  @click="showAssistantModal = false"
                  class="px-4 py-2 text-sm font-medium text-gray-600 hover:text-gray-900"
                >
                  Cancel
                </button>
                <button 
                  @click="handleAddAssistants"
                  class="px-4 py-2 bg-[#4285F4] text-white text-sm font-medium rounded-lg hover:bg-[#4285F4]/90 transition-colors"
                  :disabled="!selectedNewAssistants.length"
                >
                  Add Selected
                </button>
              </div>
            </div>
          </div>
        </div>
      </Teleport>

      <!-- Edit Text File Modal -->
      <Teleport to="body">
        <div v-if="showEditModal" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div class="bg-white rounded-xl max-w-2xl w-full p-6">
            <div class="flex justify-between items-center mb-6">
              <h2 class="text-lg font-medium">Edit Text File</h2>
              <button 
                @click="showEditModal = false" 
                class="text-gray-400 hover:text-gray-600"
              >
                <X class="w-5 h-5" />
              </button>
            </div>

            <div class="space-y-4">
              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">Title</label>
                <input
                  v-model="editedTitle"
                  type="text"
                  class="w-full px-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#4285F4]"
                  placeholder="Enter file title"
                />
              </div>

              <div>
                <label class="block text-sm font-medium text-gray-700 mb-2">Content</label>
                <textarea
                  v-model="editedContent"
                  rows="12"
                  class="w-full px-4 py-2 border border-gray-200 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-[#4285F4]"
                  placeholder="Enter your content here..."
                ></textarea>
              </div>

              <div class="flex justify-end gap-2 mt-6">
                <button
                  @click="showEditModal = false"
                  class="px-4 py-2 border border-gray-200 rounded-lg text-sm font-medium hover:border-gray-300 transition-colors"
                >
                  Cancel
                </button>
                <button
                  @click="saveTextFile"
                  class="px-4 py-2 bg-[#4285F4] text-white rounded-lg text-sm font-medium hover:bg-[#4285F4]/90 transition-colors"
                >
                  Save Changes
                </button>
              </div>
            </div>
          </div>
        </div>
      </Teleport>

      <!-- PDF Preview Modal -->
      <Teleport to="body">
        <div v-if="showPdfPreview" class="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
          <div class="bg-white rounded-xl w-[95vw] h-[95vh] flex flex-col">
            <div class="flex justify-between items-center p-4 border-b">
              <h2 class="text-lg font-medium">{{ previewFile?.name }}</h2>
              <div class="flex items-center gap-2">
                <button
                  @click="downloadDocument(previewFile!.id)"
                  class="p-2 text-gray-400 hover:text-[#4285F4] transition-colors flex items-center gap-1"
                >
                  <Download class="w-5 h-5" />
                  <span class="text-sm">Download</span>
                </button>
                <button 
                  @click="showPdfPreview = false"
                  class="p-2 text-gray-400 hover:text-gray-600"
                >
                  <X class="w-5 h-5" />
                </button>
              </div>
            </div>
            <div class="flex-1 bg-gray-100">
              <iframe
                :src="pdfUrl"
                class="w-full h-full"
                type="application/pdf"
              ></iframe>
            </div>
          </div>
        </div>
      </Teleport>
    </template>
  </div>
</template> 