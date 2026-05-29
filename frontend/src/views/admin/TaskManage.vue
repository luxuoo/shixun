<template>
  <div class="task-manage-container">
    <n-space justify="space-between" align="center" style="margin-bottom: 24px;">
      <h2>任务管理</h2>
      <n-space>
        <n-button type="success" @click="openAiDecompose">
          AI 智能创建
        </n-button>
        <n-button type="primary" @click="openCreateTask">
          手动创建
        </n-button>
      </n-space>
    </n-space>

    <n-card>
      <n-data-table
        :columns="columns"
        :data="tasks"
        :loading="loading"
        :bordered="false"
      />
    </n-card>

    <!-- AI 智能创建弹窗 -->
    <n-modal v-model:show="showAiModal" preset="card" title="AI 智能创建任务" style="width: 700px">
      <n-space vertical :size="16">
        <n-alert type="info">
          描述你想要的实训任务，AI 会自动分解为多个步骤。你可以预览后再发布。
        </n-alert>
        <n-form label-placement="left" label-width="80">
          <n-form-item label="任务名称">
            <n-input v-model:value="aiForm.title" placeholder="例如：基于 YOLO 的智慧交通系统" />
          </n-form-item>
          <n-form-item label="任务描述">
            <n-input v-model:value="aiForm.description" type="textarea" placeholder="详细描述任务目标、技术栈、预期成果等..." :rows="4" />
          </n-form-item>
          <n-grid :cols="2" :x-gap="16">
            <n-gi>
              <n-form-item label="分类">
                <n-select v-model:value="aiForm.category" :options="categoryOptions" placeholder="选择分类" />
              </n-form-item>
            </n-gi>
            <n-gi>
              <n-form-item label="难度">
                <n-rate v-model:value="aiForm.difficulty" :count="5" />
              </n-form-item>
            </n-gi>
            <n-gi>
              <n-form-item label="详细度">
                <n-select v-model:value="aiForm.detail_level" :options="detailLevelOptions" />
              </n-form-item>
            </n-gi>
            <n-gi>
              <n-form-item label="步骤数">
                <n-input-number v-model:value="aiForm.steps_count" :min="0" :max="20" placeholder="0=自动" />
              </n-form-item>
            </n-gi>
          </n-grid>
        </n-form>

        <!-- AI 分解结果预览 -->
        <div v-if="aiResult">
          <n-divider>AI 分解结果</n-divider>
          <n-descriptions bordered :column="2" style="margin-bottom: 16px;">
            <n-descriptions-item label="标题">{{ aiResult.title }}</n-descriptions-item>
            <n-descriptions-item label="分类">{{ aiResult.category }}</n-descriptions-item>
            <n-descriptions-item label="难度">{{ aiResult.difficulty }}星</n-descriptions-item>
            <n-descriptions-item label="预计时长">{{ aiResult.estimated_hours }}小时</n-descriptions-item>
          </n-descriptions>
          <n-data-table
            :columns="previewStepColumns"
            :data="aiResult.steps || []"
            :bordered="false"
            :max-height="300"
          />
        </div>
      </n-space>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showAiModal = false">取消</n-button>
          <n-button type="info" :loading="aiLoading" @click="handleAiDecompose(false)">
            仅预览
          </n-button>
          <n-button type="success" :loading="aiLoading" @click="handleAiDecompose(true)">
            分解并发布
          </n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 手动创建/编辑任务弹窗 -->
    <n-modal v-model:show="showTaskModal" preset="card" :title="editingTask ? '编辑任务' : '创建任务'" style="width: 700px">
      <n-form ref="formRef" :model="formData" :rules="rules" label-placement="left" label-width="100">
        <n-form-item label="任务名称" path="title">
          <n-input v-model:value="formData.title" placeholder="请输入任务名称" />
        </n-form-item>
        <n-form-item label="任务描述" path="description">
          <n-input v-model:value="formData.description" type="textarea" placeholder="请输入任务描述" :rows="4" />
        </n-form-item>
        <n-grid :cols="2" :x-gap="16">
          <n-gi>
            <n-form-item label="分类" path="category">
              <n-select v-model:value="formData.category" :options="categoryOptions" placeholder="选择分类" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="难度" path="difficulty">
              <n-rate v-model:value="formData.difficulty" :count="5" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="步骤数" path="total_steps">
              <n-input-number v-model:value="formData.total_steps" :min="1" :max="20" />
            </n-form-item>
          </n-gi>
          <n-gi>
            <n-form-item label="预计时长" path="estimated_hours">
              <n-input-number v-model:value="formData.estimated_hours" :min="0.5" :max="100" :step="0.5" />
            </n-form-item>
          </n-gi>
        </n-grid>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showTaskModal = false">取消</n-button>
          <n-button type="primary" :loading="saveLoading" @click="handleSaveTask">
            {{ editingTask ? '保存' : '创建' }}
          </n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 步骤管理弹窗 -->
    <n-modal v-model:show="showSteps" preset="card" title="步骤管理" style="width: 900px">
      <n-space vertical :size="16">
        <n-button type="primary" @click="openAddStep">添加步骤</n-button>
        <n-data-table :columns="stepColumns" :data="steps" :bordered="false" />
      </n-space>
    </n-modal>

    <!-- 添加/编辑步骤弹窗 -->
    <n-modal v-model:show="showStepModal" preset="card" :title="editingStep ? '编辑步骤' : '添加步骤'" style="width: 700px">
      <n-form ref="stepFormRef" :model="stepFormData" :rules="stepRules" label-placement="left" label-width="100">
        <n-form-item label="步骤序号" path="step_order">
          <n-input-number v-model:value="stepFormData.step_order" :min="1" />
        </n-form-item>
        <n-form-item label="步骤标题" path="title">
          <n-input v-model:value="stepFormData.title" placeholder="请输入步骤标题" />
        </n-form-item>
        <n-form-item label="步骤描述" path="description">
          <n-input v-model:value="stepFormData.description" type="textarea" placeholder="请输入步骤描述" :rows="3" />
        </n-form-item>
        <n-form-item label="具体要求" path="requirements">
          <n-input v-model:value="stepFormData.requirements" type="textarea" placeholder="请输入具体要求" :rows="3" />
        </n-form-item>
        <n-form-item label="预期输出" path="expected_output">
          <n-input v-model:value="stepFormData.expected_output" type="textarea" placeholder="请输入预期输出" :rows="2" />
        </n-form-item>
        <n-form-item label="提示次数" path="hints_available">
          <n-input-number v-model:value="stepFormData.hints_available" :min="1" :max="10" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showStepModal = false">取消</n-button>
          <n-button type="primary" :loading="saveStepLoading" @click="handleSaveStep">
            {{ editingStep ? '保存' : '添加' }}
          </n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import { useMessage, useDialog } from 'naive-ui'
