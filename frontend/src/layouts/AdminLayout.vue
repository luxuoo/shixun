<template>
  <n-layout has-sider style="height: 100vh">
    <!-- 侧边栏 -->
    <n-layout-sider
      bordered
      :width="240"
      :native-scrollbar="false"
      :collapsed="collapsed"
      show-trigger
      @collapse="collapsed = true"
      @expand="collapsed = false"
    >
      <div class="logo">
        <n-icon size="32" color="#2080f0">
          <svg viewBox="0 0 24 24">
            <path fill="currentColor" d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
          </svg>
        </n-icon>
        <span v-if="!collapsed" class="logo-text">管理后台</span>
      </div>

      <n-menu
        :collapsed="collapsed"
        :collapsed-width="64"
        :collapsed-icon-size="22"
        :options="menuOptions"
        :value="activeKey"
        @update:value="handleMenuClick"
      />
    </n-layout-sider>

    <!-- 主内容区 -->
    <n-layout>
      <!-- 顶部导航 -->
      <n-layout-header bordered style="height: 64px; padding: 0 24px; display: flex; align-items: center; justify-content: space-between;">
        <n-breadcrumb>
          <n-breadcrumb-item v-for="item in breadcrumbs" :key="item.path">
            {{ item.title }}
          </n-breadcrumb-item>
        </n-breadcrumb>

        <n-space align="center">
          <n-tag :type="userStore.isAdmin ? 'error' : 'warning'" size="small">
            {{ userStore.isAdmin ? '管理员' : '教师' }}
          </n-tag>
          <n-dropdown :options="userMenuOptions" @select="handleUserMenu">
            <n-button text>
              {{ userStore.user?.name || userStore.user?.username }}
              <template #icon>
                <n-icon><ChevronDown /></n-icon>
              </template>
            </n-button>
          </n-dropdown>
        </n-space>
      </n-layout-header>

      <!-- 页面内容 -->
      <n-layout-content content-style="padding: 24px;" :native-scrollbar="false">
        <router-view />
      </n-layout-content>
    </n-layout>
  </n-layout>
</template>

<script setup lang="ts">
import { ref, computed, h } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import { NIcon } from 'naive-ui'
import type { MenuOption } from 'naive-ui'
import { useUserStore } from '@/stores/user'

const ChevronDown = {
  render() {
    return h('svg', { viewBox: '0 0 24 24' }, [
      h('path', { fill: 'currentColor', d: 'M7.41 8.59L12 13.17l4.59-4.58L18 10l-6 6-6-6 1.41-1.41z' })
    ])
  }
}

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const collapsed = ref(false)

const activeKey = computed(() => route.name as string)

const menuOptions = computed<MenuOption[]>(() => {
  const baseItems: MenuOption[] = [
    {
      label: '数据面板',
      key: 'AdminDashboard',
      icon: () => h(NIcon, null, { default: () => h('svg', { viewBox: '0 0 24 24' }, [h('path', { fill: 'currentColor', d: 'M3 13h8V3H3v10zm0 8h8v-6H3v6zm10 0h8V11h-8v10zm0-18v6h8V3h-8z' })]) })
    },
    {
      label: '学生管理',
      key: 'AdminStudents',
      icon: () => h(NIcon, null, { default: () => h('svg', { viewBox: '0 0 24 24' }, [h('path', { fill: 'currentColor', d: 'M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5zm8 0c-.29 0-.62.02-.97.05 1.16.84 1.97 1.97 1.97 3.45V19h6v-2.5c0-2.33-4.67-3.5-7-3.5z' })]) })
    },
    {
      label: '班级管理',
      key: 'AdminClasses',
      icon: () => h(NIcon, null, { default: () => h('svg', { viewBox: '0 0 24 24' }, [h('path', { fill: 'currentColor', d: 'M12 3L1 9l4 2.18v6L12 21l7-3.82v-6l2-1.09V17h2V9L12 3zm6.82 6L12 12.72 5.18 9 12 5.28 18.82 9zM17 15.99l-5 2.73-5-2.73v-3.72L12 15l5-2.73v3.72z' })]) })
    },
    {
      label: '任务管理',
      key: 'AdminTasks',
      icon: () => h(NIcon, null, { default: () => h('svg', { viewBox: '0 0 24 24' }, [h('path', { fill: 'currentColor', d: 'M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z' })]) })
    },
    {
      label: '提交记录',
      key: 'AdminSubmissions',
      icon: () => h(NIcon, null, { default: () => h('svg', { viewBox: '0 0 24 24' }, [h('path', { fill: 'currentColor', d: 'M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z' })]) })
    },
    {
      label: 'AI 统计',
      key: 'AdminAiStats',
      icon: () => h(NIcon, null, { default: () => h('svg', { viewBox: '0 0 24 24' }, [h('path', { fill: 'currentColor', d: 'M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96z' })]) })
    },
    {
      label: 'AI 日志',
      key: 'AdminAiLogs',
      icon: () => h(NIcon, null, { default: () => h('svg', { viewBox: '0 0 24 24' }, [h('path', { fill: 'currentColor', d: 'M20 2H4c-1.1 0-2 .9-2 2v18l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm0 14H6l-2 2V4h16v12z' })]) })
    }
  ]

  // 管理员专属菜单
  if (userStore.isAdmin) {
    baseItems.push(
      {
        label: '用户管理',
        key: 'AdminUsers',
        icon: () => h(NIcon, null, { default: () => h('svg', { viewBox: '0 0 24 24' }, [h('path', { fill: 'currentColor', d: 'M15 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm-9-2V7H4v3H1v2h3v3h2v-3h3v-2H6zm9 4c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z' })]) })
      },
      {
        label: '系统统计',
        key: 'AdminSystemStats',
        icon: () => h(NIcon, null, { default: () => h('svg', { viewBox: '0 0 24 24' }, [h('path', { fill: 'currentColor', d: 'M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zM9 17H7v-7h2v7zm4 0h-2V7h2v10zm4 0h-2v-4h2v4z' })]) })
      }
    )
  }

  return baseItems
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
    AdminSystemStats: '系统统计'
  }
  if (route.name && nameMap[route.name as string]) {
    items.push({ path: route.path, title: nameMap[route.name as string] })
  }
  return items
})

const userMenuOptions = [
  { label: '返回前台', key: 'home' },
  { type: 'divider', key: 'd1' },
  { label: '退出登录', key: 'logout' }
]

function handleMenuClick(key: string) {
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
.logo {
  height: 64px;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  border-bottom: 1px solid var(--n-border-color);
}

.logo-text {
  font-size: 18px;
  font-weight: 600;
  color: var(--n-text-color);
}
</style>
