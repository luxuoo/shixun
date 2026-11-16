<template>
  <n-config-provider :theme="themeStore.theme" :theme-overrides="overrides">
    <n-message-provider>
      <n-dialog-provider>
        <router-view />
      </n-dialog-provider>
    </n-message-provider>
  </n-config-provider>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { NConfigProvider, NMessageProvider, NDialogProvider } from 'naive-ui'
import type { GlobalThemeOverrides } from 'naive-ui'
import { useThemeStore } from './stores/theme'

const themeStore = useThemeStore()

/* 亮色：正文/次要文字整体加深，边框加实，卡片与页面分层更清楚 */
const lightOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#1f6feb',
    primaryColorHover: '#3b82f6',
    primaryColorPressed: '#1a5fd0',
    borderRadius: '8px',
    textColorBase: '#111827',
    textColor1: '#111827',
    textColor2: '#374151',
    textColor3: '#6b7280',
    borderColor: '#dcdfe6',
    dividerColor: '#e5e7eb'
  },
  Card: {
    borderRadius: '12px',
    borderColor: '#e2e5ea'
  },
  DataTable: {
    thColor: '#f3f4f6',
    thTextColor: '#374151',
    tdTextColor: '#1f2937',
    borderColor: '#e5e7eb'
  },
  Tag: {
    border: '1px solid transparent'
  }
}

/* 暗色：保证正文与辅助文字在深底上足够亮 */
const darkOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#4d8ef7',
    primaryColorHover: '#6ba3f9',
    primaryColorPressed: '#3576dd',
    borderRadius: '8px',
    textColorBase: '#f2f4f8',
    textColor1: '#f2f4f8',
    textColor2: '#c8cdd8',
    textColor3: '#9aa1b0',
    borderColor: '#34374a',
    dividerColor: '#2a2d3d'
  },
  Card: {
    borderRadius: '12px',
    borderColor: '#2f3242'
  },
  DataTable: {
    thColor: '#22242f',
    thTextColor: '#c8cdd8',
    tdTextColor: '#e6e8ee',
    borderColor: '#2f3242'
  }
}

const overrides = computed(() => (themeStore.isDark ? darkOverrides : lightOverrides))
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
.n-statistic .n-statistic-value__content { white-space: nowrap; }
.n-descriptions .n-descriptions-table-content { word-break: break-word; }
.n-card .n-data-table { overflow-x: auto; }
.n-modal { max-width: 95vw !important; }

/* ==========================================
   暗黑模式全局适配
   ========================================== */
html.dark body {
  background-color: #101014;
  color: #e0e0e6;
}

/* --- 顶栏 --- */
html.dark .student-header,
html.dark .admin-header {
  background: #18181c !important;
  border-color: #2a2a3e !important;
}

/* --- 管理后台内容区 --- */
html.dark .admin-content {
  background: #101014 !important;
}

/* --- 侧边栏 Logo 区域 --- */
html.dark .logo {
  border-color: #2a2a3e !important;
}

/* --- 学生侧边栏整体 --- */
html.dark .n-layout-sider {
  background: #18181c !important;
}

/* ========================================
   所有自定义卡片/区域 — 背景+边框
   ======================================== */
html.dark .card-section,
html.dark .task-list,
html.dark .quick-card,
html.dark .uncalled-section,
html.dark .rank-panel,
html.dark .task-card,
html.dark .history-card,
html.dark .welcome-banner,
html.dark .stat-card,
html.dark .phase-card,
html.dark .weak-dim-item,
html.dark .eval-item,
html.dark .formula-box,
html.dark .ai-report-content,
html.dark .insight-report,
html.dark .call-display,
html.dark .rank-item {
  background: #1a1a2e !important;
  border-color: #2a2a3e !important;
}

/* ========================================
   所有文字颜色 — 标题/正文/辅助
   ======================================== */
/* 标题文字 — 深色变亮 */
html.dark .task-title,
html.dark .task-row-title,
html.dark .quick-title,
html.dark .card-title,
html.dark .section-title,
html.dark .page-title,
html.dark .stat-value,
html.dark .flow-title,
html.dark .concept-title,
html.dark .phase-name,
html.dark .progress-name,
html.dark .submit-task,
html.dark .weak-dim-label,
html.dark .rank-name,
html.dark .uncalled-title,
html.dark .rank-title,
html.dark .logo-title,
html.dark .result-name,
html.dark .rolling-name,
html.dark .weak-dim-score {
  color: #e0e0e6 !important;
}

/* 正文文字 */
html.dark .history-content,
html.dark .progress-name,
html.dark .submit-task,
html.dark .faq-content,
html.dark .step-content,
html.dark .concept-desc {
  color: #c8c8d0 !important;
}

/* 辅助/描述文字 */
html.dark .task-desc,
html.dark .task-meta,
html.dark .quick-desc,
html.dark .stat-label,
html.dark .history-time,
html.dark .submit-time,
html.dark .task-row-steps,
html.dark .task-row-hours,
html.dark .call-stats,
html.dark .init-text,
html.dark .result-info,
html.dark .logo-subtitle,
html.dark .rolling-label {
  color: #9aa3b2 !important;
}

/* ========================================
   特定页面组件
   ======================================== */

/* --- 任务卡片 (TaskList) --- */
html.dark .task-card:hover {
  box-shadow: 0 8px 24px rgba(0,0,0,0.3) !important;
  border-color: #3a3a5e !important;
}