import type { FormInst, FormRules } from 'naive-ui'
import { NButton, NTag, NSpace } from 'naive-ui'
import { taskApi } from '@/api'

const message = useMessage()
const dialog = useDialog()
const loading = ref(false)
const saveLoading = ref(false)
const saveStepLoading = ref(false)
const aiLoading = ref(false)
const showTaskModal = ref(false)
const showSteps = ref(false)
const showStepModal = ref(false)
const showAiModal = ref(false)
const formRef = ref<FormInst | null>(null)
const stepFormRef = ref<FormInst | null>(null)

const tasks = ref<any[]>([])
const steps = ref<any[]>([])
const selectedTaskId = ref<number | null>(null)
const editingTask = ref<any>(null)
const editingStep = ref<any>(null)
const aiResult = ref<any>(null)

const aiForm = ref({
  title: '',
  description: '',
  category: null as string | null,
  difficulty: 3,
  detail_level: 'normal',
  steps_count: 0
})

const detailLevelOptions = [
  { label: '简洁 - 要求简短精炼', value: 'brief' },
  { label: '标准 - 适中详细', value: 'normal' },
  { label: '详细 - 包含技术方案和检查点', value: 'detailed' }
]

const formData = ref({
  title: '',
  description: '',
  category: null as string | null,
  difficulty: 1,
  total_steps: 5,
  estimated_hours: 4
})

const stepFormData = ref({
  step_order: 1,
  title: '',
  description: '',
  requirements: '',
  expected_output: '',
  hints_available: 3
})

