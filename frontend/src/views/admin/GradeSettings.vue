<template>
  <div class="grade-settings-container">
    <h2 class="page-title">成绩设置</h2>

    <!-- 学生查看成绩开关 -->
    <n-card title="学生权限" style="margin-bottom: 20px;">
      <n-descriptions bordered :column="1">
        <n-descriptions-item label="学生查看成绩">
          <n-switch v-model:value="studentViewGrades" @update:value="saveViewSetting" />
          <span style="margin-left: 12px; color: #666;">
            {{ studentViewGrades ? '已开启 - 学生可查看个人成绩' : '已关闭 - 学生无法查看任何成绩' }}
          </span>
        </n-descriptions-item>
      </n-descriptions>
    </n-card>

    <!-- 成绩方案列表 -->
    <n-card title="成绩方案" style="margin-bottom: 20px;">
      <template #header-extra>
        <n-button type="primary" size="small" @click="openCreateScheme">新建方案</n-button>
      </template>
      <n-data-table :columns="schemeColumns" :data="schemes" :bordered="false" />
    </n-card>

    <!-- 当前方案的计分项目 -->
    <n-card v-if="currentScheme" :title="`计分项目 - ${currentScheme.name}`">
      <template #header-extra>
        <n-space>
          <n-tag :type="weightTotal === 100 ? 'success' : 'error'" size="small">
            权重总计: {{ weightTotal }}%
          </n-tag>
          <n-button type="primary" size="small" :disabled="!currentScheme" @click="openCreateItem">添加项目</n-button>
        </n-space>
      </template>
      <n-data-table :columns="itemColumns" :data="currentItems" :bordered="false" />
    </n-card>

    <!-- 创建/编辑方案弹窗 -->
    <n-modal v-model:show="showSchemeModal" preset="card" :title="editingScheme ? '编辑方案' : '新建方案'" style="width: 500px">
      <n-form label-placement="left" label-width="80">
        <n-form-item label="方案名称">
          <n-input v-model:value="schemeForm.name" placeholder="如：2024春季方案" />
        </n-form-item>
        <n-form-item label="关联班级">
          <n-select v-model:value="schemeForm.class_id" :options="classOptions" placeholder="不关联则通用" clearable />
        </n-form-item>
        <n-form-item label="小数位数">
          <n-input-number v-model:value="schemeForm.decimal_places" :min="0" :max="3" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showSchemeModal = false">取消</n-button>
          <n-button type="primary" @click="handleSaveScheme">保存</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 创建/编辑计分项目弹窗 -->
    <n-modal v-model:show="showItemModal" preset="card" :title="editingItem ? '编辑项目' : '添加项目'" style="width: 500px">
      <n-form label-placement="left" label-width="80">
        <n-form-item label="项目名称">
          <n-input v-model:value="itemForm.name" placeholder="如：平时分、考试分、实践分" />
        </n-form-item>
        <n-form-item label="权重">
          <n-space align="center">
            <n-input-number v-model:value="itemForm.weight" :min="0" :max="100" style="width: 120px;" />
            <span>%</span>
            <n-tag :type="itemForm.weight + otherWeightTotal <= 100 ? 'success' : 'error'" size="small">
              合计: {{ itemForm.weight + otherWeightTotal }}%
            </n-tag>
          </n-space>
        </n-form-item>
        <n-form-item label="满分上限">
          <n-input-number v-model:value="itemForm.max_score" :min="1" :max="1000" />
        </n-form-item>
        <n-form-item label="排序">
          <n-input-number v-model:value="itemForm.sort_order" :min="0" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showItemModal = false">取消</n-button>
          <n-button type="primary" :disabled="itemForm.weight + otherWeightTotal > 100" @click="handleSaveItem">保存</n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue'
import { useMessage, useDialog } from 'naive-ui'
import { NButton, NTag, NSpace } from 'naive-ui'
import { adminApi, authApi } from '@/api'

