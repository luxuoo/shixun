<template>
  <div class="dashboard-container">
    <h2 style="margin-bottom: 24px;">数据面板</h2>

    <!-- 统计卡片 -->
    <n-grid :cols="4" :x-gap="16" :y-gap="16" style="margin-bottom: 32px;">
      <n-gi>
        <n-card>
          <n-statistic label="学生总数" :value="stats.total_students">
            <template #prefix>
              <n-icon color="#2080f0" size="24"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg></n-icon>
            </template>
          </n-statistic>
        </n-card>
      </n-gi>
      <n-gi>
        <n-card>
          <n-statistic label="任务总数" :value="stats.total_tasks">
            <template #prefix>
              <n-icon color="#18a058" size="24"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/></svg></n-icon>
            </template>
          </n-statistic>
        </n-card>
      </n-gi>
      <n-gi>
        <n-card>
          <n-statistic label="提交总数" :value="stats.total_submissions">
            <template #prefix>
              <n-icon color="#f0a020" size="24"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg></n-icon>
            </template>
          </n-statistic>
        </n-card>
      </n-gi>
      <n-gi>
        <n-card>
          <n-statistic label="AI 调用次数" :value="stats.total_ai_calls">
            <template #prefix>
              <n-icon color="#d03050" size="24"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96z"/></svg></n-icon>
            </template>
          </n-statistic>
        </n-card>
      </n-gi>
    </n-grid>

    <!-- 图表区域 -->
    <n-grid :cols="2" :x-gap="16" :y-gap="16" style="margin-bottom: 32px;">
      <n-gi>
        <n-card title="平均分数" style="height: 300px;">
          <div style="text-align: center; padding: 40px 0;">
            <n-progress
              type="dashboard"
              :percentage="stats.average_score"
              :color="getScoreColor(stats.average_score)"
              :stroke-width="20"
              :size="180"
            >
              <div style="text-align: center;">
                <div style="font-size: 36px; font-weight: bold; color: #333;">
                  {{ stats.average_score }}
                </div>
                <div style="color: #666;">平均分</div>
              </div>
            </n-progress>
          </div>
        </n-card>
      </n-gi>
      <n-gi>
        <n-card title="任务完成率" style="height: 300px;">
          <div style="text-align: center; padding: 40px 0;">
            <n-progress
              type="dashboard"
              :percentage="completionRate"
              color="#18a058"
              :stroke-width="20"
              :size="180"
            >
              <div style="text-align: center;">
                <div style="font-size: 36px; font-weight: bold; color: #333;">
                  {{ completionRate }}%
                </div>
                <div style="color: #666;">完成率</div>
              </div>
            </n-progress>
          </div>
        </n-card>
      </n-gi>
    </n-grid>

    <!-- 最近提交 -->
    <n-card title="最近提交">
      <n-data-table
        :columns="columns"
        :data="recentSubmissions"
        :bordered="false"
        :pagination="{ pageSize: 5 }"
      />
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue'
import { NButton, NTag } from 'naive-ui'
import { adminApi } from '@/api'

const stats = ref({
  total_students: 0,
  total_tasks: 0,
  total_submissions: 0,
  total_ai_calls: 0,
  average_score: 0,
  completed_tasks: 0
})

const recentSubmissions = ref<any[]>([])

const completionRate = computed(() => {
  if (stats.value.total_submissions === 0) return 0
  return Math.round((stats.value.completed_tasks / stats.value.total_submissions) * 100)
})

const columns = [
  { title: '学生', key: 'user_id' },
  { title: '任务', key: 'task_id' },
  { title: '步骤', key: 'step_id' },
  {
    title: '状态',
    key: 'status',
    render: (row: any) => h(NTag, { type: row.status === 'reviewed' ? 'success' : 'info', size: 'small' }, { default: () => row.status === 'reviewed' ? '已审核' : '待审核' })
  },
  {
    title: '分数',
    key: 'final_score',
    render: (row: any) => row.final_score ? `${row.final_score}分` : '-'
  },
  {
    title: '时间',
    key: 'submitted_at',
    render: (row: any) => new Date(row.submitted_at).toLocaleString()
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
  } catch (error) {
    console.error('加载面板数据失败', error)
  }
}

async function loadRecentSubmissions() {
  try {
    const data = await adminApi.getSubmissions({ limit: 10 }) as any
    recentSubmissions.value = data
  } catch (error) {
    console.error('加载提交记录失败', error)
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
</style>
