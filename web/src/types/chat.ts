/**
 * 聊天相关类型定义
 */

export interface ThinkingStep {
  title: string
  description?: string
  icon?: string
  key?: string
}

export interface Message {
  id: number
  placement: 'start' | 'end'
  content: string
  loading?: boolean
  streaming?: boolean
  thinking?: ThinkingStep[]
  thinkingExpanded?: boolean
  tools?: string[]
}

export interface Session {
  id: string
  title: string
}
