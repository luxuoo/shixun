<template>
  <StarBackground />
  <n-layout has-sider style="height: 100vh; position: relative; z-index: 1;">
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
          <AoraBot shape="bot" color="cyan" face="eyes" :sizePx="26" :lineWeight="1.15" seed="logo-admin" />
        </div>
        <div v-if="!collapsed" class="logo-text">
          <div class="logo-title">AI 教学系统</div>
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
            <AoraBot shape="bot" color="black" face="eyes" :sizePx="26" seed="logo-admin" />
          </div>
          <div class="logo-text">
            <div class="logo-title">AI 教学系统</div>
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
          <n-button quaternary circle size="small" @click="themeStore.toggle()">
            <template #icon>
              <n-icon v-if="themeStore.isDark" size="18"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 7c-2.76 0-5 2.24-5 5s2.24 5 5 5 5-2.24 5-5-2.24-5-5-5zM2 13h2c.55 0 1-.45 1-1s-.45-1-1-1H2c-.55 0-1 .45-1 1s.45 1 1 1zm18 0h2c.55 0 1-.45 1-1s-.45-1-1-1h-2c-.55 0-1 .45-1 1s.45 1 1 1zM11 2v2c0 .55.45 1 1 1s1-.45 1-1V2c0-.55-.45-1-1-1s-1 .45-1 1zm0 18v2c0 .55.45 1 1 1s1-.45 1-1v-2c0-.55-.45-1-1-1s-1 .45-1 1zM5.99 4.58a.996.996 0 00-1.41 0 .996.996 0 000 1.41l1.06 1.06c.39.39 1.03.39 1.41 0s.39-1.03 0-1.41L5.99 4.58zm12.37 12.37a.996.996 0 00-1.41 0 .996.996 0 000 1.41l1.06 1.06c.39.39 1.03.39 1.41 0a.996.996 0 000-1.41l-1.06-1.06zm1.06-10.96a.996.996 0 000-1.41.996.996 0 00-1.41 0l-1.06 1.06c-.39.39-.39 1.03 0 1.41s1.03.39 1.41 0l1.06-1.06zM7.05 18.36a.996.996 0 000-1.41.996.996 0 00-1.41 0l-1.06 1.06c-.39.39-.39 1.03 0 1.41s1.03.39 1.41 0l1.06-1.06z"/></svg></n-icon>
              <n-icon v-else size="18"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 3c-4.97 0-9 4.03-9 9s4.03 9 9 9 9-4.03 9-9c0-.46-.04-.92-.1-1.36a5.389 5.389 0 01-4.4 2.26 5.403 5.403 0 01-3.14-9.8c-.44-.06-.9-.1-1.36-.1z"/></svg></n-icon>
            </template>
          </n-button>
          <n-tag :type="userStore.isAdmin ? 'error' : 'warning'" size="small" round>
            {{ userStore.isAdmin ? '管理员' : '教师' }}
          </n-tag>
          <n-divider vertical v-if="!isMobile" />
          <n-dropdown :options="userMenuOptions" @select="handleUserMenu">
            <n-button text class="user-btn">
              <BotAvatar :name="userStore.user?.username || 'guest'" :sizePx="24" />
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

  <ChangePassword v-model:show="showPwd" />
</template>

<script setup lang="ts">
import { ref, computed, h, onMounted, onBeforeUnmount } from 'vue'
import { useRouter, useRoute } from 'vue-router'
import type { MenuOption, GlobalThemeOverrides } from 'naive-ui'
import { useUserStore } from '@/stores/user'
import { useThemeStore } from '@/stores/theme'
import AoraBot from '@/components/AoraBot'
import StarBackground from '@/components/StarBackground.vue'
import ChangePassword from '@/components/ChangePassword.vue'

