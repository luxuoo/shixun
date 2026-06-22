<template>
  <n-layout has-sider style="height: 100vh">
    <!-- 桌面端侧边栏 -->
    <n-layout-sider
      v-if="!isMobile"
      bordered
      :width="220"
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
        <span v-if="!collapsed" class="logo-text">AI 教学系统</span>
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

    <!-- 移动端抽屉侧边栏 -->
    <n-drawer v-model:show="showDrawer" :width="260" placement="left">
      <n-drawer-content>
        <div class="logo">
          <n-icon size="32" color="#2080f0">
            <svg viewBox="0 0 24 24">
              <path fill="currentColor" d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
            </svg>
          </n-icon>
          <span class="logo-text">AI 教学系统</span>
        </div>
        <n-menu
          :options="menuOptions"
          :value="activeKey"
          @update:value="handleDrawerMenuClick"
        />
      </n-drawer-content>
    </n-drawer>

    <!-- 主内容区 -->
    <n-layout>
      <!-- 顶部导航 -->
      <n-layout-header bordered class="student-header">
        <!-- 移动端汉堡菜单 -->
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

        <n-space align="center" :size="12">
          <n-tag type="info" size="small" round>学生</n-tag>
          <n-divider vertical v-if="!isMobile" />
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
      <n-layout-content :content-style="isMobile ? 'padding: 12px;' : 'padding: 24px;'" :native-scrollbar="false">
        <router-view />
      </n-layout-content>
    </n-layout>
  </n-layout>
</template>

<script setup lang="ts">
import { ref, computed, h, onMounted, onBeforeUnmount } from 'vue'
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

const currentPageTitle = computed(() => {
  const nameMap: Record<string, string> = {
    Home: '首页',
    TaskList: '教学任务',
    TaskDetail: '任务详情',
    Submissions: '提交记录',
    Scores: '成绩总览',
    AiHistory: 'AI 对话历史'
  }
  return nameMap[route.name as string] || 'AI 教学系统'
})

const menuOptions: MenuOption[] = [
  {
    label: '首页',
    key: 'Home',
    icon: () => h(NIcon, null, { default: () => h('svg', { viewBox: '0 0 24 24' }, [h('path', { fill: 'currentColor', d: 'M10 20v-6h4v6h5v-8h3L12 3 2 12h3v8z' })]) })
  },
  {
    label: '教学任务',
    key: 'TaskList',
    icon: () => h(NIcon, null, { default: () => h('svg', { viewBox: '0 0 24 24' }, [h('path', { fill: 'currentColor', d: 'M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z' })]) })
  },
  {
    label: '提交记录',
    key: 'Submissions',
    icon: () => h(NIcon, null, { default: () => h('svg', { viewBox: '0 0 24 24' }, [h('path', { fill: 'currentColor', d: 'M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z' })]) })
  },
  {
    label: '成绩总览',
    key: 'Scores',
    icon: () => h(NIcon, null, { default: () => h('svg', { viewBox: '0 0 24 24' }, [h('path', { fill: 'currentColor', d: 'M5 13.18v4L12 21l7-3.82v-4L12 17l-7-3.82zM12 3L1 9l11 6 9-4.91V17h2V9L12 3z' })]) })
  },
  {
    label: 'AI 对话历史',
    key: 'AiHistory',
    icon: () => h(NIcon, null, { default: () => h('svg', { viewBox: '0 0 24 24' }, [h('path', { fill: 'currentColor', d: 'M20 2H4c-1.1 0-1.99.9-1.99 2L2 22l4-4h14c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zM6 9h12v2H6V9zm8 5H6v-2h8v2zm4-6H6V6h12v2z' })]) })
  }
]

const breadcrumbs = computed(() => {
  const items = [{ path: '/', title: '首页' }]
  const nameMap: Record<string, string> = {
    TaskList: '教学任务',
    TaskDetail: '任务详情',
    Submissions: '提交记录',
    Scores: '成绩总览',
    AiHistory: 'AI 对话历史'
  }
  if (route.name === 'TaskDetail') {
    items.push({ path: '/tasks', title: '教学任务' })
    items.push({ path: route.path, title: '任务详情' })
  } else if (route.name && nameMap[route.name as string]) {
    items.push({ path: route.path, title: nameMap[route.name as string] })
  }
  return items
})

const userMenuOptions = [
  { label: '管理后台', key: 'admin', show: userStore.isTeacher },
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
  } else if (key === 'admin') {
    router.push('/admin')
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

.student-header {
  height: 56px;
  padding: 0 16px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  background: #fff;
}

@media (min-width: 769px) {
  .student-header {
    height: 64px;
    padding: 0 24px;
  }
}
</style>
