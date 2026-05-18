<script setup lang="ts">
/**
 * App.vue —— 只负责布局编排
 * 聊天逻辑在 composables/useChat.ts
 */
import { computed, nextTick, useTemplateRef } from 'vue'
import { useDark, useToggle } from '@vueuse/core'
import { ElAConfigProvider } from 'element-ai-vue'
import Sidebar from './components/Sidebar.vue'
import EmptyState from './components/EmptyState.vue'
import MessageList from './components/MessageList.vue'
import ChatInput from './components/ChatInput.vue'
import { useChat } from './composables/useChat'

// 日夜模式
const isDark = useDark()
const toggleDark = useToggle(isDark)
const aiTheme = computed(() => isDark.value ? 'dark' : 'light')

// 聊天逻辑
const {
  sessions,
  currentSessionId,
  messages,
  loading,
  hasMessages,
  newSession,
  switchSession,
  sendMessage,
} = useChat()

// MessageList 引用，用于滚动
const messageListRef = useTemplateRef('messageListRef')

function handleSend(text: string) {
  sendMessage(text, () => {
    nextTick(() => messageListRef.value?.scrollToBottom())
  })
}
</script>

<template>
  <ElAConfigProvider :theme="aiTheme">
    <div class="app-layout">
      <!-- 左侧边栏 -->
      <Sidebar
        :sessions="sessions"
        :current-id="currentSessionId"
        :is-dark="isDark"
        @new-session="newSession"
        @switch-session="switchSession"
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
            <MessageList ref="messageListRef" :messages="messages" />
          </div>
          <div class="chat-footer">
            <ChatInput v-model:loading="loading" @send="handleSend" />
          </div>
        </template>
      </main>
    </div>
  </ElAConfigProvider>
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
  overflow: hidden;
  padding: 0 40px;
  padding-right: 16px;
}

.chat-footer {
  padding: 16px 40px 24px;
}
</style>
