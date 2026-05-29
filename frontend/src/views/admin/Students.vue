<template>
  <div class="students-container">
    <n-space justify="space-between" align="center" style="margin-bottom: 24px;">
      <h2>学生管理</h2>
      <n-space>
        <n-select
          v-model:value="selectedClass"
          :options="classOptions"
          placeholder="选择班级"
          clearable
          style="width: 200px;"
          @update:value="loadStudents"
        />
        <n-button type="success" @click="showBatchRegister = true">
          批量注册
        </n-button>
        <n-button type="primary" @click="showAddStudent = true">
          添加学生
        </n-button>
        <n-button @click="showSettings = true">
          设置
        </n-button>
      </n-space>
    </n-space>

    <n-card>
      <n-data-table
        :columns="columns"
        :data="students"
        :loading="loading"
        :bordered="false"
        :pagination="pagination"
      />
    </n-card>

    <!-- 学生详情弹窗 -->
    <n-modal v-model:show="showDetail" preset="card" title="学生详情" style="width: 800px">
      <n-spin :show="detailLoading">
        <n-space vertical :size="16">
          <n-descriptions bordered :column="2">
            <n-descriptions-item label="姓名">{{ detailData.student?.name }}</n-descriptions-item>
            <n-descriptions-item label="用户名">{{ detailData.student?.username }}</n-descriptions-item>
            <n-descriptions-item label="学号">{{ detailData.student?.student_id || '-' }}</n-descriptions-item>
            <n-descriptions-item label="邮箱">{{ detailData.student?.email || '-' }}</n-descriptions-item>
            <n-descriptions-item label="提交次数">{{ detailData.total_submissions }}</n-descriptions-item>
            <n-descriptions-item label="AI 使用次数">{{ detailData.total_ai_calls }}</n-descriptions-item>
          </n-descriptions>
          <h4>任务完成情况</h4>
          <n-data-table :columns="scoreColumns" :data="detailData.scores || []" :bordered="false" />
          <n-divider />
          <n-space>
            <n-button type="warning" @click="openAdjustScore()">总分加减分</n-button>
          </n-space>
        </n-space>
      </n-spin>
    </n-modal>

    <!-- 添加学生弹窗 -->
    <n-modal v-model:show="showAddStudent" preset="card" title="添加学生" style="width: 500px">
      <n-form ref="formRef" :model="formData" :rules="rules" label-placement="left" label-width="80">
        <n-form-item label="用户名" path="username">
          <n-input v-model:value="formData.username" placeholder="请输入用户名" />
        </n-form-item>
        <n-form-item label="密码" path="password">
          <n-input v-model:value="formData.password" type="password" placeholder="请输入密码" />
        </n-form-item>
        <n-form-item label="姓名" path="name">
          <n-input v-model:value="formData.name" placeholder="请输入姓名" />
        </n-form-item>
        <n-form-item label="学号" path="student_id">
          <n-input v-model:value="formData.student_id" placeholder="请输入学号" />
        </n-form-item>
        <n-form-item label="邮箱" path="email">
          <n-input v-model:value="formData.email" placeholder="请输入邮箱" />
        </n-form-item>
        <n-form-item label="班级" path="class_id">
          <n-select v-model:value="formData.class_id" :options="classOptions" placeholder="请选择班级" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showAddStudent = false">取消</n-button>
          <n-button type="primary" :loading="addLoading" @click="handleAddStudent">添加</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 批量注册弹窗 -->
    <n-modal v-model:show="showBatchRegister" preset="card" title="批量注册学生" style="width: 700px">
      <n-space vertical :size="16">
        <n-alert type="info">
          输入学号和姓名，每行一个学生。用户名自动使用学号，系统会生成随机密码。注册完成后可导出密码列表。
        </n-alert>
        <n-form label-placement="left" label-width="80">
          <n-form-item label="班级" required>
            <n-select v-model:value="batchClassId" :options="classOptions" placeholder="请选择班级" />
          </n-form-item>
          <n-form-item label="学生列表">
            <n-input
              v-model:value="batchText"
              type="textarea"
              placeholder="每行格式：学号 姓名&#10;例如：&#10;2024001 张三&#10;2024002 李四&#10;2024003 王五"
              :rows="10"
              style="font-family: monospace;"
            />
          </n-form-item>
        </n-form>

        <!-- 注册结果 -->
        <div v-if="batchResult">
          <n-divider>注册结果</n-divider>
          <n-alert v-if="batchResult.errors?.length" type="warning" style="margin-bottom: 12px;">
            <div v-for="(err, i) in batchResult.errors" :key="i">{{ err }}</div>
          </n-alert>
          <n-alert type="success" style="margin-bottom: 12px;">
            成功注册 {{ batchResult.success }} 名学生到 {{ batchResult.class_name }}
          </n-alert>
          <n-data-table
            :columns="batchResultColumns"
            :data="batchResult.students || []"
            :bordered="false"
            :max-height="300"
          />
          <n-button type="primary" style="margin-top: 12px;" @click="exportPasswords">
            导出密码列表
          </n-button>
        </div>
      </n-space>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showBatchRegister = false">关闭</n-button>
          <n-button type="primary" :loading="batchLoading" :disabled="!batchClassId || !batchText.trim()" @click="handleBatchRegister">
            开始注册
          </n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 加减分弹窗 -->
    <n-modal v-model:show="showAdjustScore" preset="card" title="加减分" style="width: 450px">
      <n-space vertical :size="16">
        <n-descriptions bordered :column="1">
          <n-descriptions-item label="学生">{{ detailData.student?.name }} ({{ detailData.student?.student_id }})</n-descriptions-item>
          <n-descriptions-item label="任务">{{ adjustTaskId ? (detailData.scores?.find((s: any) => s.task_id === adjustTaskId)?.task_title || `任务 #${adjustTaskId}`) : '所有任务（总分调整）' }}</n-descriptions-item>
        </n-descriptions>
        <n-form-item label="调整分数">
          <n-input-number v-model:value="adjustValue" :min="-100" :max="100" style="width: 100%;" />
        </n-form-item>
        <n-form-item label="原因">
          <n-input v-model:value="adjustReason" type="textarea" placeholder="请输入加减分原因" />
        </n-form-item>
      </n-space>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showAdjustScore = false">取消</n-button>
          <n-button type="primary" :loading="adjustLoading" @click="handleAdjustScore">确认</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 设置弹窗 -->
    <n-modal v-model:show="showSettings" preset="card" title="系统设置" style="width: 560px">
      <n-space vertical :size="20">
        <n-descriptions bordered :column="1">
          <n-descriptions-item label="学生自主注册">
            <n-switch v-model:value="settings.student_register_enabled" @update:value="saveSettings" />
            <span style="margin-left: 12px; color: #666;">
              {{ settings.student_register_enabled ? '已开启 - 学生可在登录页自行注册' : '已关闭 - 只能由管理员批量注册' }}
            </span>
          </n-descriptions-item>
        </n-descriptions>

        <n-divider>AI 功能控制</n-divider>

        <n-descriptions bordered :column="1">
          <n-descriptions-item label="AI 对话功能">
            <n-switch v-model:value="settings.ai_chat_enabled" @update:value="saveSettings" />
            <span style="margin-left: 12px; color: #666;">
              {{ settings.ai_chat_enabled ? '已开启 - 学生可使用 AI 提示和代码分析' : '已关闭 - 学生无法使用 AI 对话功能' }}
            </span>
          </n-descriptions-item>
          <n-descriptions-item label="提示次数上限">
            <n-space align="center">
              <n-input-number
                v-model:value="settings.ai_hints_limit"
                :min="0"
                :max="999"
                style="width: 120px;"
                @update:value="saveSettings"
              />
              <span style="color: #666;">
                {{ settings.ai_hints_limit > 0 ? `每个步骤最多 ${settings.ai_hints_limit} 次提示` : '0 = 使用每个步骤自带的提示次数' }}
              </span>
            </n-space>
          </n-descriptions-item>
          <n-descriptions-item label="提交自动评分">
            <n-switch v-model:value="settings.ai_auto_score" @update:value="saveSettings" />
            <span style="margin-left: 12px; color: #666;">
              {{ settings.ai_auto_score ? '已开启 - 提交代码后 AI 自动评分' : '已关闭 - 需要教师手动评分' }}
            </span>
          </n-descriptions-item>
        </n-descriptions>
      </n-space>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, h } from 'vue'
