<template>
  <n-layout has-sider style="height: 100vh">
    <!-- 桌面端深色侧边栏 -->
    <n-layout-sider
      v-if="!isMobile"
      bordered
      :width="220"
      :native-scrollbar="false"
      :collapsed="collapsed"
      show-trigger
      @collapse="collapsed = true"
      @expand="collapsed = false"
      :style="siderStyle"
    >
      <!-- Logo -->
      <div class="admin-logo">
        <div class="logo-icon">
          <n-icon size="28" color="#6366f1">
            <svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
          </n-icon>
        </div>
        <div v-if="!collapsed" class="logo-text">
          <div class="logo-title">AI 实训系统</div>
          <div class="logo-subtitle">{{ userStore.isAdmin ? '管理后台' : '教师工作台' }}</div>
        </div>
      </div>

      <!-- 菜单 -->
      <div class="menu-group" v-for="group in menuGroups" :key="group.title">
        <div v-if="!collapsed" class="group-title">{{ group.title }}</div>
        <n-menu
          :collapsed="collapsed"
          :collapsed-width="64"
          :collapsed-icon-size="20"
          :options="group.items"
          :value="activeKey"
          @update:value="handleMenuClick"
          :theme-overrides="menuThemeOverrides"
        />
      </div>
    </n-layout-sider>

    <!-- 移动端抽屉侧边栏 -->
    <n-drawer v-model:show="showDrawer" :width="280" placement="left" :style="{ background: '#1e1e2d' }">
      <n-drawer-content :style="{ background: '#1e1e2d' }">
        <div class="admin-logo">
          <div class="logo-icon">
            <n-icon size="28" color="#6366f1">
              <svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/></svg>
            </n-icon>
          </div>
          <div class="logo-text">
            <div class="logo-title">AI 实训系统</div>
            <div class="logo-subtitle">{{ userStore.isAdmin ? '管理后台' : '教师工作台' }}</div>
          </div>
        </div>
        <div class="menu-group" v-for="group in menuGroups" :key="group.title">
          <div class="group-title">{{ group.title }}</div>
          <n-menu
            :options="group.items"
            :value="activeKey"
            @update:value="handleDrawerMenuClick"
            :theme-overrides="menuThemeOverrides"
          />
        </div>
      </n-drawer-content>
    </n-drawer>

    <!-- 主内容区 -->
    <n-layout>
      <!-- 顶部栏 -->
      <n-layout-header bordered class="admin-header">
        <!-- 移动端汉堡菜单 -->
        <div style="display: flex; align-items: center;">
          <n-button v-if="isMobile" text @click="showDrawer = true" style="margin-right: 8px;">
            <n-icon size="22">
              <svg viewBox="0 0 24 24"><path fill="currentColor" d="M3 18h18v-2H3v2zm0-5h18v-2H3v2zm0-7v2h18V6H3z"/></svg>
            </n-icon>
          </n-button>
          <n-breadcrumb v-if="!isMobile">
            <n-breadcrumb-item v-for="item in breadcrumbs" :key="item.path" @click="router.push(item.path)" style="cursor: pointer;">
              {{ item.title }}
            </n-breadcrumb-item>
          </n-breadcrumb>
          <span v-if="isMobile" style="font-weight: 600; font-size: 16px;">{{ currentPageTitle }}</span>
        </div>

        <n-space align="center" :size="12">
          <n-tag :type="userStore.isAdmin ? 'error' : 'warning'" size="small" round>
            {{ userStore.isAdmin ? '管理员' : '教师' }}
          </n-tag>
          <n-divider vertical v-if="!isMobile" />
          <n-dropdown :options="userMenuOptions" @select="handleUserMenu">
            <n-button text class="user-btn">
              <n-icon size="16" style="margin-right: 6px;" v-if="!isMobile"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg></n-icon>
              {{ userStore.user?.name || userStore.user?.username }}
              <n-icon size="14" style="margin-left: 4px;"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z"/></svg></n-icon>
            </n-button>
          </n-dropdown>
        </n-space>
      </n-layout-header>

      <!-- 页面内容 -->
      <n-layout-content :content-style="isMobile ? 'padding: 12px;' : 'padding: 24px;'" :native-scrollbar="false" class="admin-content">
        <router-view />
      </n-layout-content>
    </n-layout>
  </n-layout>
