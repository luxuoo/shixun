<template>
  <div class="submissions-container">
    <div class="page-header">
      <h2>提交记录</h2>
      <n-space>
        <n-select v-model:value="selectedTask" :options="taskOptions" placeholder="选择任务" clearable style="width: 180px;" @update:value="loadSubmissions" />
        <n-select v-model:value="selectedStatus" :options="statusOptions" placeholder="状态" clearable style="width: 130px;" @update:value="loadSubmissions" />
      </n-space>
    </div>

    <n-card>
      <n-data-table :columns="columns" :data="submissions" :loading="loading" :bordered="false" :pagination="pagination" />
    </n-card>

    <!-- 详情弹窗 -->
    <n-modal v-model:show="showDetail" preset="card" title="提交详情" style="width: 800px">
      <n-space vertical :size="16">
        <n-descriptions bordered :column="2">
          <n-descriptions-item label="提交时间">{{ detailData.submitted_at ? new Date(detailData.submitted_at).toLocaleString() : '-' }}</n-descriptions-item>
          <n-descriptions-item label="状态"><n-tag :type="getStatusType(detailData.status)" size="small">{{ getStatusLabel(detailData.status) }}</n-tag></n-descriptions-item>
          <n-descriptions-item label="AI 评分"><span :style="{ color: getScoreColor(detailData.ai_score) }">{{ detailData.ai_score ? `${detailData.ai_score}分` : '待评分' }}</span></n-descriptions-item>
          <n-descriptions-item label="教师评分">{{ detailData.teacher_score ? `${detailData.teacher_score}分` : '待评分' }}</n-descriptions-item>
          <n-descriptions-item label="最终分数" :span="2"><span style="font-size: 24px; font-weight: bold;" :style="{ color: getScoreColor(detailData.final_score) }">{{ detailData.final_score ? `${detailData.final_score}分` : '-' }}</span></n-descriptions-item>
        </n-descriptions>
        <div v-if="detailData.ai_feedback">
          <h4 style="margin: 0 0 8px;">AI 反馈</h4>
          <n-card embedded><p style="margin: 0; white-space: pre-wrap;">{{ detailData.ai_feedback }}</p></n-card>
        </div>
        <div v-if="detailData.teacher_comment">
          <h4 style="margin: 0 0 8px;">教师评语</h4>
          <n-card embedded><p style="margin: 0; white-space: pre-wrap;">{{ detailData.teacher_comment }}</p></n-card>
        </div>
        <div>
          <h4 style="margin: 0 0 8px;">代码</h4>
          <n-card embedded><pre style="margin: 0; white-space: pre-wrap; font-family: monospace; font-size: 13px;">{{ detailData.code }}</pre></n-card>
        </div>
      </n-space>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h, reactive } from 'vue'
import { NButton, NTag } from 'naive-ui'
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
  { label: '教师已审核', value: 'reviewed' }
]

const pagination = reactive({
  page: 1, pageSize: 10, showSizePicker: true, pageSizes: [10, 20, 50],
  onChange: (p: number) => { pagination.page = p },
  onUpdatePageSize: (s: number) => { pagination.pageSize = s; pagination.page = 1 }
})

const columns = [
  { title: '任务', key: 'task_id', render: (row: any) => { const t = taskOptions.value.find(t => t.value === row.task_id); return t ? t.label : `任务 ${row.task_id}` } },
  { title: '步骤', key: 'step_id', width: 80, render: (row: any) => `步骤 ${row.step_id}` },
  { title: '提交时间', key: 'submitted_at', render: (row: any) => new Date(row.submitted_at).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' }) },
  { title: '状态', key: 'status', width: 100, render: (row: any) => h(NTag, { type: getStatusType(row.status), size: 'small' }, { default: () => getStatusLabel(row.status) }) },
  { title: 'AI 评分', key: 'ai_score', width: 80, render: (row: any) => h('span', { style: { color: getScoreColor(row.ai_score), fontWeight: 500 } }, row.ai_score ? `${row.ai_score}` : '-') },
  { title: '最终分数', key: 'final_score', width: 80, render: (row: any) => h('span', { style: { color: getScoreColor(row.final_score), fontWeight: 'bold' } }, row.final_score ? `${row.final_score}` : '-') },
  { title: '', key: 'actions', width: 60, render: (row: any) => h(NButton, { type: 'primary', size: 'small', quaternary: true, onClick: () => { detailData.value = row; showDetail.value = true } }, { default: () => '查看' }) }
]

function getStatusType(s: string) { return ({ pending: 'warning', ai_scored: 'info', reviewed: 'success' } as any)[s] || 'default' }
function getStatusLabel(s: string) { return ({ pending: '待评分', ai_scored: 'AI 已评分', reviewed: '已审核' } as any)[s] || s }
function getScoreColor(s: number | null) { if (!s) return '#999'; if (s >= 90) return '#18a058'; if (s >= 80) return '#2080f0'; if (s >= 60) return '#f0a020'; return '#d03050' }

async function loadSubmissions() {
  loading.value = true
  try {
    const params: any = {}
    if (selectedTask.value) params.task_id = selectedTask.value
    submissions.value = await submissionApi.getList(params) as any
  } catch {} finally { loading.value = false }
}

async function loadTasks() {
  try {
    const data = await taskApi.getList() as any
    taskOptions.value = data.map((t: any) => ({ label: t.title, value: t.id }))
  } catch {}
}

onMounted(() => { loadTasks(); loadSubmissions() })
</script>

<style scoped>
.submissions-container { max-width: 1100px; margin: 0 auto; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.page-header h2 { margin: 0; font-size: 20px; }
</style>
