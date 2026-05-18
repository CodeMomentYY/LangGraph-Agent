/**
 * 聊天逻辑 composable
 * 管理会话状态、消息发送（SSE 流式）、会话切换
 */
import { ref, watch } from 'vue'
import { sendMessageStream } from '../api/chat'
import type { StreamEvent } from '../api/chat'
import type { Message, Session } from '../types/chat'

export type { Session }

export function useChat() {
  const sessions = ref<Session[]>([])
  const currentSessionId = ref(`sess-${Date.now().toString(36)}`)
  const messages = ref<Message[]>([])
  const loading = ref(false)
  const hasMessages = ref(false)

  let abortController: AbortController | null = null

  // 监听 loading 变化：打断按钮触发时中断请求
  watch(loading, (newVal: boolean) => {
    if (!newVal && abortController) {
      abortController.abort()
      abortController = null
    }
  })

  // 新建会话
  function newSession() {
    if (messages.value.length > 0) {
      const existing = sessions.value.find((s: Session) => s.id === currentSessionId.value)
      if (!existing) {
        const first = messages.value.find((m: Message) => m.placement === 'end')
        sessions.value.unshift({
          id: currentSessionId.value,
          title: first?.content.slice(0, 18) || '新对话',
        })
      }
    }
    messages.value = []
    hasMessages.value = false
    currentSessionId.value = `sess-${Date.now().toString(36)}`
  }

  // 切换会话
  function switchSession(id: string) {
    currentSessionId.value = id
    messages.value = []
    hasMessages.value = false
  }

  // 发送消息（SSE 流式）
  async function sendMessage(text: string, onScroll?: () => void) {
    if (!text.trim() || loading.value) return

    // 首次发消息，记录到会话列表
    if (!hasMessages.value) {
      hasMessages.value = true
      const existing = sessions.value.find((s: Session) => s.id === currentSessionId.value)
      if (!existing) {
        sessions.value.unshift({
          id: currentSessionId.value,
          title: text.slice(0, 18),
        })
      }
    }

    // 用户消息
    messages.value.push({ id: Date.now(), placement: 'end', content: text })

    // AI loading 占位
    const loadingId = Date.now() + 1
    messages.value.push({ id: loadingId, placement: 'start', content: '', loading: true })

    // 滚动到底部
    onScroll?.()

    loading.value = true
    abortController = new AbortController()

    try {
      await sendMessageStream(
        { message: text, session_id: currentSessionId.value },
        (event: StreamEvent) => {
          const idx = messages.value.findIndex((m: Message) => m.id === loadingId)
          if (idx === -1) return
          handleStreamEvent(event, idx, loadingId)
          // 每次事件更新后滚动到底部
          onScroll?.()
        },
        abortController.signal
      )
    } catch (err: any) {
      const idx = messages.value.findIndex((m: Message) => m.id === loadingId)
      if (idx !== -1) {
        if (err.name === 'AbortError') {
          messages.value.splice(idx, 1)
        } else {
          messages.value[idx] = {
            id: loadingId,
            placement: 'start',
            content: `⚠️ 请求失败：${err.message || '网络错误'}`,
            loading: false,
          }
        }
      }
    } finally {
      loading.value = false
      abortController = null
    }
  }

  // 处理 SSE 事件
  function handleStreamEvent(event: StreamEvent, idx: number, loadingId: number) {
    switch (event.type) {
      case 'start':
        if (event.session_id) {
          currentSessionId.value = event.session_id
        }
        break
      case 'status':
        if (['mode_router', 'step_router', 'advance_step'].includes(event.node || '')) break
        appendThinking(idx, { title: event.text || '' })
        break
      case 'intents':
        appendThinking(idx, {
          title: '意图识别',
          description: event.text || `${event.intents?.join(' → ')}（${event.mode}）`,
        })
        break
      case 'tool_call':
        appendThinking(idx, {
          title: '调用工具',
          description: event.text || event.tools?.join(', ') || '',
        })
        break
      case 'tool_result':
        appendThinking(idx, {
          title: '工具结果',
          description: event.content || '',
        })
        break
      case 'reasoning':
        appendThinking(idx, {
          title: '思考',
          description: event.content || '',
        })
        break
      case 'reply':
        messages.value[idx] = {
          id: loadingId,
          placement: 'start',
          content: event.content || '',
          loading: false,
          streaming: false,
          thinkingExpanded: false,
          tools: event.tools_used,
          thinking: messages.value[idx].thinking,
        }
        break
    }
  }

  // 追加思考步骤
  function appendThinking(idx: number, step: { title: string; description?: string }) {
    const steps = [...(messages.value[idx].thinking || []), step]
    messages.value[idx] = {
      ...messages.value[idx],
      loading: false,
      streaming: true,
      thinkingExpanded: true,
      thinking: steps,
    }
  }

  return {
    sessions,
    currentSessionId,
    messages,
    loading,
    hasMessages,
    newSession,
    switchSession,
    sendMessage,
  }
}
