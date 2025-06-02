import axios from 'axios'
import { useAuthStore } from '@/stores/auth'

// Ensure we're using HTTPS
//const backendUrl = import.meta.env.VITE_BACKEND_URL || 'https://localhost:5001'
const backendUrl = 'https://172.20.0.14:6969'
const baseURL = backendUrl.startsWith('https://') ? `${backendUrl}/api` : `https://${backendUrl}/api`

const axiosInstance = axios.create({
  baseURL,
  headers: {
    'Content-Type': 'application/json',
  },
  withCredentials: true,
  ...(import.meta.env.DEV && {
    validateStatus: () => true, // Accept all status codes in development
    httpsAgent: {
      rejectUnauthorized: false
    }
  })
})

// Add response interceptor to handle SSL errors
axiosInstance.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.code === 'CERT_HAS_EXPIRED' || error.code === 'UNABLE_TO_VERIFY_LEAF_SIGNATURE') {
      console.warn('SSL Certificate validation failed, but continuing in development mode')
      return Promise.resolve(error.response)
    }
    return Promise.reject(error)
  }
)

export const API_URL = axiosInstance.defaults.baseURL
export default axiosInstance

// Helper function to get headers with authorization
const getHeaders = () => {
  const authStore = useAuthStore()
  return {
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${authStore.token}`
    }
  }
}

export const assistantsApi = {
  create: async (data: {
    name?: string
    prompt?: string
    greeting_message?: string
    cartesia_voice_id?: string
    phone_number_id?: string
  }) => {
    const response = await axiosInstance.post('/assistants/create', data, getHeaders())
    return response.data
  },

  getAll: async () => {
    const response = await axiosInstance.get('/assistants/', getHeaders())
    return response.data
  },

  getById: async (id: string | number) => {
    const response = await axiosInstance.get(`/assistants/${id}`, getHeaders())
    return response.data
  },

  delete: async (id: string | number) => {
    const response = await axiosInstance.delete(`/assistants/delete/${id}`, getHeaders())
    return response.data
  },

  update: async (id: number, data: { 
    name?: string;
    prompt?: string;
    greeting_message?: string;
    cartesia_voice_id?: string;
    phone_number_id?: string;
    llm_model?: string;
    llm_temperature?: number;
    llm_max_tokens?: number;
  }) => {
    const response = await axiosInstance.put(`/assistants/update/${id}`, data, getHeaders())
    return response.data
  },

  updateName: async (id: number, data: { name: string;}) => {
    const response = await axiosInstance.put(`/assistants/update/${id}`, data, getHeaders())
    return response.data
  },

  updatePrompt: async (id: string | number, data: { prompt: string }) => {
    const response = await axiosInstance.put(
      `/assistants/${id}/prompt`,
      data,
      getHeaders()
    )
    return response.data
  },

  updateVoiceID: async (id: number, data: { cartesia_voice_id: string;}) => {
    const response = await axiosInstance.put(`/assistants/update/${id}`, data, getHeaders())
    return response.data
  },

  getVoices: async () => {
    const response = await axiosInstance.get('/assistants/voices', getHeaders())
    return {
      voices: response.data as Array<{
        id: string;
        name: string;
        description: string;
        language: string;
        gender: string;
      }>,
      languages: response.data.languages as string[]
    }
  },

  // Fetch handles streaming responses better than axios
  chat: async (id: number, data: { question: string }) => {
    const response = await fetch(`${API_URL}/assistants/${id}/chat`, {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        'Authorization': `Bearer ${useAuthStore().token}`
      },
      body: JSON.stringify(data)
    })
  
    if (!response.ok) {
      throw new Error('Network response was not ok')
    }
  
    return response.json()
  }
}

export const phoneNumbersApi = {
  importFromTwilio: async (config: {
    accountSid: string
    authToken: string
    phoneNumber: string
  }) => {
    const response = await axiosInstance.post('/phone-numbers/', {
      account_sid: config.accountSid,
      auth_token: config.authToken,
      phone_number: config.phoneNumber
    }, getHeaders())
    return response.data
  },

  delete: async (phoneNumberId: number) => {
    const response = await axiosInstance.delete(
      `/phone-numbers/${phoneNumberId}`,
      getHeaders()
    )
    return response.data
  },

  update: async (phoneNumberId: number, data: {
    phone_number?: string
    account_sid?: string
    auth_token?: string
    is_verified?: boolean
  }) => {
    const response = await axiosInstance.put(
      `/phone-numbers/${phoneNumberId}`,
      data,
      getHeaders()
    )
    return response.data
  },

  getAll: async () => {
    const response = await axiosInstance.get('/phone-numbers/', getHeaders())
    return response.data
  }
}

export const knowledgeBaseApi = {
  getAll: async () => {
    const response = await axiosInstance.get('/base-knowledge/', getHeaders())
    return response.data
  },

  getById: async (id: number) => {
    const response = await axiosInstance.get(`/base-knowledge/${id}`, getHeaders())
    return response.data
  },

  create: async (data: {
    name: string
    description?: string
    assistant_ids: string[]
  }) => {
    const response = await axiosInstance.post('/base-knowledge/', data, getHeaders())
    return response.data
  },

  getFiles: async (id: number) => {
    const response = await axiosInstance.get(`/base-knowledge/${id}/files`, getHeaders())
    return response.data
  },

  addAssistant: async (baseKnowledgeId: number, assistantId: string) => {
    const response = await axiosInstance.post(
      `/base-knowledge/${baseKnowledgeId}/assistants`,
      { assistant_id: assistantId },
      getHeaders()
    )
    return response.data
  },

  removeAssistant: async (baseKnowledgeId: number, assistantId: string) => {
    const response = await axiosInstance.delete(
      `/base-knowledge/${baseKnowledgeId}/assistants/${assistantId}`,
      getHeaders()
    )
    return response.data
  },

  update: async (id: number, data: {
    name?: string
    description?: string
  }) => {
    const response = await axiosInstance.put(
      `/base-knowledge/${id}`,
      data,
      getHeaders()
    )
    return response.data
  },

  delete: async (id: number) => {
    const response = await axiosInstance.delete(
      `/base-knowledge/${id}`,
      getHeaders()
    )
    return response.data
  },

  uploadFile: async (baseKnowledgeId: number, file: File, description?: string) => {
    const formData = new FormData()
    formData.append('file', file)
    if (description) {
      formData.append('description', description)
    }

    const response = await axiosInstance.post(
      `/base-knowledge/${baseKnowledgeId}/files`,
      formData,
      {
        ...getHeaders(),
        headers: {
          ...getHeaders().headers,
          'Content-Type': 'multipart/form-data'
        }
      }
    )
    return response.data
  },

  createTextDocument: async (baseKnowledgeId: number, data: {
    title: string
    content: string
    description?: string
  }) => {
    const response = await axiosInstance.post(
      `/base-knowledge/${baseKnowledgeId}/text`,
      data,
      getHeaders()
    )
    return response.data
  },

  deleteFile: async (baseKnowledgeId: number, fileId: number) => {
    const response = await axiosInstance.delete(
      `/base-knowledge/${baseKnowledgeId}/files/${fileId}`,
      getHeaders()
    )
    return response.data
  },

  getFileContent: async (baseKnowledgeId: number, fileId: number) => {
    const response = await axiosInstance.get(
      `/base-knowledge/${baseKnowledgeId}/files/${fileId}/content`,
      getHeaders()
    )
    return response.data
  },

  downloadFile: async (baseKnowledgeId: number, fileId: number) => {
    const response = await axiosInstance.get(
      `/base-knowledge/${baseKnowledgeId}/files/${fileId}/download`,
      {
        ...getHeaders(),
        responseType: 'blob'
      }
    )
    return response.data
  },

  updateTextFile: async (
    baseKnowledgeId: number, 
    fileId: number, 
    data: {
      title?: string
      content?: string
      description?: string
    }
  ) => {
    const response = await axiosInstance.put(
      `/base-knowledge/${baseKnowledgeId}/files/${fileId}`,
      data,
      getHeaders()
    )
    return response.data
  },

  startProcessing: async (id: number) => {
    const response = await axiosInstance.post(`/base-knowledge/${id}/process`, {}, getHeaders())
    return response.data
  },

  getTaskStatus: async (taskId: string) => {
    const response = await axiosInstance.get(`/base-knowledge/tasks/${taskId}`, getHeaders())
    return response.data
  },

  getLastTaskStatus: async (id: number) => {
    const response = await axiosInstance.get(`/base-knowledge/${id}/tasks/last`, getHeaders())
    return response.data
  }
}

export const testCallsApi = {
  startTestCall: async (phoneNumberId: number) => {
    console.log('Starting test call with phone number ID:', phoneNumberId);
    try {
      const response = await axiosInstance.post('/calls/test-call/start', { phone_number_id: phoneNumberId }, getHeaders())
      console.log('Start test call response:', response.data);
      return response.data
    } catch (error) {
      console.error('Error starting test call:', error);
      throw error;
    }
  },

  endTestCall: async (callId: number) => {
    console.log('Ending test call with ID:', callId);
    try {
      const response = await axiosInstance.post('/calls/test-call/end', { call_id: callId }, getHeaders())
      console.log('End test call response:', response.data);
      return response.data
    } catch (error) {
      console.error('Error ending test call:', error);
      throw error;
    }
  },

  getAvailablePhoneNumbers: async () => {
    const response = await axiosInstance.get('/calls/test-call/available-phone-numbers', getHeaders())
    return response.data
  }
} 