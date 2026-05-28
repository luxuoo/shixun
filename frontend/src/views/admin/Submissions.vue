<template>
  <div class="submissions-container">
    <n-space justify="space-between" align="center" style="margin-bottom: 24px;">
      <h2>提交记录管理</h2>
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
        <n-button
          type="warning"
          :disabled="selectedRowKeys.length === 0"
          @click="showBatchReview = true"
        >
          批量评分 ({{ selectedRowKeys.length }})
        </n-button>
      </n-space>
    </n-space>

    <n-card>
      <n-data-table
        :columns="columns"
        :data="submissions"
        :loading="loading"
        :bordered="false"
        :pagination="pagination"
        :row-key="(row: any) => row.id"
        v-model:checked-row-keys="selectedRowKeys"
      />
    </n-card>

    <!-- 单个评分弹窗 -->
    <n-modal v-model:show="showReview" preset="card" title="评分" style="width: 700px">
      <n-space vertical :size="16">
        <n-descriptions bordered :column="2">
          <n-descriptions-item label="学生">{{ reviewData.user_name || reviewData.username || `ID: ${reviewData.user_id}` }}</n-descriptions-item>
          <n-descriptions-item label="任务">{{ reviewData.task_title || `ID: ${reviewData.task_id}` }}</n-descriptions-item>
          <n-descriptions-item label="AI 评分">{{ reviewData.ai_score || '-' }}</n-descriptions-item>
          <n-descriptions-item label="提交时间">{{ reviewData.submitted_at ? new Date(reviewData.submitted_at).toLocaleString() : '-' }}</n-descriptions-item>
        </n-descriptions>

        <div v-if="reviewData.ai_feedback">
          <h4 style="margin: 0 0 8px 0;">AI 反馈</h4>
          <n-card embedded>
            <p style="margin: 0; white-space: pre-wrap;">{{ reviewData.ai_feedback }}</p>
          </n-card>
        </div>

        <div>
          <h4 style="margin: 0 0 8px 0;">学生代码</h4>
          <n-card embedded>
            <pre style="margin: 0; white-space: pre-wrap; font-family: monospace; max-height: 300px; overflow-y: auto;">{{ reviewData.code }}</pre>
          </n-card>
        </div>

        <n-form label-placement="left" label-width="80">
          <n-form-item label="老师评分">
            <n-input-number v-model:value="reviewForm.teacher_score" :min="0" :max="100" style="width: 200px;" />
          </n-form-item>
          <n-form-item label="评语">
            <n-input v-model:value="reviewForm.teacher_comment" type="textarea" placeholder="请输入评语" :rows="3" />
          </n-form-item>
        </n-form>
      </n-space>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showReview = false">取消</n-button>
          <n-button type="primary" :loading="reviewLoading" @click="handleReview">
            提交评分
          </n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 批量评分弹窗 -->
    <n-modal v-model:show="showBatchReview" preset="card" title="批量评分" style="width: 500px">
      <n-space vertical :size="16">
        <n-alert type="info">
          已选择 {{ selectedRowKeys.length }} 条提交记录
        </n-alert>
        <n-form label-placement="left" label-width="80">
          <n-form-item label="统一评分">
            <n-input-number v-model:value="batchForm.teacher_score" :min="0" :max="100" style="width: 200px;" />
          </n-form-item>
          <n-form-item label="评语">
            <n-input v-model:value="batchForm.teacher_comment" type="textarea" placeholder="批量评语（可选）" :rows="3" />
          </n-form-item>
        </n-form>
      </n-space>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showBatchReview = false">取消</n-button>
          <n-button type="primary" :loading="batchLoading" @click="handleBatchReview">
            确认批量评分
          </n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, h } from 'vue'
import { useMessage } from 'naive-ui'
import { NButton, NTag } from 'naive-ui'
import { adminApi, taskApi } from '@/api'

const message = useMessage()
const loading = ref(false)
const reviewLoading = ref(false)
const batchLoading = ref(false)
const showReview = ref(false)
const showBatchReview = ref(false)

const submissions = ref<any[]>([])
const selectedTask = ref<number | null>(null)
const selectedStatus = ref<string | null>(null)
const taskOptions = ref<{ label: string; value: number }[]>([])
const selectedRowKeys = ref<number[]>([])

const reviewData = ref<any>({})
const reviewForm = ref({
  teacher_score: 80,
  teacher_comment: ''
})

