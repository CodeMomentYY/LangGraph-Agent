const API_BASE = '/api'

export interface ChatRequest {
  message: string
  user_id?: string
  session_id?: string
}

export interface ChatResponse {
  reply: string
  session_id: string
  tools_used: string[]
}

// SSE 事件类型
export interface StreamEvent {
  type: 'start' | 'status' | 'intents' | 'tool_call' | 'tool_result' | 'reasoning' | 'reply' | 'done'
  session_id?: string
  node?: string
  text?: string
  intents?: string[]
  mode?: string
  tools?: string[]
  content?: string
  tools_used?: string[]
}

/**
 * 流式发送消息（SSE），通过回调逐步接收事件
 */
export async function sendMessageStream(
  req: ChatRequest,
  onEvent: (event: StreamEvent) => void,
  signal?: AbortSignal
): Promise<void> {
  const response = await fetch(`${API_BASE}/chat/stream`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
    signal,
  })

  if (!response.ok) throw new Error(`HTTP ${response.status}`)
  if (!response.body) throw new Error('No response body')

  const reader = response.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })

    // 按 SSE 格式解析：每条消息以 \n\n 分隔
    const parts = buffer.split('\n\n')
    buffer = parts.pop() || '' // 最后一段可能不完整，留到下次

    for (const part of parts) {
      if (part.startsWith('data: ')) {
        try {
          const data = JSON.parse(part.slice(6)) as StreamEvent
          onEvent(data)
        } catch {
          // 忽略解析错误
        }
      }
    }
  }
}

/**
 * 普通发送消息（一次性返回，保留兼容）
 */
export async function sendMessage(req: ChatRequest, signal?: AbortSignal): Promise<ChatResponse> {
  const response = await fetch(`${API_BASE}/chat`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(req),
    signal,
  })
  if (!response.ok) throw new Error(`HTTP ${response.status}`)
  return response.json()
}