const message = useMessage()
const dialog = useDialog()
const schemes = ref<any[]>([])
const currentScheme = ref<any>(null)
const currentItems = ref<any[]>([])
const classOptions = ref<{ label: string; value: number }[]>([])
const showSchemeModal = ref(false)
const showItemModal = ref(false)
const editingScheme = ref<any>(null)
const editingItem = ref<any>(null)
const studentViewGrades = ref(true)

const schemeForm = ref({ name: '', class_id: null as number | null, decimal_places: 1 })
const itemForm = ref({ name: '', weight: 10, max_score: 100, sort_order: 0 })

const weightTotal = computed(() => currentItems.value.reduce((sum, i) => sum + i.weight, 0))
const otherWeightTotal = computed(() => {
  if (editingItem.value) {
    return currentItems.value.filter(i => i.id !== editingItem.value.id).reduce((sum, i) => sum + i.weight, 0)
  }
  return weightTotal.value
})

const schemeColumns = [
  { title: '方案名称', key: 'name' },
  { title: '关联班级', key: 'class_name', render: (row: any) => row.class_name || '通用' },
  { title: '小数位数', key: 'decimal_places', width: 80 },
  { title: '权重总计', key: 'weight_total', width: 80, render: (row: any) => h(NTag, { type: row.weight_total === 100 ? 'success' : row.weight_total > 0 ? 'warning' : 'default', size: 'small' }, { default: () => `${row.weight_total}%` }) },
  { title: '状态', key: 'is_active', width: 80, render: (row: any) => h(NTag, { type: row.is_active ? 'success' : 'default', size: 'small' }, { default: () => row.is_active ? '已激活' : '未激活' }) },
  { title: '操作', key: 'actions', width: 260, render: (row: any) => h(NSpace, { size: 'small' }, { default: () => [
    h(NButton, { type: 'info', size: 'small', onClick: () => selectScheme(row) }, { default: () => '项目' }),
    h(NButton, { type: row.is_active ? 'success' : 'warning', size: 'small', onClick: () => handleActivate(row) }, { default: () => row.is_active ? '已激活' : '激活' }),
    h(NButton, { type: 'primary', size: 'small', onClick: () => openEditScheme(row) }, { default: () => '编辑' }),
    h(NButton, { type: 'error', size: 'small', onClick: () => handleDeleteScheme(row) }, { default: () => '删除' })
  ] }) }
]

const itemColumns = [
  { title: '排序', key: 'sort_order', width: 60 },
  { title: '项目名称', key: 'name' },
  { title: '权重', key: 'weight', width: 80, render: (row: any) => `${row.weight}%` },
  { title: '满分', key: 'max_score', width: 80 },
  { title: '操作', key: 'actions', width: 140, render: (row: any) => h(NSpace, { size: 'small' }, { default: () => [
    h(NButton, { type: 'primary', size: 'small', onClick: () => openEditItem(row) }, { default: () => '编辑' }),
    h(NButton, { type: 'error', size: 'small', onClick: () => handleDeleteItem(row) }, { default: () => '删除' })
  ] }) }
]

function selectScheme(scheme: any) {
  currentScheme.value = scheme
  currentItems.value = scheme.items || []
}

function openCreateScheme() {
  editingScheme.value = null
  schemeForm.value = { name: '', class_id: null, decimal_places: 1 }
  showSchemeModal.value = true
}

function openEditScheme(scheme: any) {
  editingScheme.value = scheme
  schemeForm.value = { name: scheme.name, class_id: scheme.class_id, decimal_places: scheme.decimal_places }
  showSchemeModal.value = true
}

function openCreateItem() {
  editingItem.value = null
  const nextOrder = currentItems.value.length
  itemForm.value = { name: '', weight: 10, max_score: 100, sort_order: nextOrder }
  showItemModal.value = true
}

