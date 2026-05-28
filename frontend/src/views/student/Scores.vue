<template>
  <div class="scores-container">
    <n-space justify="space-between" align="center" style="margin-bottom: 24px;">
      <h2>我的成绩单</h2>
    </n-space>

    <!-- 统计卡片 -->
    <n-grid :cols="4" :x-gap="16" style="margin-bottom: 24px;">
      <n-gi>
        <n-card>
          <n-statistic label="已完成任务" :value="completedTasks" />
        </n-card>
      </n-gi>
      <n-gi>
        <n-card>
          <n-statistic label="进行中任务" :value="inProgressTasks" />
        </n-card>
      </n-gi>
      <n-gi>
        <n-card>
          <n-statistic label="平均分" :value="averageScore" :precision="1" />
        </n-card>
      </n-gi>
      <n-gi>
        <n-card>
          <n-statistic label="总提交次数" :value="totalSubmissions" />
        </n-card>
      </n-gi>
    </n-grid>

    <!-- 成绩表格 -->
    <n-card>
      <n-data-table
        :columns="columns"
        :data="scores"
        :loading="loading"
        :bordered="false"
        :pagination="pagination"
      />
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
  page: 1,
  pageSize: 10,
  showSizePicker: true,
  pageSizes: [10, 20],
  onChange: (page: number) => { pagination.page = page },
  onUpdatePageSize: (pageSize: number) => { pagination.pageSize = pageSize; pagination.page = 1 }
})

const completedTasks = computed(() => scores.value.filter(s => s.status === 'completed' || s.status === 'reviewed').length)
const inProgressTasks = computed(() => scores.value.filter(s => s.status === 'in_progress').length)
const averageScore = computed(() => {
  const scored = scores.value.filter(s => s.final_score != null)
  if (scored.length === 0) return 0
  return scored.reduce((sum, s) => sum + s.final_score, 0) / scored.length
})
const totalSubmissions = computed(() => scores.value.reduce((sum, s) => sum + (s.total_submissions || 0), 0))

const columns = [
  {
    title: '任务名称',
    key: 'task_title',
    render: (row: any) => row.task_title || `任务 #${row.task_id}`
  },
  {
    title: '完成率',
    key: 'completion_rate',
    width: 160,
    render: (row: any) => h(NProgress, {
      type: 'line',
      percentage: row.completion_rate || 0,
      status: (row.completion_rate || 0) >= 100 ? 'success' : 'info',
      showIndicator: true,
      indicatorPlacement: 'inside'
    })
  },
  {
    title: 'AI 评分',
    key: 'ai_total_score',
    width: 100,
    render: (row: any) => row.ai_total_score != null ? `${row.ai_total_score}分` : '-'
  },
  {
    title: '教师评分',
    key: 'teacher_score',
    width: 100,
    render: (row: any) => row.teacher_score != null ? `${row.teacher_score}分` : '-'
  },
  {
    title: '最终分数',
    key: 'final_score',
    width: 100,
    render: (row: any) => {
      const score = row.final_score
      if (score == null) return '-'
      const type = score >= 90 ? 'success' : score >= 60 ? 'warning' : 'error'
      return h(NTag, { type, size: 'small' }, { default: () => `${score}分` })
    }
  },
  {
    title: 'AI 提示使用',
    key: 'ai_hint_count',
    width: 110,
    render: (row: any) => row.ai_hint_count || 0
  },
  {
    title: '提交次数',
    key: 'total_submissions',
    width: 100
  },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render: (row: any) => {
      const map: Record<string, { label: string; type: string }> = {
        in_progress: { label: '进行中', type: 'info' },
        completed: { label: '已完成', type: 'success' },
        reviewed: { label: '已评阅', type: 'success' }
      }
      const info = map[row.status] || { label: row.status, type: 'default' }
      return h(NTag, { type: info.type as any, size: 'small' }, { default: () => info.label })
    }
  }
]

async function loadScores() {
  loading.value = true
  try {
    const data = await submissionApi.getMyScores() as any
    scores.value = data
  } catch (error) {
    console.error('加载成绩单失败', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadScores()
})
</script>

<style scoped>
.scores-container {
  max-width: 1200px;
  margin: 0 auto;
}
</style>