import { useMessage } from 'naive-ui'
import type { FormInst, FormRules } from 'naive-ui'
import { NButton, NTag } from 'naive-ui'
import { adminApi, authApi } from '@/api'

const message = useMessage()
const loading = ref(false)
const detailLoading = ref(false)
const addLoading = ref(false)
const batchLoading = ref(false)
const showDetail = ref(false)
const showAddStudent = ref(false)
const showBatchRegister = ref(false)
const showSettings = ref(false)
const formRef = ref<FormInst | null>(null)

const students = ref<any[]>([])
const selectedClass = ref<number | null>(null)
const classOptions = ref<{ label: string; value: number }[]>([])
const detailData = ref<any>({})

// 批量注册
const batchClassId = ref<number | null>(null)
const batchText = ref('')
const batchResult = ref<any>(null)

// 加减分
const showAdjustScore = ref(false)
const adjustTaskId = ref<number | null>(null)
const adjustValue = ref(0)
const adjustReason = ref('')
const adjustLoading = ref(false)
const adjustingStudentId = ref<number | null>(null)

// 设置
const settings = ref({ student_register_enabled: true, ai_chat_enabled: true, ai_hints_limit: 0, ai_auto_score: true })

const formData = ref({
  username: '',
  password: '',
  name: '',
  student_id: '',
  email: '',
  class_id: null as number | null,
  role: 'student'
})

