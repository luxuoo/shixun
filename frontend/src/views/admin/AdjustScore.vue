<template>
  <div class="adjust-score-container">
    <h2 class="page-title">加减分</h2>

    <!-- 筛选栏 -->
    <div class="filter-bar">
      <n-select v-model:value="selectedClass" :options="classOptions" placeholder="选择班级" clearable style="width: 180px;" @update:value="loadStudents" />
      <n-input v-model:value="searchText" placeholder="搜索姓名或学号" clearable style="width: 200px;" />
    </div>

    <!-- 学生列表 -->
    <n-card>
      <n-data-table
        :columns="columns"
        :data="filteredStudents"
        :loading="loading"
        :bordered="false"
        :pagination="pagination"
        :row-class-name="() => 'student-row'"
      />
    </n-card>

    <!-- 加减分弹窗 -->
    <n-modal v-model:show="showModal" preset="card" title="加减分" style="width: 500px">
      <n-space vertical :size="20">
        <n-descriptions bordered :column="1">
          <n-descriptions-item label="学生">{{ currentStudent?.name }}</n-descriptions-item>
          <n-descriptions-item label="学号">{{ currentStudent?.student_id || '-' }}</n-descriptions-item>
          <n-descriptions-item label="班级">{{ getClassName(currentStudent?.class_id) }}</n-descriptions-item>
        </n-descriptions>

        <div>
          <div style="margin-bottom: 8px; font-weight: 500;">选择任务</div>
          <n-select v-model:value="form.taskId" :options="taskOptions" placeholder="不选择则调整所有任务" clearable />
        </div>

        <div>
          <div style="margin-bottom: 8px; font-weight: 500;">调整分数</div>
          <n-input-number v-model:value="form.adjustment" :min="-100" :max="100" style="width: 100%;" />
          <div style="margin-top: 6px; display: flex; gap: 8px;">
            <n-button size="small" @click="form.adjustment = 5">+5</n-button>
            <n-button size="small" @click="form.adjustment = 10">+10</n-button>
            <n-button size="small" @click="form.adjustment = -5">-5</n-button>
            <n-button size="small" @click="form.adjustment = -10">-10</n-button>
          </div>
        </div>

        <div>
          <div style="margin-bottom: 8px; font-weight: 500;">原因</div>
          <n-input v-model:value="form.reason" type="textarea" placeholder="请输入加减分原因" :rows="3" />
        </div>
      </n-space>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showModal = false">取消</n-button>
          <n-button type="primary" :loading="submitting" :disabled="form.adjustment === 0" @click="handleSubmit">
            {{ form.adjustment > 0 ? '加' : '减' }}{{ Math.abs(form.adjustment) }}分
          </n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, h, reactive } from 'vue'
import { useMessage } from 'naive-ui'
import { NButton, NTag } from 'naive-ui'
import { adminApi, authApi, taskApi } from '@/api'

const message = useMessage()
const loading = ref(false)
const submitting = ref(false)
const showModal = ref(false)
const students = ref<any[]>([])
const selectedClass = ref<number | null>(null)
const classOptions = ref<{ label: string; value: number }[]>([])
const taskOptions = ref<{ label: string; value: number }[]>([])
const searchText = ref('')
const currentStudent = ref<any>(null)

const form = ref({
  taskId: null as number | null,
  adjustment: 0,
  reason: ''
})

const pagination = reactive({
  page: 1, pageSize: 20, showSizePicker: true, pageSizes: [20, 50],
  onChange: (p: number) => { pagination.page = p },
  onUpdatePageSize: (s: number) => { pagination.pageSize = s; pagination.page = 1 }
})

const filteredStudents = computed(() => {
  if (!searchText.value) return students.value
  const q = searchText.value.toLowerCase()
  return students.value.filter(s =>
    (s.name || '').toLowerCase().includes(q) ||
    (s.student_id || '').toLowerCase().includes(q)
  )
})

function getClassName(classId: number | null) {
  if (!classId) return '-'
  const cls = classOptions.value.find(c => c.value === classId)
  return cls ? cls.label : '-'
}

const columns = [
  { title: '学号', key: 'student_id', width: 120, sorter: (a: any, b: any) => (a.student_id || '').localeCompare(b.student_id || ''), render: (row: any) => row.student_id || '-' },
  { title: '姓名', key: 'name', width: 100 },
  { title: '班级', key: 'class_id', width: 140, render: (row: any) => getClassName(row.class_id) },
  { title: '用户名', key: 'username', width: 100 },
  { title: '状态', key: 'is_active', width: 80, render: (row: any) => h(NTag, { type: row.is_active ? 'success' : 'error', size: 'small' }, { default: () => row.is_active ? '正常' : '禁用' }) },
  { title: '操作', key: 'actions', width: 100, render: (row: any) => h(NButton, { type: 'warning', size: 'small', onClick: () => openModal(row) }, { default: () => '加减分' }) }
]

function openModal(student: any) {
  currentStudent.value = student
  form.value = { taskId: null, adjustment: 0, reason: '' }
  showModal.value = true
}

async function handleSubmit() {
  if (!currentStudent.value || form.value.adjustment === 0) return
  submitting.value = true
  try {
    await adminApi.adjustScore(currentStudent.value.id, {
      task_id: form.value.taskId || undefined,
      adjustment: form.value.adjustment,
      reason: form.value.reason
    })
    message.success(`已${form.value.adjustment > 0 ? '加' : '减'}${Math.abs(form.value.adjustment)}分`)
    showModal.value = false
  } catch (error: any) {
    message.error(error.detail || '操作失败')
  } finally {
    submitting.value = false
  }
}

async function loadStudents() {
  loading.value = true
  try {
    students.value = await adminApi.getStudents(selectedClass.value || undefined) as any
  } catch (error: any) {
    message.error(error?.detail || '加载学生列表失败')
  } finally { loading.value = false }
}

async function loadClasses() {
  try {
    const data = await authApi.getClasses() as any
    classOptions.value = data.map((c: any) => ({ label: c.name, value: c.id }))
  } catch (error: any) {
    message.error(error?.detail || '加载班级列表失败')
  }
}

async function loadTasks() {
  try {
    const data = await taskApi.getList() as any
    taskOptions.value = data.map((t: any) => ({ label: t.title, value: t.id }))
  } catch (error: any) {
    message.error(error?.detail || '加载任务列表失败')
  }
}

onMounted(() => {
  loadClasses()
  loadStudents()
  loadTasks()
})
</script>

<style scoped>
.adjust-score-container { max-width: 1100px; margin: 0 auto; }
.page-title { margin: 0 0 24px; font-size: 20px; }
.filter-bar { display: flex; gap: 12px; margin-bottom: 16px; }
:deep(.student-row td) { white-space: nowrap; }
</style>
