<template>
  <div class="class-manage-container">
    <n-space justify="space-between" align="center" style="margin-bottom: 24px;">
      <h2>班级管理</h2>
      <n-button type="primary" @click="openCreateClass">
        创建班级
      </n-button>
    </n-space>

    <n-card>
      <n-data-table
        :columns="columns"
        :data="classes"
        :loading="loading"
        :bordered="false"
      />
    </n-card>

    <!-- 创建/编辑班级弹窗 -->
    <n-modal v-model:show="showClassModal" preset="card" :title="editingClass ? '编辑班级' : '创建班级'" style="width: 500px">
      <n-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-placement="left"
        label-width="80"
      >
        <n-form-item label="班级名称" path="name">
          <n-input v-model:value="formData.name" placeholder="请输入班级名称" />
        </n-form-item>
        <n-form-item label="描述" path="description">
          <n-input v-model:value="formData.description" type="textarea" placeholder="请输入班级描述" :rows="3" />
        </n-form-item>
        <n-form-item label="教师" path="teacher_id">
          <n-select
            v-model:value="formData.teacher_id"
            :options="teacherOptions"
            placeholder="选择教师"
            clearable
          />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showClassModal = false">取消</n-button>
          <n-button type="primary" :loading="saveLoading" @click="handleSaveClass">
            {{ editingClass ? '保存' : '创建' }}
          </n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 分配学生弹窗 -->
    <n-modal v-model:show="showAssignModal" preset="card" title="分配学生" style="width: 600px">
      <n-transfer
        v-model:value="selectedStudentIds"
        :options="studentTransferOptions"
        source-title="未分配学生"
        target-title="已分配学生"
        style="margin-bottom: 16px;"
      />
      <template #footer>
        <n-space justify="end">
          <n-button @click="showAssignModal = false">取消</n-button>
          <n-button type="primary" :loading="assignLoading" @click="handleAssignStudents">
            确认分配
          </n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 班级统计弹窗 -->
    <n-modal v-model:show="showStatsModal" preset="card" title="班级统计" style="width: 900px">
      <n-spin :show="statsLoading">
        <n-space vertical :size="16">
          <n-descriptions bordered :column="2">
            <n-descriptions-item label="班级名称">{{ classStats.class_name }}</n-descriptions-item>
            <n-descriptions-item label="学生总数">{{ classStats.total_students }}</n-descriptions-item>
            <n-descriptions-item label="平均分">{{ classStats.average_score }}</n-descriptions-item>
          </n-descriptions>

          <h4>成绩分布</h4>
          <n-space>
            <n-tag v-for="(count, range) in classStats.score_distribution" :key="range" type="info">
              {{ range }}: {{ count }}人
            </n-tag>
          </n-space>

          <h4>学生排名</h4>
          <n-data-table
            :columns="rankColumns"
            :data="classStats.rankings || []"
            :bordered="false"
            :max-height="300"
          />

          <h4>任务完成情况</h4>
          <n-data-table
            :columns="taskColumns"
            :data="taskCompletionData"
            :bordered="false"
          />
        </n-space>
      </n-spin>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, computed, h } from 'vue'
import { useMessage, useDialog } from 'naive-ui'
import type { FormInst, FormRules } from 'naive-ui'
import { NButton, NTag, NSpace } from 'naive-ui'
import { adminApi, authApi } from '@/api'

const message = useMessage()
const dialog = useDialog()
const loading = ref(false)
const saveLoading = ref(false)
const assignLoading = ref(false)
const statsLoading = ref(false)
const showClassModal = ref(false)
const showAssignModal = ref(false)
const showStatsModal = ref(false)
const formRef = ref<FormInst | null>(null)

const classes = ref<any[]>([])
const teachers = ref<any[]>([])
const allStudents = ref<any[]>([])
const editingClass = ref<any>(null)
const selectedClassId = ref<number | null>(null)
const selectedStudentIds = ref<number[]>([])
const classStats = ref<any>({})

const formData = ref({
  name: '',
  description: '',
  teacher_id: null as number | null
})

const rules: FormRules = {
  name: { required: true, message: '请输入班级名称', trigger: 'blur' }
}

const teacherOptions = computed(() =>
  teachers.value.map(t => ({ label: `${t.name} (${t.username})`, value: t.id }))
)

const studentTransferOptions = computed(() =>
  allStudents.value.map(s => ({ label: `${s.name || s.username}`, value: s.id }))
)

