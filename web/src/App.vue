<script setup lang="ts">
/**
 * App.vue —— 只负责布局编排和全局状态
 * 具体 UI 全部委托给子组件
 */
import { ref, watch } from 'vue'
import { useDark, useToggle } from '@vueuse/core'
import Sidebar from './components/Sidebar.vue'
import EmptyState from './components/EmptyState.vue'
import MessageList from './components/MessageList.vue'
import ChatInput from './components/ChatInput.vue'
import { sendMessage } from './api/chat'
import type { Session } from './components/Sidebar.vue'
import type { Message } from './components/MessageList.vue'

// 日夜模式（使用 vueuse，自动给 html 加 dark class）
const isDark = useDark()
const toggleDark = useToggle(isDark)

// 会话状态
const sessions = ref<Session[]>([])
const currentSessionId = ref(`sess-${Date.now().toString(36)}`)
const messages = ref<Message[]>([])
const loading = ref(false)

// 请求中断控制器
let abortController: AbortController | null = null

// 监听 loading 变化：如果被外部（打断按钮）设为 false，中断请求
watch(loading, (newVal) => {
  if (!newVal && abortController) {
    abortController.abort()
    abortController = null
  }
})

// 是否有对话内容（决定布局）
const hasMessages = ref(false)

// 新建会话
function handleNewSession() {
  if (messages.value.length > 0) {
    const existing = sessions.value.find(s => s.id === currentSessionId.value)
    if (!existing) {
      const first = messages.value.find(m => m.placement === 'end')
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
function handleSwitchSession(id: string) {
  currentSessionId.value = id
  messages.value = []
  hasMessages.value = false
}

// 发送消息
async function handleSend(text: string) {
  if (!text.trim() || loading.value) return

  // 首次发消息，记录到会话列表
  if (!hasMessages.value) {
    hasMessages.value = true
    const existing = sessions.value.find(s => s.id === currentSessionId.value)
    if (!existing) {
      sessions.value.unshift({
        id: currentSessionId.value,
        title: text.slice(0, 18),
      })
    }
  }

  // 用户消息
  messages.value.push({ id: Date.now(), placement: 'end', content: text })

  // AI loading
  const loadingId = Date.now() + 1
  messages.value.push({ id: loadingId, placement: 'start', content: '', loading: true })

  loading.value = true
  abortController = new AbortController()
  try {
    const res = await sendMessage(
      { message: text, session_id: currentSessionId.value },
      abortController.signal
    )
    const idx = messages.value.findIndex(m => m.id === loadingId)
    if (idx !== -1) {
      messages.value[idx] = {
        id: loadingId,
        placement: 'start',
        content: res.reply,
        loading: false,
        tools: res.tools_used,
      }
    }
  } catch (err: any) {
    const idx = messages.value.findIndex(m => m.id === loadingId)
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
</script>

<template>
  <div class="app-layout">
    <!-- 左侧边栏 -->
    <Sidebar
      :sessions="sessions"
      :current-id="currentSessionId"
      :is-dark="isDark"
      @new-session="handleNewSession"
      @switch-session="handleSwitchSession"
      @toggle-theme="toggleDark()"
    />

    <!-- 右侧主区域 -->
    <main class="main-area">
      <!-- 无对话：标题 + 输入框居中 -->
      <EmptyState
        v-if="!hasMessages"
        v-model:loading="loading"
        @send="handleSend"
      />

      <!-- 有对话：消息列表 + 底部固定输入框 -->
      <template v-else>
        <div class="chat-scroll">
          <MessageList :messages="messages" />
        </div>
        <div class="chat-footer">
          <ChatInput v-model:loading="loading" @send="handleSend" />
        </div>
      </template>
    </main>
  </div>
</template>

<style scoped>
.app-layout {
  display: flex;
  height: 100vh;
  width: 100%;
}

.main-area {
  flex: 1;
  display: flex;
  flex-direction: column;
  overflow: hidden;
  background: var(--el-bg-color-page, #f5f7fa);
}

.chat-scroll {
  flex: 1;
  overflow-y: auto;
  padding: 0 40px;
}

.chat-footer {
  padding: 16px 40px 24px;
}
</style>
