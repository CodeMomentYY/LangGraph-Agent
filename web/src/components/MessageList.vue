<script setup lang="ts">
import { ElABubble, ElABubbleList, ElAThinking } from 'element-ai-vue'
import { useTemplateRef } from 'vue'

export interface Message {
  id: number
  placement: 'start' | 'end'
  content: string
  loading?: boolean
  typing?: boolean
  thinking?: string[]  // 思考过程列表
  tools?: string[]
}

defineProps<{
  messages: Message[]
}>()

const bubbleListRef = useTemplateRef('bubbleListRef')

function scrollToBottom() {
  bubbleListRef.value?.scrollToBottom()
}

defineExpose({ scrollToBottom })
</script>

<template>
  <div class="message-list">
    <ElABubbleList ref="bubbleListRef">
      <ElABubble
        v-for="msg in messages"
        :key="msg.id"
        :placement="msg.placement"
        :content="msg.loading ? '' : msg.content"
        :loading="msg.loading"
        :typing="msg.placement === 'start' && !msg.loading && !!msg.content"
        :typing-over="true"
        :is-markdown="msg.placement === 'start' && !msg.loading"
        :variant="msg.placement === 'start' ? 'borderless' : 'filled'"
      >
        <!-- 思考过程（显示在回复内容上方） -->
        <template #header v-if="msg.thinking && msg.thinking.length">
          <ElAThinking title="思考过程">
            <div class="thinking-content">
              <div v-for="(step, i) in msg.thinking" :key="i" class="thinking-step">
                {{ step }}
              </div>
            </div>
          </ElAThinking>
        </template>
        <template #footer v-if="msg.tools && msg.tools.length">
          <span class="tools-tag">🔧 {{ msg.tools.join(', ') }}</span>
        </template>
      </ElABubble>
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

:deep(.el-ai-bubble-list__content) {
  padding-right: 8px;
}

:deep(.el-ai-bubble) {
  margin-bottom: 24px;
}

.thinking-content {
  padding: 4px 12px 8px;
  font-size: 13px;
  color: var(--el-text-color-secondary, #909399);
  line-height: 1.6;
}

.thinking-step {
  padding: 2px 0;
}

.tools-tag {
  font-size: 12px;
  color: var(--el-text-color-secondary, #909399);
}
</style>
