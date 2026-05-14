<script setup lang="ts">
/**
 * 侧边栏组件
 * 职责：品牌展示、新建对话、会话列表、日夜切换
 */
import { Sunny, Moon } from '@element-plus/icons-vue'

export interface Session {
  id: string
  title: string
}

defineProps<{
  sessions: Session[]
  currentId: string
  isDark: boolean
}>()

const emit = defineEmits<{
  (e: 'new-session'): void
  (e: 'switch-session', id: string): void
  (e: 'toggle-theme'): void
}>()
</script>

<template>
  <aside class="sidebar">
    <!-- 顶部 -->
    <div class="sidebar-top">
      <span class="brand">MomentYY</span>
      <el-switch
        :model-value="isDark"
        @change="emit('toggle-theme')"
        inline-prompt
        :active-icon="Moon"
        :inactive-icon="Sunny"
        active-color="#2c2c2c"
        inactive-color="#c0c4cc"
      />
    </div>

    <!-- 新建对话 -->
    <button class="new-btn" @click="emit('new-session')">＋ 开启新对话</button>

    <!-- 会话列表 -->
    <div class="session-list">
      <template v-if="sessions.length">
        <div class="group-title">最近对话</div>
        <div
          v-for="s in sessions"
          :key="s.id"
          class="session-item"
          :class="{ active: s.id === currentId }"
          @click="emit('switch-session', s.id)"
        >
          {{ s.title }}
        </div>
      </template>
    </div>
  </aside>
</template>

<style scoped>
.sidebar {
  width: 260px;
  height: 100%;
  display: flex;
  flex-direction: column;
  border-right: 1px solid var(--el-border-color-lighter, #e8e8e8);
  background: var(--el-bg-color-page, #f5f7fa);
  flex-shrink: 0;
}

.sidebar-top {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 16px;
}

/* Switch 颜色覆盖 */
.sidebar-top :deep(.el-switch.is-checked .el-switch__core) {
  background-color: #4a4a4a;
  border-color: #4a4a4a;
}
.sidebar-top :deep(.el-switch .el-switch__core) {
  background-color: #dcdfe6;
  border-color: #dcdfe6;
}
.brand {
  font-size: 18px;
  font-weight: 700;
}

.new-btn {
  margin: 0 12px 12px;
  padding: 10px;
  border: 1px solid var(--el-border-color, #dcdfe6);
  border-radius: 8px;
  background: transparent;
  cursor: pointer;
  font-size: 14px;
}
.new-btn:hover {
  background: var(--el-fill-color-lighter, #fafafa);
}

.session-list {
  flex: 1;
  overflow-y: auto;
  padding: 0 8px;
}
.group-title {
  font-size: 12px;
  color: var(--el-text-color-secondary, #909399);
  padding: 8px 8px 4px;
}
.session-item {
  padding: 10px 12px;
  border-radius: 8px;
  cursor: pointer;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.session-item:hover {
  background: var(--el-fill-color-light, #f5f5f5);
}
.session-item.active {
  background: var(--el-color-primary-light-9, #ecf5ff);
  color: var(--el-color-primary, #409eff);
}
</style>