const batchForm = ref({
  teacher_score: 80,
  teacher_comment: ''
})

const statusOptions = [
  { label: '待评分', value: 'pending' },
  { label: 'AI 已评分', value: 'ai_scored' },
  { label: '老师已审核', value: 'reviewed' }
]

const pagination = reactive({
  page: 1,
  pageSize: 20,
  showSizePicker: true,
  pageSizes: [10, 20, 50, 100],
  onChange: (page: number) => { pagination.page = page },
  onUpdatePageSize: (pageSize: number) => { pagination.pageSize = pageSize; pagination.page = 1 }
})

const columns = [
  { type: 'selection' as const },
  { title: 'ID', key: 'id', width: 60 },
  {
    title: '学生',
    key: 'user_id',
    width: 100,
    render: (row: any) => row.user_name || row.username || `ID: ${row.user_id}`
  },
  {
    title: '任务',
    key: 'task_id',
    render: (row: any) => row.task_title || `任务 ${row.task_id}`
  },
  { title: '步骤', key: 'step_id', width: 80 },
  {
    title: '状态',
    key: 'status',
    width: 100,
    render: (row: any) => h(NTag, { type: getStatusType(row.status), size: 'small' }, { default: () => getStatusLabel(row.status) })
  },
  {
    title: 'AI 评分',
    key: 'ai_score',
    width: 90,
    render: (row: any) => h('span', { style: { color: getScoreColor(row.ai_score) } }, row.ai_score ? `${row.ai_score}分` : '-')
  },
  {
    title: '老师评分',
    key: 'teacher_score',
    width: 90,
    render: (row: any) => row.teacher_score ? `${row.teacher_score}分` : '-'
  },
  {
    title: '最终分数',
    key: 'final_score',
    width: 90,
    render: (row: any) => h('span', { style: { color: getScoreColor(row.final_score), fontWeight: 'bold' } }, row.final_score ? `${row.final_score}分` : '-')
  },
  {
    title: '提交时间',
    key: 'submitted_at',
    width: 160,
    render: (row: any) => new Date(row.submitted_at).toLocaleString()
  },
  {
    title: '操作',
    key: 'actions',
    width: 80,
    render: (row: any) => h(NButton, { type: 'primary', size: 'small', onClick: () => openReview(row) }, { default: () => '评分' })
  }
]

function getStatusType(status: string) {
  const types: Record<string, string> = { 'pending': 'warning', 'ai_scored': 'info', 'reviewed': 'success' }
  return types[status] as any || 'default'
}

function getStatusLabel(status: string) {
  const labels: Record<string, string> = { 'pending': '待评分', 'ai_scored': 'AI 已评分', 'reviewed': '老师已审核' }
  return labels[status] || status
}

function getScoreColor(score: number | null) {
  if (!score) return '#999'
  if (score >= 90) return '#18a058'
  if (score >= 80) return '#2080f0'
  if (score >= 60) return '#f0a020'
  return '#d03050'
}

function openReview(row: any) {
  reviewData.value = row
  reviewForm.value = {
    teacher_score: row.teacher_score || 80,
    teacher_comment: row.teacher_comment || ''
  }
  showReview.value = true
}

async function handleReview() {
  reviewLoading.value = true
  try {
    await adminApi.reviewSubmission(reviewData.value.id, reviewForm.value)
    message.success('评分成功')
    showReview.value = false
    loadSubmissions()
  } catch (error: any) {
    message.error(error.detail || '评分失败')
  } finally {
    reviewLoading.value = false
  }
}

async function handleBatchReview() {
  if (selectedRowKeys.value.length === 0) return
  batchLoading.value = true
  try {
    await adminApi.batchScore({
      submission_ids: selectedRowKeys.value,
      teacher_score: batchForm.value.teacher_score,
      teacher_comment: batchForm.value.teacher_comment
    })
    message.success(`成功评分 ${selectedRowKeys.value.length} 条记录`)
    showBatchReview.value = false
    selectedRowKeys.value = []
    loadSubmissions()
  } catch (error: any) {
    message.error(error.detail || '批量评分失败')
  } finally {
    batchLoading.value = false
  }
}

async function loadSubmissions() {
  loading.value = true
  try {
    const params: any = {}
    if (selectedTask.value) params.task_id = selectedTask.value
    if (selectedStatus.value) params.status = selectedStatus.value
    const data = await adminApi.getSubmissions(params) as any
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
  max-width: 1400px;
  margin: 0 auto;
}
</style>
