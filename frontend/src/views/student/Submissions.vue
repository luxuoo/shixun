<template>
  <div class="submissions-container">
    <n-space justify="space-between" align="center" style="margin-bottom: 24px;">
      <h2>我的提交记录</h2>
      <n-space>
        <n-select
          v-model:value="selectedTask"
          :options="taskOptions"
          placeholder="选择任务"
          clearable
          style="width: 200px;"
          @update:value="loadSubmissions"
        />
        <n-select
          v-model:value="selectedStatus"
          :options="statusOptions"
          placeholder="选择状态"
          clearable
          style="width: 150px;"
          @update:value="loadSubmissions"
        />
      </n-space>
    </n-space>

    <n-card>
      <n-data-table
        :columns="columns"
        :data="submissions"
        :loading="loading"
        :bordered="false"
        :pagination="pagination"
      />
    </n-card>

    <!-- 提交详情弹窗 -->
    <n-modal v-model:show="showDetail" preset="card" title="提交详情" style="width: 800px">
      <n-space vertical :size="16">
        <n-descriptions bordered :column="2">
          <n-descriptions-item label="提交时间">
            {{ detailData.submitted_at ? new Date(detailData.submitted_at).toLocaleString() : '-' }}
          </n-descriptions-item>
          <n-descriptions-item label="状态">
            <n-tag :type="getStatusType(detailData.status)">
              {{ getStatusLabel(detailData.status) }}
            </n-tag>
          </n-descriptions-item>
          <n-descriptions-item label="AI 评分">
            <span :style="{ color: getScoreColor(detailData.ai_score) }">
              {{ detailData.ai_score ? `${detailData.ai_score}分` : '待评分' }}
            </span>
          </n-descriptions-item>
          <n-descriptions-item label="老师评分">
            {{ detailData.teacher_score ? `${detailData.teacher_score}分` : '待评分' }}
          </n-descriptions-item>
          <n-descriptions-item label="最终分数" :span="2">
            <span style="font-size: 24px; font-weight: bold;" :style="{ color: getScoreColor(detailData.final_score) }">
              {{ detailData.final_score ? `${detailData.final_score}分` : '-' }}
            </span>
          </n-descriptions-item>
        </n-descriptions>

        <div v-if="detailData.ai_feedback">
          <h4 style="margin: 0 0 8px 0;">AI 反馈</h4>
          <n-card embedded>
            <p style="margin: 0; white-space: pre-wrap;">{{ detailData.ai_feedback }}</p>
          </n-card>
        </div>

        <div v-if="detailData.teacher_comment">
          <h4 style="margin: 0 0 8px 0;">老师评语</h4>
          <n-card embedded>
            <p style="margin: 0; white-space: pre-wrap;">{{ detailData.teacher_comment }}</p>
          </n-card>
        </div>

        <div>
          <h4 style="margin: 0 0 8px 0;">提交的代码</h4>
          <n-card embedded>
            <pre style="margin: 0; white-space: pre-wrap; font-family: monospace;">{{ detailData.code }}</pre>
          </n-card>
        </div>
      </n-space>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h, reactive } from 'vue'
import { NButton, NTag } from 'naive-ui'
import type { DataTableColumns } from 'naive-ui'
import { submissionApi, taskApi } from '@/api'

const loading = ref(false)
const submissions = ref<any[]>([])
const selectedTask = ref<number | null>(null)
const selectedStatus = ref<string | null>(null)
const showDetail = ref(false)
const detailData = ref<any>({})
const taskOptions = ref<{ label: string; value: number }[]>([])

const statusOptions = [
  { label: '待评分', value: 'pending' },
  { label: 'AI 已评分', value: 'ai_scored' },
  { label: '老师已审核', value: 'reviewed' }
]

const pagination = reactive({
  page: 1,
  pageSize: 10,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
  onChange: (page: number) => {
    pagination.page = page
  },
  onUpdatePageSize: (pageSize: number) => {
    pagination.pageSize = pageSize
    pagination.page = 1
  }
})

const columns: DataTableColumns<any> = [
  {
    title: '任务名称',
    key: 'task_id',
    render: (row) => {
      const task = taskOptions.value.find(t => t.value === row.task_id)
      return task ? task.label : `任务 ${row.task_id}`
    }
  },
  {
    title: '步骤',
    key: 'step_id',
    render: (row) => `步骤 ${row.step_id}`
  },
  {
    title: '提交时间',
    key: 'submitted_at',
    render: (row) => new Date(row.submitted_at).toLocaleString()
  },
  {
    title: '状态',
    key: 'status',
    render: (row) => h(NTag, { type: getStatusType(row.status), size: 'small' }, { default: () => getStatusLabel(row.status) })
  },
  {
    title: 'AI 评分',
    key: 'ai_score',
    render: (row) => h('span', { style: { color: getScoreColor(row.ai_score) } }, row.ai_score ? `${row.ai_score}分` : '-')
  },
  {
    title: '最终分数',
    key: 'final_score',
    render: (row) => h('span', { style: { color: getScoreColor(row.final_score), fontWeight: 'bold' } }, row.final_score ? `${row.final_score}分` : '-')
  },
  {
    title: '操作',
    key: 'actions',
    render: (row) => h(NButton, { type: 'primary', size: 'small', onClick: () => viewDetail(row) }, { default: () => '查看' })
  }
]

function getStatusType(status: string) {
  const types: Record<string, string> = {
    'pending': 'warning',
    'ai_scored': 'info',
    'reviewed': 'success'
  }
  return types[status] as any || 'default'
}

function getStatusLabel(status: string) {
  const labels: Record<string, string> = {
    'pending': '待评分',
    'ai_scored': 'AI 已评分',
    'reviewed': '老师已审核'
  }
  return labels[status] || status
}

function getScoreColor(score: number | null) {
  if (!score) return '#999'
  if (score >= 90) return '#18a058'
  if (score >= 80) return '#2080f0'
  if (score >= 60) return '#f0a020'
  return '#d03050'
}

function viewDetail(row: any) {
  detailData.value = row
  showDetail.value = true
}

async function loadSubmissions() {
  loading.value = true
  try {
    const params: any = {}
    if (selectedTask.value) params.task_id = selectedTask.value
    const data = await submissionApi.getList(params) as any
    submissions.value = data
  } catch (error) {
    console.error('加载提交记录失败', error)
  } finally {
    loading.value = false
  }
}

async function loadTasks() {
  try {
    const data = await taskApi.getList() as any
    taskOptions.value = data.map((t: any) => ({
      label: t.title,
      value: t.id
    }))
  } catch (error) {
    console.error('加载任务列表失败', error)
  }
}

onMounted(() => {
  loadTasks()
  loadSubmissions()
})
</script>

<style scoped>
.submissions-container {
  max-width: 1200px;
  margin: 0 auto;
}
</style>