const router = useRouter()
const route = useRoute()
const userStore = useUserStore()
const themeStore = useThemeStore()
const collapsed = ref(false)
const showDrawer = ref(false)
const showPwd = ref(false)
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
  itemTextColor: 'rgba(255,255,255,0.82)',
  itemTextColorHover: '#fff',
  itemTextColorActive: '#fff',
  itemIconColor: 'rgba(255,255,255,0.7)',
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

/** 菜单图标 = 小角色：深色侧边栏必须用亮色身体，墨黑身体在深底上等于隐形 */
function botIcon(shape: string, color = 'cyan') {
  return () => h(AoraBot, {
    shape,
    color,
    face: 'eyes',
    sizePx: 22,
    lineWeight: 1.15,
    seed: `menu-${shape}`
  })
}

const menuGroups = computed(() => {
  const groups = [
    {
      title: '概览',
      items: [
        { label: '数据面板', key: 'AdminDashboard', icon: botIcon('planet', 'blue') }
      ]
    },
    {
      title: '教学管理',
      items: [
        { label: '学生管理', key: 'AdminStudents', icon: botIcon('chick', 'yellow') },
        { label: '班级管理', key: 'AdminClasses', icon: botIcon('onigiri', 'orange') },
        { label: '任务管理', key: 'AdminTasks', icon: botIcon('bulb', 'green') },
        { label: '提交记录', key: 'AdminSubmissions', icon: botIcon('drop', 'cyan') },
        { label: '课堂点名', key: 'AdminRollCall', icon: botIcon('bell', 'pink') },
        { label: '成绩管理', key: 'AdminGradeManage', icon: botIcon('star', 'orange') },
        { label: '过程性评价', key: 'AdminProcessEval', icon: botIcon('gem', 'violet') },
        { label: '评分明录', key: 'AdminScoreEntry', icon: botIcon('flame', 'yellow') },
        { label: '评价配置', key: 'AdminProcessEvalConfig', icon: botIcon('bot', 'cyan') }
      ]
    },
    {
      title: '数据分析',
      items: [
        { label: 'AI 统计', key: 'AdminAiStats', icon: botIcon('ghost', 'violet') },
        { label: 'AI 日志', key: 'AdminAiLogs', icon: botIcon('chat', 'green') }
      ]
    }
  ]

  if (userStore.isAdmin) {
    groups.push({
      title: '系统设置',
      items: [
        { label: '用户管理', key: 'AdminUsers', icon: botIcon('cat', 'orange') },
        { label: '系统统计', key: 'AdminSystemStats', icon: botIcon('planet', 'blue') }
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
    AdminGradeManage: '成绩管理',
    AdminProcessEval: '过程性评价',
    AdminProcessEvalConfig: '评价配置',
    AdminScoreEntry: '评分明录'
  }
  const name = route.name as string
  const title = nameMap[name]
  return title || '管理后台'
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
    AdminGradeManage: '成绩管理',
    AdminProcessEval: '过程性评价',
    AdminProcessEvalConfig: '评价配置',
    AdminScoreEntry: '评分明录'
  }
  const name = route.name as string
  if (name && nameMap[name]) {
    items.push({ path: route.path, title: nameMap[name] })
  }
  return items
})

const userMenuOptions = [
  { label: '返回学生端', key: 'home' },
  { type: 'divider', key: 'd1' },
  { label: '修改密码', key: 'password' },
  { type: 'divider', key: 'd2' },
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
  if (key === 'password') {
    showPwd.value = true
  } else if (key === 'logout') {
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

.logo-emoji {
  font-size: 19px;
  line-height: 1;
}

.menu-emoji {
  font-size: 16px;
  line-height: 1;
  display: inline-flex;
  width: 20px;
  justify-content: center;
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
  color: rgba(255, 255, 255, 0.62);
  white-space: nowrap;
}

.menu-group {
  padding: 8px 0;
}

.group-title {
  padding: 8px 20px 4px;
  font-size: 11px;
  font-weight: 600;
  color: rgba(255, 255, 255, 0.48);
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
