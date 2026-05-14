<script setup lang="ts">
import ChatInput from './ChatInput.vue'

const loading = defineModel<boolean>('loading', { default: false })

const emit = defineEmits<{
  (e: 'send', text: string): void
}>()
</script>

<template>
  <div class="empty-state">
    <div class="empty-content">
      <h1 class="title">使用 MomentYY 开始对话</h1>
      <p class="subtitle">你的全能 AI 工作助手</p>
    </div>
    <ChatInput v-model:loading="loading" @send="(text) => emit('send', text)" />
  </div>
</template>

<style scoped>
.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  padding: 0 40px 80px;
  gap: 32px;
}
.empty-content {
  text-align: center;
}
.title {
  font-size: 24px;
  font-weight: 600;
  margin-bottom: 8px;
  color: var(--el-text-color-primary, #303133);
}
.subtitle {
  font-size: 14px;
  color: var(--el-text-color-secondary, #909399);
}
</style>
