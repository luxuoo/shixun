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

/* 亮色：正文/次要文字整体加深，边框加实，卡片与页面分层更清楚；
   语义色加深到白字/浅底上可达 4.5:1 */
const lightOverrides: GlobalThemeOverrides = {
  common: {
    primaryColor: '#1a66d6',
    primaryColorHover: '#2f74e0',
    primaryColorPressed: '#155abc',
    borderRadius: '8px',
    textColorBase: '#111827',
    textColor1: '#111827',
    textColor2: '#374151',
    textColor3: '#6b7280',
    borderColor: '#dcdfe6',
    dividerColor: '#e5e7eb',
    successColor: '#0b7341',
    successColorHover: '#0e854c',
    successColorPressed: '#095f36',
    infoColor: '#1667d9',
    infoColorHover: '#2f7de0',
    infoColorPressed: '#1258bb',
    errorColor: '#c22546',
    errorColorHover: '#d33a5b',
    errorColorPressed: '#a81f3c',
    warningColor: '#f0a020',
    warningColorHover: '#f5b040',
    warningColorPressed: '#d98f15',
    placeholderColor: '#6b7280'
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
    border: '1px solid transparent',
    textColorWarning: '#8a5800'
  },
  Button: {
    textColorWarning: '#453006',
    textColorHoverWarning: '#453006',
    textColorPressedWarning: '#453006',
    textColorFocusWarning: '#453006',
    textColorDisabledWarning: '#453006',
    textColorTextWarning: '#b45309',
    textColorTextHoverWarning: '#92400e',
    textColorTextPressedWarning: '#92400e',
    textColorTextFocusWarning: '#92400e'
  },
  Empty: {
    textColor: '#5f6673'
  },
  Steps: {
    headerTextColorWait: '#5f6673',
    indicatorTextColorWait: '#5f6673',
    descriptionTextColorWait: '#5f6673'
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
    dividerColor: '#2a2d3d',
    successColor: '#36ad6a',
    successColorHover: '#4cc07d',
    successColorPressed: '#2c9159',
    infoColor: '#4d9df5',
    infoColorHover: '#6baff7',
    infoColorPressed: '#3a86d8',
    errorColor: '#e88080',
    errorColorHover: '#ef9a9a',
    errorColorPressed: '#d06a6a',
    warningColor: '#f2c97d',
    warningColorHover: '#f6d695',
    warningColorPressed: '#d9b26a',
    placeholderColor: 'rgba(255, 255, 255, 0.52)'
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
  },
  Button: {
    textColorWarning: '#3d2e0a',
    textColorHoverWarning: '#3d2e0a',
    textColorPressedWarning: '#3d2e0a',
    textColorFocusWarning: '#3d2e0a',
    textColorDisabledWarning: '#3d2e0a'
  },
  Empty: {
    textColor: '#9aa1b0'
  },
  Steps: {
    headerTextColorWait: '#9aa3b2',
    indicatorTextColorWait: '#9aa3b2',
    descriptionTextColorWait: '#9aa3b2'
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
   暗黑模式：页面颜色统一由 styles/theme.css 的变量承担，
   这里只补 naive-ui 内部组件与少数刻意深色块。
   ========================================== */

/* 学生侧边栏（naive 布局组件） */
html.dark .n-layout-sider {
  background: #18181c !important;
}

/* 学生主页墨色横幅：暗色下加一道细边，避免与页面底色糊在一起 */
html.dark .hero-banner {
  border: 1px solid rgba(255, 255, 255, 0.08);
}

/* 弹窗卡片与页面卡片同色 */
html.dark .n-modal .n-card {
  background: var(--c-card) !important;
}

/* 表格行 hover */
html.dark .n-data-table .n-data-table-tr:hover .n-data-table-td {
  background: rgba(255, 255, 255, 0.04) !important;
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
