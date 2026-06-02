<template>
  <div class="dashboard-container">
    <!-- 欢迎区 -->
    <n-card class="welcome-banner">
      <div class="welcome-content">
        <div>
          <h2 style="margin: 0; color: #1e1e2d;">{{ greeting }}，{{ userStore.user?.name || userStore.user?.username }}</h2>
          <p style="margin: 6px 0 0; color: #666;">{{ userStore.isAdmin ? '系统管理员' : '教师' }} · 今天是 {{ todayStr }}</p>
        </div>
        <n-tag :type="userStore.isAdmin ? 'error' : 'warning'" size="large" round>
          {{ userStore.isAdmin ? '管理员' : '教师' }}
        </n-tag>
      </div>
    </n-card>

    <!-- 统计卡片 -->
    <div class="stat-grid">
      <n-card class="stat-card stat-blue">
        <n-space align="center" :size="16">
          <div class="stat-icon">
            <n-icon size="28" color="#2080f0"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg></n-icon>
          </div>
          <div>
            <div class="stat-value">{{ stats.total_students }}</div>
            <div class="stat-label">学生总数</div>
          </div>
        </n-space>
      </n-card>
      <n-card class="stat-card stat-green">
        <n-space align="center" :size="16">
          <div class="stat-icon" style="background: rgba(24,160,88,0.1);">
            <n-icon size="28" color="#18a058"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/></svg></n-icon>
          </div>
          <div>
            <div class="stat-value">{{ stats.total_tasks }}</div>
            <div class="stat-label">实训任务</div>
          </div>
        </n-space>
      </n-card>
      <n-card class="stat-card stat-orange">
        <n-space align="center" :size="16">
          <div class="stat-icon" style="background: rgba(240,160,32,0.1);">
            <n-icon size="28" color="#f0a020"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg></n-icon>
          </div>
          <div>
            <div class="stat-value">{{ stats.total_submissions }}</div>
            <div class="stat-label">提交总数</div>
          </div>
        </n-space>
      </n-card>
      <n-card class="stat-card stat-red">
        <n-space align="center" :size="16">
          <div class="stat-icon" style="background: rgba(208,48,80,0.1);">
            <n-icon size="28" color="#d03050"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96z"/></svg></n-icon>
          </div>
          <div>
            <div class="stat-value">{{ stats.total_ai_calls }}</div>
            <div class="stat-label">AI 调用</div>
          </div>
        </n-space>
      </n-card>
    </div>

    <!-- 快捷操作 -->
    <h3 style="margin: 28px 0 16px; font-size: 16px;">快捷操作</h3>
    <div class="quick-grid">
      <n-card hoverable class="quick-card" @click="router.push({ name: 'AdminStudents' })">
        <n-space vertical align="center" :size="8">
          <n-icon size="36" color="#2080f0"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg></n-icon>
          <span style="font-weight: 500;">学生管理</span>
          <span style="font-size: 12px; color: #999;">管理学生账号和班级</span>
        </n-space>
      </n-card>
      <n-card hoverable class="quick-card" @click="router.push({ name: 'AdminTasks' })">
        <n-space vertical align="center" :size="8">
          <n-icon size="36" color="#18a058"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/></svg></n-icon>
          <span style="font-weight: 500;">任务管理</span>
          <span style="font-size: 12px; color: #999;">创建和编辑实训任务</span>
        </n-space>
      </n-card>
      <n-card hoverable class="quick-card" @click="router.push({ name: 'AdminGrades' })">
        <n-space vertical align="center" :size="8">
          <n-icon size="36" color="#f0a020"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M5 13.18v4L12 21l7-3.82v-4L12 17l-7-3.82zM12 3L1 9l11 6 9-4.91V17h2V9L12 3z"/></svg></n-icon>
          <span style="font-weight: 500;">成绩管理</span>
          <span style="font-size: 12px; color: #999;">查看和管理学生成绩</span>
        </n-space>
      </n-card>
      <n-card hoverable class="quick-card" @click="router.push({ name: 'AdminRollCall' })">
        <n-space vertical align="center" :size="8">
          <n-icon size="36" color="#d03050"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg></n-icon>
          <span style="font-weight: 500;">课堂点名</span>
          <span style="font-size: 12px; color: #999;">随机点名学生</span>
        </n-space>
      </n-card>
    </div>

    <!-- 图表 + 最近提交 -->
    <div class="bottom-grid">
      <n-card title="教学概览">
        <n-space vertical :size="16">
          <n-space justify="space-between" align="center">
            <span>平均分数</span>
            <n-progress type="line" :percentage="stats.average_score" :color="getScoreColor(stats.average_score)" style="width: 200px;" />
          </n-space>
          <n-space justify="space-between" align="center">
            <span>任务完成率</span>
            <n-progress type="line" :percentage="completionRate" color="#18a058" style="width: 200px;" />
          </n-space>
          <n-space justify="space-between" align="center">
            <span>学生活跃度</span>
            <n-progress type="line" :percentage="activeRate" color="#2080f0" style="width: 200px;" />
          </n-space>
        </n-space>
      </n-card>
      <n-card title="最近提交">
        <n-data-table
          :columns="columns"
          :data="recentSubmissions"
          :bordered="false"
          :pagination="{ pageSize: 5 }"
          size="small"
        />
      </n-card>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue'
