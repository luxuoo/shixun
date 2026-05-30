<template>
  <div class="scores-container">
    <h2 class="page-title">我的成绩单</h2>

    <!-- 统计卡片 -->
    <n-grid :cols="4" :x-gap="16" :y-gap="16" style="margin-bottom: 24px;">
      <n-gi>
        <div class="stat-card">
          <div class="stat-num" style="color: #18a058;">{{ completedTasks }}</div>
          <div class="stat-label">已完成</div>
        </div>
      </n-gi>
      <n-gi>
        <div class="stat-card">
          <div class="stat-num" style="color: #2080f0;">{{ inProgressTasks }}</div>
          <div class="stat-label">进行中</div>
        </div>
      </n-gi>
      <n-gi>
        <div class="stat-card">
          <div class="stat-num" style="color: #f0a020;">{{ averageScore.toFixed(1) }}</div>
          <div class="stat-label">平均分</div>
        </div>
      </n-gi>
      <n-gi>
        <div class="stat-card">
          <div class="stat-num" style="color: #6366f1;">{{ totalSubmissions }}</div>
          <div class="stat-label">总提交</div>
        </div>
      </n-gi>
    </n-grid>

    <!-- 成绩表格 -->
    <n-card>
      <n-data-table :columns="columns" :data="scores" :loading="loading" :bordered="false" :pagination="pagination" />
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, reactive, h } from 'vue'
import { NTag, NProgress } from 'naive-ui'
import { submissionApi } from '@/api'

const loading = ref(false)
const scores = ref<any[]>([])

const pagination = reactive({
  page: 1, pageSize: 10, showSizePicker: true, pageSizes: [10, 20],
  onChange: (p: number) => { pagination.page = p },
  onUpdatePageSize: (s: number) => { pagination.pageSize = s; pagination.page = 1 }
})

const completedTasks = computed(() => scores.value.filter(s => s.status === 'completed' || s.status === 'reviewed').length)
const inProgressTasks = computed(() => scores.value.filter(s => s.status === 'in_progress').length)
const averageScore = computed(() => {
  const scored = scores.value.filter(s => s.final_score != null)
  return scored.length ? scored.reduce((sum, s) => sum + s.final_score, 0) / scored.length : 0
})
const totalSubmissions = computed(() => scores.value.reduce((sum, s) => sum + (s.total_submissions || 0), 0))

const columns = [
  { title: '任务', key: 'task_title', render: (row: any) => row.task_title || `任务 #${row.task_id}` },
  { title: '完成率', key: 'completion_rate', width: 130, render: (row: any) => h(NProgress, { type: 'line', percentage: row.completion_rate || 0, status: (row.completion_rate || 0) >= 100 ? 'success' : 'info', showIndicator: true, indicatorPlacement: 'inside' }) },
  { title: 'AI 评分', key: 'ai_total_score', width: 80, render: (row: any) => row.ai_total_score != null ? `${row.ai_total_score}` : '-' },
  { title: '教师评分', key: 'teacher_score', width: 80, render: (row: any) => row.teacher_score != null ? `${row.teacher_score}` : '-' },
  { title: '出勤分', key: 'attendance_score', width: 70, render: (row: any) => row.attendance_score ? `${row.attendance_score}` : '-' },
  { title: '加减分', key: 'bonus_score', width: 70, render: (row: any) => {
    const b = row.bonus_score || 0
    return b ? `${b > 0 ? '+' : ''}${b}` : '-'
  }},
  { title: '最终分数', key: 'final_score', width: 90, render: (row: any) => {
    const s = row.final_score
    if (s == null) return '-'
    const type = s >= 90 ? 'success' : s >= 60 ? 'warning' : 'error'
    return h(NTag, { type, size: 'small' }, { default: () => `${s}分` })
  }},
  { title: '提示', key: 'ai_hint_count', width: 60, render: (row: any) => row.ai_hint_count || 0 },
  { title: '提交', key: 'total_submissions', width: 50 },
  { title: '状态', key: 'status', width: 70, render: (row: any) => {
    const m: Record<string, { l: string; t: string }> = { in_progress: { l: '进行中', t: 'info' }, completed: { l: '已完成', t: 'success' }, reviewed: { l: '已评阅', t: 'success' } }
    const i = m[row.status] || { l: row.status, t: 'default' }
    return h(NTag, { type: i.t as any, size: 'small' }, { default: () => i.l })
  }}
]

async function loadScores() {
  loading.value = true
  try { scores.value = await submissionApi.getMyScores() as any } catch {} finally { loading.value = false }
}

onMounted(() => { loadScores() })
</script>

<style scoped>
.scores-container {
  max-width: 1100px;
  margin: 0 auto;
}

.page-title {
  margin: 0 0 24px;
  font-size: 20px;
}

.stat-card {
  background: #fff;
  border: 1px solid #e8e8ec;
  border-radius: 12px;
  padding: 20px;
  text-align: center;
}

.stat-num {
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
}

.stat-label {
  font-size: 13px;
  color: #999;
  margin-top: 4px;
}
</style>