</template>

<script setup lang="ts">
import { ref, computed, h, onMounted, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { NIcon } from 'naive-ui'
import type { MenuOption, GlobalThemeOverrides } from 'naive-ui'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const collapsed = ref(false)
const showDrawer = ref(false)
const isMobile = ref(window.innerWidth <= 768)

function handleResize() {
  isMobile.value = window.innerWidth <= 768
}

onMounted(() => {
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
})

const activeKey = computed(() => route.name as string)

const siderStyle = {
  background: '#1e1e2d'
}

const menuThemeOverrides: GlobalThemeOverrides['Menu'] = {
  itemTextColor: 'rgba(255,255,255,0.65)',
  itemTextColorHover: '#fff',
  itemTextColorActive: '#fff',
  itemIconColor: 'rgba(255,255,255,0.45)',
  itemIconColorHover: '#fff',
  itemIconColorActive: '#fff',
  itemColorActive: 'rgba(99,102,241,0.2)',
  itemColorHover: 'rgba(255,255,255,0.06)',
  itemTextColorChildActive: '#6366f1',
  itemIconColorChildActive: '#6366f1',
  arrowColor: 'rgba(255,255,255,0.45)',
  arrowColorHover: '#fff',
  arrowColorActive: '#fff'
}

function icon(path: string) {
  return () => h(NIcon, null, { default: () => h('svg', { viewBox: '0 0 24 24' }, [h('path', { fill: 'currentColor', d: path })]) })
}

const menuGroups = computed(() => {
  const groups = [
    {
      title: '概览',
      items: [
        { label: '数据面板', key: 'AdminDashboard', icon: icon('M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z') }
      ]
    },
    {
      title: '教学管理',
      items: [
        { label: '学生管理', key: 'AdminStudents', icon: icon('M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z') },
        { label: '班级管理', key: 'AdminClasses', icon: icon('M12 3L1 9l4 2.18v6L12 21l7-3.82v-6l2-1.09V17h2V9L12 3zm6.82 6L12 12.72 5.18 9 12 5.28 18.82 9zM17 15.99l-5 2.73-5-2.73v-3.72L12 15l5-2.73v3.72z') },
        { label: '任务管理', key: 'AdminTasks', icon: icon('M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z') },
        { label: '提交记录', key: 'AdminSubmissions', icon: icon('M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z') },
        { label: '成绩管理', key: 'AdminGrades', icon: icon('M5 13.18v4L12 21l7-3.82v-4L12 17l-7-3.82zM12 3L1 9l11 6 9-4.91V17h2V9L12 3z') },
        { label: '成绩设置', key: 'AdminGradeSettings', icon: icon('M19.14 12.94c.04-.3.06-.61.06-.94 0-.32-.02-.64-.07-.94l2.03-1.58a.49.49 0 00.12-.61l-1.92-3.32a.49.49 0 00-.59-.22l-2.39.96c-.5-.38-1.03-.7-1.62-.94l-.36-2.54a.48.48 0 00-.48-.41h-3.84a.48.48 0 00-.48.41l-.36 2.54c-.59.24-1.13.57-1.62.94l-2.39-.96a.49.49 0 00-.59.22L2.74 8.87a.48.48 0 00.12.61l2.03 1.58c-.05.3-.07.62-.07.94s.02.64.07.94l-2.03 1.58a.49.49 0 00-.12.61l1.92 3.32c.12.22.37.29.59.22l2.39-.96c.5.38 1.03.7 1.62.94l.36 2.54c.05.24.26.41.48.41h3.84c.24 0 .44-.17.48-.41l.36-2.54c.59-.24 1.13-.56 1.62-.94l2.39.96c.22.08.47 0 .59-.22l1.92-3.32c.12-.22.07-.47-.12-.61l-2.01-1.58zM12 15.6A3.6 3.6 0 1115.6 12 3.6 3.6 0 0112 15.6z') },
        { label: '课堂点名', key: 'AdminRollCall', icon: icon('M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z') },
        { label: '加减分', key: 'AdminAdjustScore', icon: icon('M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm5 10h-4v4h-2v-4H7v-2h4V6h2v4h4v2z') }
      ]
    },
    {
      title: '数据分析',
      items: [
        { label: 'AI 统计', key: 'AdminAiStats', icon: icon('M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96z') },
        { label: 'AI 日志', key: 'AdminAiLogs', icon: icon('M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z') }
      ]
    }
  ]

  if (userStore.isAdmin) {
    groups.push({
      title: '系统设置',
      items: [
        { label: '用户管理', key: 'AdminUsers', icon: icon('M15 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm-9-2V7H4v3H1v2h3v3h2v-3h3v-2H6zm9 4c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z') },
        { label: '系统统计', key: 'AdminSystemStats', icon: icon('M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z') }
      ]
    })
  }

  return groups
})

const currentPageTitle = computed(() => {
  const nameMap: Record<string, string> = {
    AdminDashboard: '数据面板',
    AdminStudents: '学生管理',
    AdminClasses: '班级管理',
    AdminTasks: '任务管理',
    AdminSubmissions: '提交记录',
    AdminAiStats: 'AI 统计',
    AdminAiLogs: 'AI 日志',
    AdminUsers: '用户管理',
    AdminSystemStats: '系统统计',
    AdminRollCall: '课堂点名',
    AdminGrades: '成绩管理',
    AdminGradeSettings: '成绩设置',
    AdminAdjustScore: '加减分'
  }
  return nameMap[route.name as string] || '管理后台'
})

const breadcrumbs = computed(() => {
  const items = [{ path: '/admin', title: '管理后台' }]
  const nameMap: Record<string, string> = {
    AdminDashboard: '数据面板',
    AdminStudents: '学生管理',
    AdminClasses: '班级管理',
    AdminTasks: '任务管理',
    AdminSubmissions: '提交记录',
    AdminAiStats: 'AI 统计',
    AdminAiLogs: 'AI 日志',
    AdminUsers: '用户管理',
    AdminSystemStats: '系统统计',
    AdminRollCall: '课堂点名',
    AdminGrades: '成绩管理',
    AdminGradeSettings: '成绩设置',
    AdminAdjustScore: '加减分'
  }
  if (route.name && nameMap[route.name as string]) {
    items.push({ path: route.path, title: nameMap[route.name as string] })
  }
  return items
})

const userMenuOptions = [
  { label: '返回学生端', key: 'home', icon: () => h(NIcon, null, { default: () => h('svg', { viewBox: '0 0 24 24' }, [h('path', { fill: 'currentColor', d: 'M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z' })]) }) },
  { type: 'divider', key: 'd1' },
  { label: '退出登录', key: 'logout' }
]

function handleMenuClick(key: string) {
  router.push({ name: key })
}

function handleDrawerMenuClick(key: string) {
  showDrawer.value = false
  router.push({ name: key })
}

function handleUserMenu(key: string) {
  if (key === 'logout') {
    userStore.logout()
    router.push('/login')
  } else if (key === 'home') {
    router.push('/')
  }
}
</script>

<style scoped>
.admin-logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 10px;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  padding: 0 16px;
}

.logo-icon {
  width: 36px;
  height: 36px;
  border-radius: 8px;
  background: rgba(99, 102, 241, 0.15);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.logo-text {
  overflow: hidden;
}

.logo-title {
  font-size: 15px;
  font-weight: 700;
  color: #fff;
  line-height: 1.3;
  white-space: nowrap;
}

.logo-subtitle {
  font-size: 11px;
  color: rgba(255, 255, 255, 0.45);
  white-space: nowrap;
}

.menu-group {
  padding: 8px 0;
}

.group-title {
  padding: 8px 20px 4px;
  font-size: 11px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.3);
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.admin-header {
  height: 56px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
}

@media (min-width: 769px) {
  .admin-header {
    padding: 0 24px;
  }
}

.user-btn {
  display: flex;
  align-items: center;
  font-size: 14px;
}

.admin-content {
  background: #f5f5f9;
}
</style>