const rules: FormRules = {
  username: { required: true, message: '请输入用户名', trigger: 'blur' },
  password: { required: true, message: '请输入密码', trigger: 'blur' },
  name: { required: true, message: '请输入姓名', trigger: 'blur' }
}

const pagination = reactive({
  page: 1,
  pageSize: 10,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
  onChange: (page: number) => { pagination.page = page },
  onUpdatePageSize: (pageSize: number) => { pagination.pageSize = pageSize; pagination.page = 1 }
})

const columns = [
  { title: '姓名', key: 'name', render: (row: any) => row.name || '-' },
  { title: '用户名', key: 'username' },
  { title: '学号', key: 'student_id', sorter: (a: any, b: any) => (a.student_id || '').localeCompare(b.student_id || ''), render: (row: any) => row.student_id || '-' },
  { title: '邮箱', key: 'email', render: (row: any) => row.email || '-' },
  { title: '状态', key: 'is_active', render: (row: any) => h(NTag, { type: row.is_active ? 'success' : 'error', size: 'small' }, { default: () => row.is_active ? '正常' : '禁用' }) },
  { title: '操作', key: 'actions', render: (row: any) => h(NButton, { type: 'primary', size: 'small', onClick: () => viewDetail(row) }, { default: () => '查看' }) }
]

const scoreColumns = [
  { title: '任务', key: 'task_title', render: (row: any) => row.task_title || `任务 #${row.task_id}` },
  { title: 'AI 评分', key: 'ai_total_score', render: (row: any) => row.ai_total_score ? `${row.ai_total_score}分` : '-' },
  { title: '老师评分', key: 'teacher_score', render: (row: any) => row.teacher_score ? `${row.teacher_score}分` : '-' },
  { title: '加减分', key: 'bonus_score', render: (row: any) => row.bonus_score ? `${row.bonus_score > 0 ? '+' : ''}${row.bonus_score}分` : '-' },
  { title: '最终分数', key: 'final_score', render: (row: any) => row.final_score ? `${row.final_score}分` : '-' },
  { title: '完成率', key: 'completion_rate', render: (row: any) => row.completion_rate ? `${row.completion_rate}%` : '-' },
  { title: '状态', key: 'status', render: (row: any) => h(NTag, { type: row.status === 'completed' ? 'success' : 'info', size: 'small' }, { default: () => row.status === 'completed' ? '已完成' : '进行中' }) },
  { title: '操作', key: 'actions', width: 100, render: (row: any) => h(NButton, { type: 'warning', size: 'small', onClick: () => openAdjustScore(row.task_id) }, { default: () => '加减分' }) }
]

const batchResultColumns = [
  { title: '学号', key: 'student_id' },
  { title: '姓名', key: 'name' },
  { title: '用户名', key: 'username' },
  { title: '密码', key: 'password', render: (row: any) => h('span', { style: { color: '#d03050', fontWeight: 'bold' } }, row.password) }
]

