<script setup lang="ts">
import { ElABubble, ElABubbleList, ElAThinking, ElAMarkdown } from 'element-ai-vue'
import { useTemplateRef, computed } from 'vue'
import { useDark } from '@vueuse/core'
import type { ThinkingStep, Message } from '../types/chat'

const isDark = useDark()

defineProps<{
  messages: Message[]
}>()

const bubbleListRef = useTemplateRef('bubbleListRef')

function scrollToBottom() {
  bubbleListRef.value?.scrollToBottom()
}

function formatThinkingMarkdown(steps: ThinkingStep[]): string {
  return steps.map(step => {
    if (step.description) {
      return `**${step.title}**\n\n${step.description}`
    }
    return step.title
  }).join('\n\n')
}

defineExpose({ scrollToBottom })
</script>

<template>
  <div class="message-list">
    <ElABubbleList ref="bubbleListRef">
      <template v-for="msg in messages" :key="msg.id">
        <!-- 用户消息 -->
        <ElABubble
          v-if="msg.placement === 'end'"
          placement="end"
          :content="msg.content"
          variant="filled"
        />

        <!-- AI 消息 -->
        <div v-else class="ai-message">
          <!-- Loading 状态 -->
          <ElABubble
            v-if="msg.loading && !msg.streaming"
            placement="start"
            content=""
            :loading="true"
            variant="borderless"
          />

          <!-- Streaming + 最终回复 -->
          <template v-else>
            <!-- 思考过程（Thinking 面板） -->
            <ElAThinking
              v-if="msg.thinking && msg.thinking.length"
              v-model="msg.thinkingExpanded"
              :title="msg.streaming ? '正在思考...' : `已完成思考（${msg.thinking.length} 步）`"
            >
              <ElAMarkdown
                :content="formatThinkingMarkdown(msg.thinking)"
                :theme="isDark ? 'dark' : 'light'"
              />
            </ElAThinking>

            <!-- 最终回复内容 -->
            <ElABubble
              v-if="msg.content"
              placement="start"
              :content="msg.content"
              :typing="true"
              :is-markdown="true"
              variant="borderless"
            />
          </template>
        </div>
      </template>
    </ElABubbleList>
  </div>
</template>

<style scoped>
.message-list {
  max-width: 780px;
  width: 100%;
  height: 100%;
  margin: 0 auto;
  padding: 20px 0;
}

:deep(.el-ai-bubble-list) {
  height: 100%;
  padding-right: 12px;
}

:deep(.el-ai-bubble-list > button),
:deep(.el-ai-bubble-list [class*="back"]) {
  display: none !important;
}

:deep(.el-ai-bubble-list-bottom-action__inner) {
  display: none !important;
}

:deep(.el-ai-bubble-list__content) {
  padding-right: 8px;
}

.ai-message {
  margin-bottom: 24px;
}

.ai-message :deep(.el-ai-thinking) {
  margin: 16px 0 8px;
}

.tools-tag {
  font-size: 12px;
  color: var(--el-text-color-secondary, #909399);
}
</style>
