<template>
  <div class="dashboard-container">
    <!-- 欢迎区 -->
    <n-card class="welcome-banner">
      <div class="welcome-content">
        <div>
          <h2 style="margin: 0; color: #1e1e2d;">{{ greeting }}，{{ userStore.user?.name || userStore.user?.username }}</h2>
          <p style="margin: 6px 0 0; color: #4a5160;">{{ userStore.isAdmin ? '系统管理员' : '教师' }} · 今天是 {{ todayStr }}</p>
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
            <AoraBot shape="chick" color="blue" face="eyes" :sizePx="30" :lineWeight="1.15" seed="stat-students" />
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
            <AoraBot shape="bulb" color="green" face="eyes" :sizePx="30" :lineWeight="1.15" seed="stat-tasks" />
          </div>
          <div>
            <div class="stat-value">{{ stats.total_tasks }}</div>
            <div class="stat-label">教学任务</div>
          </div>
        </n-space>
      </n-card>
      <n-card class="stat-card stat-orange">
        <n-space align="center" :size="16">
          <div class="stat-icon" style="background: rgba(240,160,32,0.1);">
            <AoraBot shape="drop" color="orange" face="eyes" :sizePx="30" :lineWeight="1.15" seed="stat-subs" />
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
            <AoraBot shape="ghost" color="violet" face="eyes" :sizePx="30" :lineWeight="1.15" seed="stat-ai" />
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
          <AoraBot shape="chick" color="blue" face="eyes" :sizePx="40" :lineWeight="1.15" seed="quick-students" />
          <span style="font-weight: 500;">学生管理</span>
          <span style="font-size: 12px; color: #5f6673;">管理学生账号和班级</span>
        </n-space>
      </n-card>
      <n-card hoverable class="quick-card" @click="router.push({ name: 'AdminTasks' })">
        <n-space vertical align="center" :size="8">
          <AoraBot shape="bulb" color="green" face="eyes" :sizePx="40" :lineWeight="1.15" seed="quick-tasks" />
          <span style="font-weight: 500;">任务管理</span>
          <span style="font-size: 12px; color: #5f6673;">创建和编辑教学任务</span>
        </n-space>
      </n-card>
      <n-card hoverable class="quick-card" @click="router.push({ name: 'AdminProcessEval' })">
        <n-space vertical align="center" :size="8">
          <AoraBot shape="star" color="orange" face="eyes" :sizePx="40" :lineWeight="1.15" seed="quick-eval" />
          <span style="font-weight: 500;">过程性评价</span>
          <span style="font-size: 12px; color: #5f6673;">查看班级评价看板</span>
        </n-space>
      </n-card>
      <n-card hoverable class="quick-card" @click="router.push({ name: 'AdminRollCall' })">
        <n-space vertical align="center" :size="8">
          <AoraBot shape="bell" color="pink" face="eyes" :sizePx="40" :lineWeight="1.15" seed="quick-roll" />
          <span style="font-weight: 500;">课堂点名</span>
          <span style="font-size: 12px; color: #5f6673;">随机点名学生</span>
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
        >
          <template #empty>
            <EmptyState text="最近还没有学生提交" shape="drop" state="sleeping" :sizePx="56" seed="dash-empty-subs" />
          </template>
        </n-data-table>
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
.stat-emoji { font-size: 26px; line-height: 1; }
.quick-emoji { font-size: 32px; line-height: 1; }

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
  color: #5f6673;
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
