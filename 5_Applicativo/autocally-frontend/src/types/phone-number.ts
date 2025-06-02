export interface PhoneNumber {
  id: number
  phone_number: string
  usedBy?: string
  spent?: number
  lastCall?: string
  totalCalls?: number
  avgDuration?: string
  successRate?: number
} 