const rules: FormRules = {
  title: { required: true, message: '请输入任务名称', trigger: 'blur' },
  total_steps: { required: true, type: 'number', message: '请输入步骤数', trigger: 'blur' }
}

const stepRules: FormRules = {
  title: { required: true, message: '请输入步骤标题', trigger: 'blur' },
  step_order: { required: true, type: 'number', message: '请输入步骤序号', trigger: 'blur' }
}

const categoryOptions = [
  { label: 'Python', value: 'Python' },
  { label: 'Web', value: 'Web' },
  { label: 'YOLO', value: 'YOLO' },
  { label: '数据分析', value: '数据分析' },
  { label: '机器学习', value: '机器学习' }
]

const columns = [
  { title: 'ID', key: 'id', width: 60 },
  { title: '任务名称', key: 'title' },
  { title: '分类', key: 'category', render: (row: any) => h(NTag, { type: 'info', size: 'small' }, { default: () => row.category || '未分类' }) },
  { title: '难度', key: 'difficulty', render: (row: any) => h(NTag, { type: row.difficulty <= 2 ? 'success' : row.difficulty <= 3 ? 'warning' : 'error', size: 'small' }, { default: () => `${row.difficulty}星` }) },
  { title: '步骤数', key: 'total_steps' },
  { title: '状态', key: 'is_active', render: (row: any) => h(NTag, { type: row.is_active ? 'success' : 'error', size: 'small' }, { default: () => row.is_active ? '启用' : '禁用' }) },
  {
    title: '操作', key: 'actions', width: 280,
    render: (row: any) => h(NSpace, { size: 'small' }, {
      default: () => [
        h(NButton, { type: 'primary', size: 'small', onClick: () => manageSteps(row) }, { default: () => '步骤' }),
        h(NButton, { type: 'info', size: 'small', onClick: () => openEditTask(row) }, { default: () => '编辑' }),
        h(NButton, { type: row.is_active ? 'warning' : 'success', size: 'small', onClick: () => toggleTask(row) }, { default: () => row.is_active ? '禁用' : '启用' }),
        h(NButton, { type: 'error', size: 'small', onClick: () => confirmDeleteTask(row) }, { default: () => '删除' })
      ]
    })
  }
]

const stepColumns = [
  { title: '序号', key: 'step_order', width: 80 },
  { title: '标题', key: 'title' },
  { title: '提示次数', key: 'hints_available', width: 100 },
  {
    title: '操作', key: 'actions', width: 160,
    render: (row: any) => h(NSpace, { size: 'small' }, {
      default: () => [
        h(NButton, { type: 'info', size: 'small', onClick: () => openEditStep(row) }, { default: () => '编辑' }),
        h(NButton, { type: 'error', size: 'small', onClick: () => confirmDeleteStep(row) }, { default: () => '删除' })
      ]
    })
  }
]

const previewStepColumns = [
  { title: '序号', key: 'step_order', width: 60 },
  { title: '标题', key: 'title', width: 150 },
  { title: '描述', key: 'description', ellipsis: { tooltip: true } },
  { title: '要求', key: 'requirements', ellipsis: { tooltip: true } }
]

function openCreateTask() {
  editingTask.value = null
  formData.value = { title: '', description: '', category: null, difficulty: 1, total_steps: 5, estimated_hours: 4 }
  showTaskModal.value = true
}

function openAiDecompose() {
  aiForm.value = { title: '', description: '', category: null, difficulty: 3, detail_level: 'normal', steps_count: 0 }
  aiResult.value = null
  showAiModal.value = true
}

function openEditTask(task: any) {
  editingTask.value = task
  formData.value = { title: task.title, description: task.description || '', category: task.category, difficulty: task.difficulty, total_steps: task.total_steps, estimated_hours: task.estimated_hours || 4 }
  showTaskModal.value = true
}

function openAddStep() {
  editingStep.value = null
  stepFormData.value = { step_order: (steps.value.length || 0) + 1, title: '', description: '', requirements: '', expected_output: '', hints_available: 3 }
  showStepModal.value = true
}