function openEditItem(item: any) {
  editingItem.value = item
  itemForm.value = { name: item.name, weight: item.weight, max_score: item.max_score, sort_order: item.sort_order }
  showItemModal.value = true
}

async function handleSaveScheme() {
  if (!schemeForm.value.name) { message.warning('请输入方案名称'); return }
  try {
    if (editingScheme.value) {
      await adminApi.updateGradeScheme(editingScheme.value.id, schemeForm.value)
      message.success('方案更新成功')
    } else {
      await adminApi.createGradeScheme(schemeForm.value)
      message.success('方案创建成功')
    }
    showSchemeModal.value = false
    await loadSchemes()
  } catch (e: any) { message.error(e.detail || '操作失败') }
}

async function handleSaveItem() {
  if (!itemForm.value.name) { message.warning('请输入项目名称'); return }
  if (itemForm.value.weight + otherWeightTotal.value > 100) { message.warning('权重总和不能超过100%'); return }
  try {
    if (editingItem.value) {
      await adminApi.updateGradeItem(editingItem.value.id, itemForm.value)
      message.success('项目更新成功')
    } else {
      await adminApi.createGradeItem(currentScheme.value.id, itemForm.value)
      message.success('项目添加成功')
    }
    showItemModal.value = false
    await loadSchemes()
    if (currentScheme.value) {
      const updated = schemes.value.find(s => s.id === currentScheme.value.id)
      if (updated) selectScheme(updated)
    }
  } catch (e: any) { message.error(e.detail || '操作失败') }
}

async function handleActivate(scheme: any) {
  try {
    await adminApi.activateGradeScheme(scheme.id)
    message.success(`方案 "${scheme.name}" 已激活`)
    await loadSchemes()
  } catch (e: any) { message.error(e.detail || '操作失败') }
}

async function handleDeleteScheme(scheme: any) {
  dialog.warning({
    title: '确认删除', content: `确定删除方案 "${scheme.name}" 及其所有计分项目？`,
    positiveText: '删除', negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await adminApi.deleteGradeScheme(scheme.id)
        message.success('方案已删除')
        if (currentScheme.value?.id === scheme.id) { currentScheme.value = null; currentItems.value = [] }
        await loadSchemes()
      } catch (e: any) { message.error(e.detail || '删除失败') }
    }
  })
}

async function handleDeleteItem(item: any) {
  dialog.warning({
    title: '确认删除', content: `确定删除计分项目 "${item.name}"？`,
    positiveText: '删除', negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await adminApi.deleteGradeItem(item.id)
        message.success('项目已删除')
        await loadSchemes()
        if (currentScheme.value) {
          const updated = schemes.value.find(s => s.id === currentScheme.value.id)
          if (updated) selectScheme(updated)
        }
      } catch (e: any) { message.error(e.detail || '删除失败') }
    }
  })
}

async function saveViewSetting() {
  try {
    await authApi.updateSettings({ student_view_grades: studentViewGrades.value })
    message.success('设置已保存')
  } catch (e: any) { message.error(e.detail || '保存失败') }
}

async function loadSchemes() {
  try {
    schemes.value = await adminApi.getGradeSchemes() as any
  } catch (error: any) {
    message.error(error?.detail || '加载成绩方案失败')
  }
}

async function loadClasses() {
  try {
    const data = await authApi.getClasses() as any
    classOptions.value = data.map((c: any) => ({ label: c.name, value: c.id }))
  } catch (error: any) {
    message.error(error?.detail || '加载班级列表失败')
  }
}

async function loadSettings() {
  try {
    const data = await authApi.getSettings() as any
    studentViewGrades.value = data.student_view_grades !== false
  } catch (error: any) {
    message.error(error?.detail || '加载设置失败')
  }
}

onMounted(() => {
  loadSchemes()
  loadClasses()
  loadSettings()
})
</script>

<style scoped>
.grade-settings-container { max-width: 1200px; margin: 0 auto; }
.page-title { margin: 0 0 24px; font-size: 20px; }
</style>