async function viewDetail(student: any) {
  showDetail.value = true
  detailLoading.value = true
  try {
    const data = await adminApi.getStudentDetail(student.id) as any
    detailData.value = data
  } catch (error) {
    message.error('加载学生详情失败')
  } finally {
    detailLoading.value = false
  }
}

async function handleAddStudent() {
  try {
    await formRef.value?.validate()
    addLoading.value = true
    await authApi.register(formData.value)
    message.success('学生添加成功')
    showAddStudent.value = false
    loadStudents()
  } catch (error: any) {
    message.error(error.detail || '添加失败')
  } finally {
    addLoading.value = false
  }
}

async function handleBatchRegister() {
  if (!batchClassId.value || !batchText.value.trim()) return

  // 解析文本
  const lines = batchText.value.trim().split('\n').filter(l => l.trim())
  const students = lines.map(line => {
    const parts = line.trim().split(/\s+/)
    if (parts.length >= 2) {
      return { student_id: parts[0], name: parts.slice(1).join(' ') }
    }
    return null
  }).filter(Boolean)

  if (students.length === 0) {
    message.warning('请输入有效的学生数据')
    return
  }

  batchLoading.value = true
  try {
    const result = await authApi.batchRegister({
      students: students as any,
      class_id: batchClassId.value
    }) as any
    batchResult.value = result
    message.success(`成功注册 ${result.success} 名学生`)
    loadStudents()
  } catch (error: any) {
    message.error(error.detail || '批量注册失败')
  } finally {
    batchLoading.value = false
  }
}

function exportPasswords() {
  if (!batchResult.value?.students?.length) return

  let csv = '学号,姓名,用户名,密码\n'
  for (const s of batchResult.value.students) {
    csv += `${s.student_id},${s.name},${s.username},${s.password}\n`
  }

  const blob = new Blob(['﻿' + csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `学生账号_${batchResult.value.class_name}_${new Date().toISOString().slice(0, 10)}.csv`
  link.click()
  URL.revokeObjectURL(url)
  message.success('密码列表已导出')
}

async function loadStudents() {
  loading.value = true
  try {
    const data = await adminApi.getStudents(selectedClass.value || undefined) as any
    students.value = data
  } catch (error) {
    console.error('加载学生列表失败', error)
  } finally {
    loading.value = false
  }
}

async function loadClasses() {
  try {
    const data = await authApi.getClasses() as any
    classOptions.value = data.map((c: any) => ({ label: c.name, value: c.id }))
  } catch (error) {
    console.error('加载班级列表失败', error)
  }
}

async function loadSettings() {
  try {
    const data = await authApi.getSettings() as any
    settings.value = data
  } catch (error) {
    console.error('加载设置失败', error)
  }
}

async function saveSettings() {
  try {
    await authApi.updateSettings(settings.value)
    message.success('设置已保存')
  } catch (error: any) {
    message.error(error.detail || '保存失败')
  }
}

function openAdjustScore(taskId?: number) {
  adjustTaskId.value = taskId || null
  adjustValue.value = 0
  adjustReason.value = ''
  adjustingStudentId.value = detailData.value.student?.id
  showAdjustScore.value = true
}

async function handleAdjustScore() {
  if (!adjustingStudentId.value) return
  if (adjustValue.value === 0) {
    message.warning('请输入调整分数')
    return
  }
  adjustLoading.value = true
  try {
    await adminApi.adjustScore(adjustingStudentId.value, {
      task_id: adjustTaskId.value || undefined,
      adjustment: adjustValue.value,
      reason: adjustReason.value
    })
    message.success(`已${adjustValue.value > 0 ? '加' : '减'}${Math.abs(adjustValue.value)}分`)
    showAdjustScore.value = false
    // 刷新详情
    const data = await adminApi.getStudentDetail(adjustingStudentId.value) as any
    detailData.value = data
  } catch (error: any) {
    message.error(error.detail || '操作失败')
  } finally {
    adjustLoading.value = false
  }
}

onMounted(() => {
  loadClasses()
  loadStudents()
  loadSettings()
})
</script>

<style scoped>
.students-container {
  max-width: 1200px;
  margin: 0 auto;
}
</style>