import { useRouter } from 'vue-router'
import { NTag, useMessage } from 'naive-ui'
import { adminApi } from '@/api'
import { useUserStore } from '@/stores/user'

const router = useRouter()
const userStore = useUserStore()
const message = useMessage()

const stats = ref({
  total_students: 0,
  total_tasks: 0,
  total_submissions: 0,
  total_ai_calls: 0,
  average_score: 0,
  completed_tasks: 0
})

const recentSubmissions = ref<any[]>([])

const todayStr = new Date().toLocaleDateString('zh-CN', { year: 'numeric', month: 'long', day: 'numeric', weekday: 'long' })

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 12) return '早上好'
  if (h < 18) return '下午好'
  return '晚上好'
})

const completionRate = computed(() => {
  if (stats.value.total_submissions === 0) return 0
  return Math.round((stats.value.completed_tasks / stats.value.total_submissions) * 100)
})

const activeRate = computed(() => {
  if (stats.value.total_students === 0) return 0
  return Math.min(100, Math.round((stats.value.total_submissions / Math.max(stats.value.total_students, 1)) * 10))
})

const columns = [
  { title: '学生', key: 'user_id', width: 80 },
  { title: '任务', key: 'task_id', width: 80 },
  {
    title: '状态',
    key: 'status',
    width: 80,
    render: (row: any) => h(NTag, { type: row.status === 'reviewed' ? 'success' : 'info', size: 'small' }, { default: () => row.status === 'reviewed' ? '已审核' : '待审核' })
  },
  {
    title: '分数',
    key: 'final_score',
    width: 70,
    render: (row: any) => row.final_score ? `${row.final_score}` : '-'
  },
  {
    title: '时间',
    key: 'submitted_at',
    render: (row: any) => new Date(row.submitted_at).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
  }
]

function getScoreColor(score: number) {
  if (score >= 90) return '#18a058'
  if (score >= 80) return '#2080f0'
  if (score >= 60) return '#f0a020'
  return '#d03050'
}

async function loadDashboard() {
  try {
    const data = await adminApi.getDashboard() as any
    stats.value = data
  } catch (error: any) {
    message.error(error?.detail || '加载面板数据失败')
  }
}

async function loadRecentSubmissions() {
  try {
    const data = await adminApi.getSubmissions({ limit: 10 }) as any
    recentSubmissions.value = data
  } catch (error: any) {
    message.error(error?.detail || '加载提交记录失败')
  }
}

onMounted(() => {
  loadDashboard()
  loadRecentSubmissions()
})
</script>

<style scoped>
.dashboard-container {
  max-width: 1400px;
  margin: 0 auto;
}

.welcome-banner {
  background: #fff;
  border: 1px solid #e8e8ec;
}

.welcome-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
}

.stat-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-top: 20px;
}

.stat-card {
  border: 1px solid #e8e8ec;
}

.stat-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: rgba(32, 128, 240, 0.1);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.stat-value {
  font-size: 24px;
  font-weight: 700;
  color: #1e1e2d;
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: #999;
  margin-top: 2px;
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

.quick-card {
  cursor: pointer;
  transition: all 0.2s;
  border: 1px solid #e8e8ec;
}

.quick-card:hover {
  border-color: #6366f1;
  box-shadow: 0 4px 12px rgba(99, 102, 241, 0.1);
  transform: translateY(-2px);
}

.bottom-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-top: 24px;
}

/* 响应式 */
@media (max-width: 768px) {
  .stat-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .quick-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .bottom-grid {
    grid-template-columns: 1fr;
  }

  .stat-value {
    font-size: 20px;
  }

  .stat-icon {
    width: 40px;
    height: 40px;
  }
}

@media (min-width: 769px) and (max-width: 1024px) {
  .stat-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .quick-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
