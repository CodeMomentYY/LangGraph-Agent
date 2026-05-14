<script setup lang="ts">
import { ElASender } from 'element-ai-vue'
import { ref } from 'vue'

const loading = defineModel<boolean>('loading', { default: false })

const emit = defineEmits<{
  (e: 'send', text: string): void
}>()

const content = ref('')
const focusClass = ref(false)

function handleSend(text: string) {
  emit('send', text)
  content.value = ''  // 发送后清空
}
</script>

<template>
  <div class="chat-input">
    <div class="wrapper" :class="{ 'focus-class': focusClass }">
      <ElASender
        v-model="content"
        v-model:loading="loading"
        placeholder="请输入聊天内容"
        @focus="focusClass = true"
        @blur="focusClass = false"
        @send="handleSend"
      />
    </div>
  </div>
</template>

<style scoped lang="scss">
.chat-input {
  max-width: 780px;
  width: 100%;
  margin: 0 auto;
}

.wrapper {
  width: 100%;
  border-radius: 12px;
  padding: 8px;
  border: 1px solid rgba(17, 25, 37, 0.15);

  &.focus-class {
    border-color: rgba(17, 25, 37, 0.45);
  }
}

html.dark {
  .wrapper {
    border-color: rgba(121, 121, 121, 0.6);

    &.focus-class {
      border-color: rgba(255, 255, 255, 0.6);
    }
  }
}

:deep(.el-ai-base-sender-input__editor p) {
  min-height: 24px;
  line-height: 24px;
  font-size: 16px;
}
</style>
