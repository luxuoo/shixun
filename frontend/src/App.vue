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
  color: #888 !important;
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
html.dark .hero-banner {
  background: linear-gradient(135deg, #1e1b4b 0%, #312e81 50%, #4c1d95 100%) !important;
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
  color: #ccc !important;
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
html.dark .step-content { color: #bbb !important; }
html.dark .faq-content { color: #bbb !important; }
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
  color: #ccc;
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