function openEditStep(step: any) {
  editingStep.value = step
  stepFormData.value = { step_order: step.step_order, title: step.title, description: step.description || '', requirements: step.requirements || '', expected_output: step.expected_output || '', hints_available: step.hints_available || 3 }
  showStepModal.value = true
}

async function manageSteps(task: any) {
  selectedTaskId.value = task.id
  showSteps.value = true
  await loadSteps(task.id)
}

async function loadTasks() {
  loading.value = true
  try {
    const data = await taskApi.getList() as any
    tasks.value = data
  } catch (error) {
    console.error('加载任务列表失败', error)
  } finally {
    loading.value = false
  }
}

async function loadSteps(taskId: number) {
  try {
    const data = await taskApi.getSteps(taskId) as any
    steps.value = data
  } catch (error) {
    console.error('加载步骤列表失败', error)
  }
}

async function handleAiDecompose(autoPublish: boolean) {
  if (!aiForm.value.title || !aiForm.value.description) {
    message.warning('请填写任务名称和描述')
    return
  }
  aiLoading.value = true
  try {
    const result = await taskApi.aiDecompose({
      title: aiForm.value.title,
      description: aiForm.value.description,
      category: aiForm.value.category || undefined,
      difficulty: aiForm.value.difficulty,
      auto_publish: autoPublish,
      detail_level: aiForm.value.detail_level,
      steps_count: aiForm.value.steps_count || undefined
    }) as any

    if (result.success) {
      if (result.published) {
        message.success(result.message || '任务已创建并发布')
        showAiModal.value = false
        loadTasks()
      } else {
        aiResult.value = result.data
        message.info('分解完成，请预览后选择发布')
      }
    }
  } catch (error: any) {
    message.error(error.detail || 'AI 分解失败')
  } finally {
    aiLoading.value = false
  }
}

async function handleSaveTask() {
  try {
    await formRef.value?.validate()
    saveLoading.value = true
    if (editingTask.value) {
      await taskApi.update(editingTask.value.id, formData.value)
      message.success('任务更新成功')
    } else {
      await taskApi.create(formData.value)
      message.success('任务创建成功')
    }
    showTaskModal.value = false
    loadTasks()
  } catch (error: any) {
    message.error(error.detail || '操作失败')
  } finally {
    saveLoading.value = false
  }
}

async function handleSaveStep() {
  if (!selectedTaskId.value) return
  try {
    await stepFormRef.value?.validate()
    saveStepLoading.value = true
    if (editingStep.value) {
      await taskApi.updateStep(selectedTaskId.value, editingStep.value.id, stepFormData.value)
      message.success('步骤更新成功')
    } else {
      await taskApi.createStep(selectedTaskId.value, stepFormData.value)
      message.success('步骤添加成功')
    }
    showStepModal.value = false
    loadSteps(selectedTaskId.value)
  } catch (error: any) {
    message.error(error.detail || '操作失败')
  } finally {
    saveStepLoading.value = false
  }
}

async function toggleTask(task: any) {
  try {
    await taskApi.update(task.id, { is_active: !task.is_active })
    message.success(`任务已${task.is_active ? '禁用' : '启用'}`)
    loadTasks()
  } catch (error: any) {
    message.error(error.detail || '操作失败')
  }
}

function confirmDeleteTask(task: any) {
  dialog.warning({
    title: '确认删除',
    content: `确定要删除任务"${task.title}"吗？关联的所有数据（步骤、提交、评分）都将被删除。`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await taskApi.delete(task.id)
        message.success('任务已删除')
        loadTasks()
      } catch (error: any) {
        message.error(error.detail || '删除失败')
      }
    }
  })
}

function confirmDeleteStep(step: any) {
  dialog.warning({
    title: '确认删除',
    content: `确定要删除步骤"${step.title}"吗？`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      if (!selectedTaskId.value) return
      try {
        await taskApi.deleteStep(selectedTaskId.value, step.id)
        message.success('步骤已删除')
        loadSteps(selectedTaskId.value)
      } catch (error: any) {
        message.error(error.detail || '删除失败')
      }
    }
  })
}

onMounted(() => {
  loadTasks()
})
</script>

<style scoped>
.task-manage-container {
  max-width: 1200px;
  margin: 0 auto;
}
</style>