const columns = [
  { title: 'ID', key: 'id', width: 60 },
  { title: '班级名称', key: 'name' },
  { title: '描述', key: 'description', render: (row: any) => row.description || '-' },
  { title: '教师', key: 'teacher_name', render: (row: any) => row.teacher_name || '-' },
  { title: '学生数', key: 'student_count', width: 80 },
  {
    title: '操作',
    key: 'actions',
    width: 300,
    render: (row: any) => h(NSpace, { size: 'small' }, {
      default: () => [
        h(NButton, { type: 'primary', size: 'small', onClick: () => openAssignStudents(row) }, { default: () => '分配学生' }),
        h(NButton, { type: 'info', size: 'small', onClick: () => viewClassStats(row) }, { default: () => '统计' }),
        h(NButton, { type: 'warning', size: 'small', onClick: () => openEditClass(row) }, { default: () => '编辑' }),
        h(NButton, { type: 'error', size: 'small', onClick: () => confirmDeleteClass(row) }, { default: () => '删除' })
      ]
    })
  }
]

const rankColumns = [
  { title: '排名', key: 'rank', width: 60, render: (_row: any, index: number) => index + 1 },
  { title: '姓名', key: 'name' },
  { title: '用户名', key: 'username' },
  { title: '平均分', key: 'average_score' },
  { title: '任务数', key: 'task_count' }
]

const taskColumns = [
  { title: '任务', key: 'task_name' },
  { title: '总学生', key: 'total_students', width: 80 },
  { title: '已完成', key: 'completed', width: 80 },
  {
    title: '完成率',
    key: 'completion_rate',
    width: 100,
    render: (row: any) => `${row.completion_rate}%`
  }
]

const taskCompletionData = computed(() => {
  const tc = classStats.value.task_completion || {}
  return Object.entries(tc).map(([name, data]: [string, any]) => ({
    task_name: name,
    ...data
  }))
})

function openCreateClass() {
  editingClass.value = null
  formData.value = { name: '', description: '', teacher_id: null }
  showClassModal.value = true
}

function openEditClass(cls: any) {
  editingClass.value = cls
  formData.value = { name: cls.name, description: cls.description || '', teacher_id: cls.teacher_id }
  showClassModal.value = true
}

async function openAssignStudents(cls: any) {
  selectedClassId.value = cls.id
  // 加载所有学生
  try {
    const students = await adminApi.getStudents() as any
    allStudents.value = students
    // 已在该班级的学生
    const classStudents = students.filter((s: any) => s.class_id === cls.id)
    selectedStudentIds.value = classStudents.map((s: any) => s.id)
    showAssignModal.value = true
  } catch (error) {
    message.error('加载学生列表失败')
  }
}

async function viewClassStats(cls: any) {
  showStatsModal.value = true
  statsLoading.value = true
  try {
    const data = await adminApi.getClassStats(cls.id) as any
    classStats.value = data
  } catch (error) {
    message.error('加载班级统计失败')
  } finally {
    statsLoading.value = false
  }
}

async function loadClasses() {
  loading.value = true
  try {
    const data = await adminApi.getClasses() as any
    classes.value = data
  } catch (error) {
    console.error('加载班级列表失败', error)
  } finally {
    loading.value = false
  }
}

async function loadTeachers() {
  try {
    const data = await authApi.getUsers('teacher') as any
    teachers.value = data
  } catch (error) {
    console.error('加载教师列表失败', error)
  }
}

async function handleSaveClass() {
  try {
    await formRef.value?.validate()
    saveLoading.value = true
    if (editingClass.value) {
      await adminApi.updateClass(editingClass.value.id, formData.value)
      message.success('班级更新成功')
    } else {
      await authApi.createClass(formData.value)
      message.success('班级创建成功')
    }
    showClassModal.value = false
    loadClasses()
  } catch (error: any) {
    message.error(error.detail || '操作失败')
  } finally {
    saveLoading.value = false
  }
}

async function handleAssignStudents() {
  if (!selectedClassId.value) return
  assignLoading.value = true
  try {
    await adminApi.assignStudents(selectedClassId.value, selectedStudentIds.value)
    message.success('学生分配成功')
    showAssignModal.value = false
    loadClasses()
  } catch (error: any) {
    message.error(error.detail || '分配失败')
  } finally {
    assignLoading.value = false
  }
}

function confirmDeleteClass(cls: any) {
  dialog.warning({
    title: '确认删除',
    content: `确定要删除班级"${cls.name}"吗？该班级的学生将被取消班级分配。`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await adminApi.deleteClass(cls.id)
        message.success('班级已删除')
        loadClasses()
      } catch (error: any) {
        message.error(error.detail || '删除失败')
      }
    }
  })
}

onMounted(() => {
  loadClasses()
  loadTeachers()
})
</script>

<style scoped>
.class-manage-container {
  max-width: 1200px;
  margin: 0 auto;
}
</style>