/* --- AI 对话历史 --- */
html.dark .history-content :deep(code) {
  background: #2a2a3e;
  color: #e0e0e6;
}
html.dark .history-content :deep(pre) {
  background: #141420;
  border: 1px solid #2a2a3e;
}

/* --- 管理仪表盘 --- */
html.dark .stat-icon {
  background: rgba(32, 128, 240, 0.15) !important;
}
html.dark .quick-card:hover {
  box-shadow: 0 8px 24px rgba(0,0,0,0.3) !important;
  border-color: #6366f1 !important;
}

/* --- 学生主页 --- */
/* 暗色下墨色块比页面底色略亮一档 + 一道细边，避免糊在一起 */
html.dark .hero-banner {
  background: #1c1d22 !important;
  border: 1px solid rgba(255, 255, 255, 0.08);
}
html.dark .task-row:hover {
  background: #22223a !important;
}
html.dark .submit-item,
html.dark .progress-item,
html.dark .task-row {
  border-color: #2a2a3e !important;
}
html.dark .progress-bar {
  background: #2a2a3e !important;
}
html.dark .progress-fill {
  background: linear-gradient(90deg, #6366f1, #8b5cf6) !important;
}
html.dark .progress-pct {
  color: #818cf8 !important;
}
html.dark .quick-blue .quick-icon { background: #1a2a4e !important; color: #60a5fa !important; }
html.dark .quick-green .quick-icon { background: #1a2e1a !important; color: #4ade80 !important; }
html.dark .quick-purple .quick-icon { background: #2a1a3e !important; color: #a78bfa !important; }
html.dark .quick-orange .quick-icon { background: #2e2a1a !important; color: #fbbf24 !important; }

/* --- 点名区域 --- */
html.dark .call-display.rolling {
  border-color: #6366f1 !important;
  background: #1a1a30 !important;
}
html.dark .call-display.called {
  border-color: #ef4444 !important;
  background: #2a1a1a !important;
}
html.dark .uncalled-tag {
  background: #22223a !important;
  color: #b8c0cf !important;
}
html.dark .rank-item.rank-top {
  background: #2a2a1a !important;
  border-color: #4a4a2a !important;
}

/* --- 评价相关补充 --- */
html.dark .concept-card.green { background: #1a2a1e !important; border-color: #2a4a2e !important; }
html.dark .concept-card.blue { background: #1a1a2e !important; border-color: #2a3a5e !important; }
html.dark .formula-example { background: #141420 !important; border-color: #2a2a3e !important; }
html.dark .flow-item { background: #1a1a2e !important; }
html.dark .weak-dim-item:hover { background: #22223a !important; }
html.dark .step-content { color: #b8c0cf !important; }
html.dark .faq-content { color: #b8c0cf !important; }
html.dark .remark-input { background: #1a1a2e !important; border-color: #2a2a3e !important; color: #e0e0e6 !important; }

/* --- 通用标题 --- */
html.dark h1, html.dark h2, html.dark h3, html.dark h4 { color: #e0e0e6 !important; }
html.dark .hero-text p { color: rgba(255,255,255,0.85) !important; }

/* --- 弹窗/模态框 --- */
html.dark .n-modal .n-card { background: #1a1a2e !important; }

/* --- 表格 --- */
html.dark .n-data-table .n-data-table-tr:hover .n-data-table-td { background: rgba(255,255,255,0.04) !important; }

/* --- AI 报告区域 --- */
html.dark .ai-report-content {
  background: #141420;
  border-color: #2a2a3e;
}
html.dark .insight-report {
  background: linear-gradient(135deg, #141420 0%, #1a1a30 100%);
  border-color: #2a2a3e;
}

/* --- 点名区域 --- */
html.dark .call-display {
  background: #1a1a2e;
  border-color: #2a2a3e;
}
html.dark .call-display.rolling {
  border-color: #6366f1;
  background: #1a1a30;
}
html.dark .call-display.called {
  border-color: #ef4444;
  background: #2a1a1a;
}
html.dark .rolling-name { color: #818cf8; }
html.dark .result-name { color: #f87171; }
html.dark .result-avatar {
  background: linear-gradient(135deg, #ef4444, #dc2626);
}
html.dark .uncalled-tag {
  background: #22223a;
  color: #b8c0cf;
}
html.dark .rank-item {
  background: #1a1a2e;
  border-color: #2a2a3e;
}
html.dark .rank-item.rank-top {
  background: #2a2a1a;
  border-color: #4a4a2a;
}

/* --- 移动端全局适配 --- */
@media (max-width: 768px) {
  .n-layout-content { padding: 12px !important; }
  .n-data-table { overflow-x: auto; }
  .n-space { flex-wrap: wrap !important; }
  .n-breadcrumb { display: none; }
  .n-modal { width: 95vw !important; max-width: 95vw !important; margin: 10px !important; }
  .n-descriptions { --n-column: 1 !important; }
  .n-descriptions-table { table-layout: fixed !important; }
  .n-descriptions .n-descriptions-table-content { max-width: 100% !important; }
  .n-form .n-form-item { flex-direction: column !important; }
  .n-form .n-form-item-label { width: 100% !important; margin-bottom: 4px; }
  .n-form .n-form-item-blank { flex: 1 !important; }
}
</style>
