<template>
  <div class="home-container">
    <!-- 欢迎区域 -->
    <n-card class="welcome-card">
      <div style="padding: 8px 0;">
        <h2>欢迎回来，{{ userStore.user?.name || userStore.user?.username }}！</h2>
        <p style="color: #666; margin-top: 8px;">继续你的编程学习之旅</p>
      </div>
    </n-card>

    <!-- 统计卡片 -->
    <n-grid :cols="4" :x-gap="16" :y-gap="16" style="margin-top: 24px;">
      <n-gi>
        <n-card>
          <n-statistic label="已完成任务" :value="stats.completedTasks">
            <template #prefix>
              <n-icon color="#18a058"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg></n-icon>
            </template>
          </n-statistic>
        </n-card>
      </n-gi>
      <n-gi>
        <n-card>
          <n-statistic label="总提交次数" :value="stats.totalSubmissions">
            <template #prefix>
              <n-icon color="#2080f0"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/></svg></n-icon>
            </template>
          </n-statistic>
        </n-card>
      </n-gi>
      <n-gi>
        <n-card>
          <n-statistic label="AI 提示使用" :value="stats.aiHintsUsed">
            <template #prefix>
              <n-icon color="#f0a020"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96z"/></svg></n-icon>
            </template>
          </n-statistic>
        </n-card>
      </n-gi>
      <n-gi>
        <n-card>
          <n-statistic label="平均分数" :value="stats.averageScore" :precision="1">
            <template #suffix>/ 100</template>
          </n-statistic>
        </n-card>
      </n-gi>
    </n-grid>

    <!-- 快捷入口 -->
    <h3 style="margin-top: 32px; margin-bottom: 16px;">快捷入口</h3>
    <n-grid :cols="3" :x-gap="16">
      <n-gi>
        <n-card hoverable @click="router.push('/tasks')">
          <n-space vertical align="center">
            <n-icon size="48" color="#2080f0">
              <svg viewBox="0 0 24 24"><path fill="currentColor" d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/></svg>
            </n-icon>
            <span style="font-size: 16px; font-weight: 500;">开始实训</span>
            <span style="color: #666; font-size: 14px;">查看可用的实训任务</span>
          </n-space>
        </n-card>
      </n-gi>
      <n-gi>
        <n-card hoverable @click="router.push('/submissions')">
          <n-space vertical align="center">
            <n-icon size="48" color="#18a058">
              <svg viewBox="0 0 24 24"><path fill="currentColor" d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg>
            </n-icon>
            <span style="font-size: 16px; font-weight: 500;">提交记录</span>
            <span style="color: #666; font-size: 14px;">查看历史提交和评分</span>
          </n-space>
        </n-card>
      </n-gi>
      <n-gi>
        <n-card hoverable>
          <n-space vertical align="center">
            <n-icon size="48" color="#f0a020">
              <svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm1 15h-2v-6h2v6zm0-8h-2V7h2v2z"/></svg>
            </n-icon>
            <span style="font-size: 16px; font-weight: 500;">学习帮助</span>
            <span style="color: #666; font-size: 14px;">获取学习指导</span>
          </n-space>
        </n-card>
      </n-gi>
    </n-grid>

    <!-- 最近任务 -->
    <h3 style="margin-top: 32px; margin-bottom: 16px;">最近任务</h3>
    <n-data-table
      :columns="taskColumns"
      :data="recentTasks"
      :bordered="false"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import { useRouter } from 'vue-router'
import { NButton, NTag } from 'naive-ui'
import { useUserStore } from '@/stores/user'
import { taskApi, submissionApi } from '@/api'

const router = useRouter()
const userStore = useUserStore()

const stats = ref({
  completedTasks: 0,
  totalSubmissions: 0,
  aiHintsUsed: 0,
  averageScore: 0
})

const recentTasks = ref<any[]>([])

const taskColumns = [
  {
    title: '任务名称',
    key: 'title',
    render: (row: any) => h('span', { style: 'font-weight: 500;' }, row.title)
  },
  {
    title: '分类',
    key: 'category',
    render: (row: any) => h(NTag, { type: 'info', size: 'small' }, { default: () => row.category || '未分类' })
  },
  {
    title: '难度',
    key: 'difficulty',
    render: (row: any) => {
      const types: Record<string, string> = { 1: 'success', 2: 'info', 3: 'warning', 4: 'error', 5: 'error' }
      return h(NTag, { type: types[row.difficulty] as any, size: 'small' }, { default: () => `${row.difficulty}星` })
    }
  },
  {
    title: '步骤数',
    key: 'total_steps'
  },
  {
    title: '操作',
    key: 'actions',
    render: (row: any) => h(NButton, { type: 'primary', size: 'small', onClick: () => router.push(`/tasks/${row.id}`) }, { default: () => '开始' })
  }
]

async function loadData() {
  try {
    // 加载任务列表
    const tasks = await taskApi.getList() as any
    recentTasks.value = tasks.slice(0, 5)

    // 加载提交统计
    const submissions = await submissionApi.getList() as any
    stats.value.totalSubmissions = submissions.length

    // 计算平均分
    const scoredSubmissions = submissions.filter((s: any) => s.ai_score)
    if (scoredSubmissions.length > 0) {
      const totalScore = scoredSubmissions.reduce((sum: number, s: any) => sum + s.ai_score, 0)
      stats.value.averageScore = totalScore / scoredSubmissions.length
    }
  } catch (error) {
    console.error('加载数据失败', error)
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.home-container {
  max-width: 1200px;
  margin: 0 auto;
}

.welcome-card {
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
}

.welcome-card :deep(.n-card__content) {
  color: white;
}

.welcome-card h2 {
  color: white;
  margin: 0;
}
</style>
