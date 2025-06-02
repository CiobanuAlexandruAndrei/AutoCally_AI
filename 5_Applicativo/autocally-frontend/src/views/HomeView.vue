<template>
    <div class="h-full flex flex-col lg:flex-row">
        <!-- Left sidebar with assistants list -->
        <div class="w-full lg:w-80 border-b lg:border-b-0 lg:border-r border-gray-200 bg-gray-50 p-6 overflow-y-auto">
            <div class="flex justify-between items-center mb-8">
                <h1 class="text-lg font-semibold text-gray-800">My Assistants</h1>
                <button @click="createAssistant"
                    class="p-2 bg-blue-600 text-white rounded-lg text-sm font-medium hover:bg-blue-700 transition-colors">
                    <Plus class="w-4 h-4" />
                </button>
            </div>

            <div class="space-y-3">
                <div v-for="assistant in assistants" :key="assistant.id" @click="selectAssistant(assistant)" :class="[
                    'bg-white rounded-xl p-4 border cursor-pointer transition-colors',
                    selectedAssistantId === assistant.id
                        ? 'border-blue-400'
                        : 'border-gray-100 hover:border-blue-400'
                ]">
                    <div class="flex items-start justify-between">
                        <div>
                            <h3 class="font-medium text-gray-800" @click.stop="startEditing(assistant)">
                                <span v-if="editingAssistant?.id !== assistant.id">{{ assistant.name }}</span>
                                <input v-else type="text" v-model="editingAssistant.name" @blur="saveEdit"
                                    @keyup.enter="saveEdit" @keyup.esc="cancelEdit" ref="editInput"
                                    class="w-full border border-blue-400 rounded px-1 focus:outline-none" />
                            </h3>
                            <p class="text-sm text-gray-500">{{ assistant.callsMade }} calls made</p>
                        </div>
                        <div class="text-right">
                            <div class="text-sm font-medium"
                                :class="assistant.isActive ? 'text-green-600' : 'text-gray-400'">
                                {{ assistant.isActive ? 'Active' : 'Not Active' }}
                            </div>
                            <button @click.stop="deleteAssistant(assistant)"
                                class="mt-2 text-red-500 hover:text-red-600 text-sm">
                                Delete
                            </button>
                        </div>
                    </div>
                </div>
            </div>

            <!-- Add loading and error states -->
            <div v-if="isLoading" class="flex items-center justify-center h-full">
                <div class="animate-spin rounded-full h-8 w-8 border-b-2 border-blue-600"></div>
            </div>

            <div v-else-if="error" class="p-4 bg-red-50 text-red-600 rounded-lg m-4">
                {{ error }}
            </div>
        </div>

        <!-- Main content area -->
        <div class="flex-1 overflow-y-auto">
            <template v-if="selectedAssistantId">
                <AssistantsView :assistant-id="selectedAssistantId" />
            </template>
            <template v-else>
                <div class="h-full flex items-center justify-center text-gray-500 bg-white">
                    Select an assistant to get started
                </div>
            </template>
        </div>
    </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { Plus } from 'lucide-vue-next'
import AssistantsView from './AssistantsView.vue'
import { assistantsApi } from '@/services/api'

interface Assistant {
    id: string
    name: string
    prompt?: string
    cartesia_voice_id?: string
    phone_number_id?: string
    language: string
    description: string
    costPerMinute: number
    latency: number
    isActive: boolean
    callsMade: number
}

const selectedAssistantId = ref<string | null>(null)
const editingAssistant = ref<Assistant | null>(null)
const editInput = ref<HTMLInputElement | null>(null)

const assistants = ref<Assistant[]>([])
const isLoading = ref(false)
const error = ref('')

const createAssistant = async () => {
    try {
        const response = await assistantsApi.create({
            name: 'New Assistant'
        })

        assistants.value.push({
            ...response.assistant,
            language: 'English',
            description: '',
            costPerMinute: 0.03,
            latency: 700,
            isActive: true,
            callsMade: 0
        })
    } catch (err) {
        console.error('Failed to create assistant:', err)
        error.value = 'Failed to create assistant'
    }
}

const fetchAssistants = async () => {
    try {
        isLoading.value = true
        const response = await assistantsApi.getAll()

        assistants.value = response.map((assistant: any) => ({
            ...assistant,
            language: 'English',
            description: '',
            costPerMinute: 0.03,
            latency: 700,
            isActive: true,
            callsMade: 0
        }))
    } catch (err) {
        console.error('Failed to fetch assistants:', err)
        error.value = 'Failed to fetch assistants'
    } finally {
        isLoading.value = false
    }
}

onMounted(() => {
    fetchAssistants()
})

const selectAssistant = async (assistant: Assistant) => {
    selectedAssistantId.value = assistant.id;
    try {
        isLoading.value = true;
        const response = await assistantsApi.getById(assistant.id);
        
        // Update the assistant in the list with the fresh data
        const index = assistants.value.findIndex(a => a.id === assistant.id);
        if (index !== -1) {
            assistants.value[index] = {
                ...assistants.value[index],
                ...response,
                // Preserve any UI-specific properties
                isActive: assistants.value[index].isActive,
                callsMade: assistants.value[index].callsMade,
                language: assistants.value[index].language,
                description: assistants.value[index].description,
                costPerMinute: assistants.value[index].costPerMinute,
                latency: assistants.value[index].latency
            };
        }
    } catch (err) {
        console.error('Failed to fetch assistant data:', err);
        error.value = 'Failed to fetch assistant data';
    } finally {
        isLoading.value = false;
    }
}

const startEditing = (assistant: Assistant) => {
    editingAssistant.value = { ...assistant }
    setTimeout(() => {
        editInput.value?.focus()
    })
}

const saveEdit = async () => {
    if (editingAssistant.value) {
        try {
            await assistantsApi.updateName(
                parseInt(editingAssistant.value.id),
                {
                    name: editingAssistant.value.name
                }
            )

            const index = assistants.value.findIndex(a => a.id === editingAssistant.value?.id)
            if (index !== -1) {
                assistants.value[index].name = editingAssistant.value.name
            }
        } catch (err) {
            console.error('Failed to update assistant name:', err)
            error.value = 'Failed to update assistant name'
        }
    }
    editingAssistant.value = null
}

const deleteAssistant = async (assistant: Assistant) => {
    try {
        await assistantsApi.delete(assistant.id)
        assistants.value = assistants.value.filter(a => a.id !== assistant.id)
        if (selectedAssistantId.value === assistant.id) {
            selectedAssistantId.value = null
        }
    } catch (err) {
        console.error('Failed to delete assistant:', err)
        error.value = 'Failed to delete assistant'
    }
}

const updatePrompt = async (assistant: Assistant, prompt: string) => {
    try {
        await assistantsApi.updatePrompt(assistant.id, { prompt })
        const index = assistants.value.findIndex(a => a.id === assistant.id)
        if (index !== -1) {
            assistants.value[index].prompt = prompt
        }
    } catch (err) {
        console.error('Failed to update assistant prompt:', err)
        error.value = 'Failed to update assistant prompt'
    }
}

const cancelEdit = () => {
    editingAssistant.value = null
}
</script>