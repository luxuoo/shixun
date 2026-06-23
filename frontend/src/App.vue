<template>
  <n-config-provider :theme="themeStore.theme" :theme-overrides="themeOverrides">
    <n-message-provider>
      <n-dialog-provider>
        <router-view />
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { NConfigProvider, NMessageProvider, NDialogProvider } from 'naive-ui'
import type { GlobalThemeOverrides } from 'naive-ui'
import { useThemeStore } from './stores/theme'

const themeStore = useThemeStore()

const themeOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#2080f0',
    primaryColorHover: '#4098fc',
    primaryColorPressed: '#1060c9',
    borderRadius: '8px'
  },
  Card: {
    borderRadius: '12px'
  }
}
</script>

<style>
* {
  margin: 0;
  padding: 0;
  box-sizing: border-box;
}

body {
  font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial,
    'Noto Sans', sans-serif, 'Apple Color Emoji', 'Segoe UI Emoji', 'Segoe UI Symbol',
    'Noto Color Emoji';
  -webkit-font-smoothing: antialiased;
  -moz-osx-font-smoothing: grayscale;
  overflow-x: hidden;
  transition: background-color 0.3s, color 0.3s;
}

#app {
  width: 100%;
  min-height: 100vh;
}

/* 全局表格防溢出 */
.n-data-table .n-data-table-td {
  white-space: nowrap;
  max-width: 200px;
  overflow: hidden;
  text-overflow: ellipsis;
}

/* 统计数字防换行 */
.n-statistic .n-statistic-value__content {
  white-space: nowrap;
}

/* 描述列表防溢出 */
.n-descriptions .n-descriptions-table-content {
  word-break: break-word;
}

/* 表格容器允许横向滚动 */
.n-card .n-data-table {
  overflow-x: auto;
}

/* 全局响应式模态框 */
.n-modal {
  max-width: 95vw !important;
}

/* 暗黑模式全局适配 */
html.dark body {
  background-color: #101014;
  color: #e0e0e6;
}

html.dark .hero-banner {
  background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #4c1d95 100%) !important;
}

html.dark .card-section,
html.dark .task-list,
html.dark .quick-card {
  background: #1a1a2e;
  border-color: #2a2a3e;
}

html.dark .concept-card.blue {
  background: #1a1a2e;
  border-color: #2a3a5e;
}

html.dark .concept-card.green {
  background: #1a2a1e;
  border-color: #2a4a2e;
}

html.dark .formula-box {
  background: #1a1a2e;
  border-color: #2a2a3e;
}

html.dark .formula-example {
  background: #141420;
  border-color: #2a2a3e;
}

html.dark .flow-item {
  background: #1a1a2e;
}

html.dark .eval-item {
  border-color: #2a2a3e;
}

html.dark .phase-card {
  background: #1a1a2e;
}

html.dark .progress-fill {
  background: linear-gradient(90deg, #6366f1, #8b5cf6);
}

/* 移动端全局适配 */
@media (max-width: 768px) {
  .n-layout-content {
    padding: 12px !important;
  }
  .n-data-table {
    overflow-x: auto;
  }
  .n-space {
    flex-wrap: wrap !important;
  }
  .n-breadcrumb {
    display: none;
  }
  .n-modal {
    width: 95vw !important;
    max-width: 95vw !important;
    margin: 10px !important;
  }
  .n-descriptions {
    --n-column: 1 !important;
  }
  .n-descriptions-table {
    table-layout: fixed !important;
  }
  .n-descriptions .n-descriptions-table-content {
    max-width: 100% !important;
  }
  .n-form .n-form-item {
    flex-direction: column !important;
  }
  .n-form .n-form-item-label {
    width: 100% !important;
    margin-bottom: 4px;
  }
  .n-form .n-form-item-blank {
    flex: 1 !important;
  }
}
</style>
