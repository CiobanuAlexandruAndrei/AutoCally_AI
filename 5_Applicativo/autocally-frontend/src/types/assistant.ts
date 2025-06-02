export interface Assistant {
  id: string
  name: string
  prompt?: string
  greeting_message?: string
  cartesia_voice_id?: string
  phone_number_id?: string
  language: string
  description: string
  costPerMinute: number
  latency: number
  isActive: boolean
  callsMade: number
  llm_model: string
  llm_temperature: number
  llm_max_tokens: number
} 