<template>
  <div class="score-entry-container">
    <h2 style="margin: 0 0 24px; font-size: 20px;">评分明录</h2>

    <!-- 选择区域 -->
    <n-card style="margin-bottom: 20px;">
      <n-space align="center" wrap>
        <n-select
          v-model:value="selectedTemplateId"
          :options="templateOptions"
          placeholder="选择评价模板"
          clearable
          style="width: 240px;"
          @update:value="handleTemplateChange"
        />
        <n-select
          v-model:value="selectedPhaseId"
          :options="phaseOptions"
          placeholder="选择阶段"
          clearable
          style="width: 160px;"
          :disabled="!selectedTemplateId"
          @update:value="handlePhaseChange"
        />
        <n-select
          v-model:value="selectedIndicatorId"
          :options="indicatorOptions"
          placeholder="选择指标"
          clearable
          style="width: 200px;"
          :disabled="!selectedPhaseId"
          @update:value="handleIndicatorChange"
        />
      </n-space>
      <div v-if="currentIndicator" style="margin-top: 12px; color: #666; font-size: 13px;">
        <n-space>
          <n-tag size="small" type="info">权重: {{ currentIndicator.weight }}%</n-tag>
          <n-tag size="small">满分: {{ currentIndicator.max_score }}</n-tag>
          <n-tag size="small" v-for="sc in currentScorerConfigs" :key="sc.scorer_role" type="warning">
            {{ scorerRoleMap[sc.scorer_role] || sc.scorer_role }} ({{ sc.weight }}%)
          </n-tag>
        </n-space>
      </div>
    </n-card>

    <!-- 学生评分表格 -->
    <n-card v-if="selectedIndicatorId">
      <template #header>
        <n-space align="center" justify="space-between" style="width: 100%;">
          <span>{{ currentIndicator?.name || '评分' }}</span>
          <n-space>
            <n-tag type="success" size="small">已评 {{ scoredCount }}/{{ students.length }}</n-tag>
            <n-button type="primary" :loading="saving" :disabled="!hasChanges" @click="handleBatchSave">
              批量保存
            </n-button>
          </n-space>
        </n-space>
      </template>

      <n-spin :show="loadingStudents">
        <n-data-table
          :columns="columns"
          :data="studentRows"
          :bordered="true"
          :single-line="false"
          :pagination="{ pageSize: 50 }"
          :row-key="(row: any) => row.student_id"
        />
      </n-spin>
    </n-card>

    <n-empty v-else description="请先选择模板 → 阶段 → 指标，然后为学生录入分数" style="padding: 80px 0;" />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue'
import { useMessage, NInputNumber, NTag, NButton } from 'naive-ui'
import { evalApi, adminApi } from '@/api'

const message = useMessage()

const scorerRoleMap: Record<string, string> = {
  teacher: '教师', ai: 'AI', self: '自评', peer: '互评', enterprise: '企业导师', system: '系统'
}

// --- 状态 ---
const loadingStudents = ref(false)
const saving = ref(false)
const templates = ref<any[]>([])
const currentTemplate = ref<any>(null)
const currentIndicator = ref<any>(null)
const currentScorerConfigs = ref<any[]>([])
const students = ref<any[]>([])

const selectedTemplateId = ref<number | null>(null)
const selectedPhaseId = ref<number | null>(null)
const selectedIndicatorId = ref<number | null>(null)

// 学生评分数据 { student_id: score }
const scoreMap = ref<Record<number, number | null>>({})
const remarkMap = ref<Record<number, string>>({})
const changedIds = ref<Set<number>>(new Set())

// --- 选项 ---
const templateOptions = computed(() =>
  templates.value.map((t: any) => ({ label: `${t.name}${t.is_active ? ' (已激活)' : ''}`, value: t.id }))
)

const phaseOptions = computed(() => {
  if (!currentTemplate.value?.phases) return []
  return currentTemplate.value.phases.map((p: any) => ({ label: `${p.name} (${p.weight}%)`, value: p.id }))
})

const indicatorOptions = computed(() => {
  if (!selectedPhaseId.value || !currentTemplate.value?.phases) return []
  const phase = currentTemplate.value.phases.find((p: any) => p.id === selectedPhaseId.value)
  if (!phase?.indicators) return []
  return phase.indicators.map((i: any) => ({ label: `${i.name} (${i.weight}%)`, value: i.id }))
})

const hasChanges = computed(() => changedIds.value.size > 0)

const scoredCount = computed(() =>
  students.value.filter(s => scoreMap.value[s.student_id] != null).length
)

// --- 表格列 ---
const columns = [
  { title: '学号', key: 'username', width: 120 },
  { title: '姓名', key: 'student_name', width: 120 },
  {
    title: '当前分数',
    key: 'latest_score',
    width: 100,
    render: (row: any) => {
      if (row.latest_score == null) return h('span', { style: 'color: #ccc;' }, '--')
      return h('span', { style: 'font-weight: 600;' }, `${row.latest_score}`)
    }
  },
  {
    title: '录入分数',
    key: 'score_input',
    width: 160,
    render: (row: any) => {
      return h(NInputNumber, {
        value: scoreMap.value[row.student_id],
        min: 0,
        max: currentIndicator.value?.max_score || 100,
        size: 'small',
        placeholder: '输入分数',
        onUpdateValue: (val: number | null) => {
          scoreMap.value[row.student_id] = val
          changedIds.value.add(row.student_id)
        }
      })
    }
  },
  {
    title: '评语',
    key: 'remark',
    width: 200,
    render: (row: any) => {
      return h('input', {
        value: remarkMap.value[row.student_id] || '',
        placeholder: '可选',
        style: 'width: 100%; padding: 4px 8px; border: 1px solid #e0e0e0; border-radius: 4px; font-size: 13px;',
        onInput: (e: Event) => {
          remarkMap.value[row.student_id] = (e.target as HTMLInputElement).value
          changedIds.value.add(row.student_id)
        }
      })
    }
  },
  {
    title: '来源',
    key: 'latest_scorer_role',
    width: 80,
    render: (row: any) => {
      if (!row.latest_scorer_role) return '-'
      return h(NTag, { size: 'small', type: 'info' }, { default: () => scorerRoleMap[row.latest_scorer_role] || row.latest_scorer_role })
    }
  }
]

const studentRows = computed(() => students.value)

// --- 加载 ---
async function loadTemplates() {
  try {
    const res = await evalApi.getTemplates() as any
    templates.value = Array.isArray(res) ? res : []
  } catch (e: any) {
    message.error('加载模板失败')
  }
}

async function handleTemplateChange(id: number | null) {
  selectedPhaseId.value = null
  selectedIndicatorId.value = null
  currentTemplate.value = null
  currentIndicator.value = null
  students.value = []
  if (!id) return
  try {
    currentTemplate.value = await evalApi.getTemplate(id) as any
  } catch {
    message.error('加载模板详情失败')
  }
}

function handlePhaseChange() {
  selectedIndicatorId.value = null
  currentIndicator.value = null
  students.value = []
}

async function handleIndicatorChange(id: number | null) {
  currentIndicator.value = null
  students.value = []
  scoreMap.value = {}
  remarkMap.value = {}
  changedIds.value = new Set()
  if (!id) return
  // 获取指标详情
  if (currentTemplate.value?.phases) {
    for (const phase of currentTemplate.value.phases) {
      const ind = phase.indicators?.find((i: any) => i.id === id)
      if (ind) {
        currentIndicator.value = ind
        currentScorerConfigs.value = ind.scorer_configs || []
        break
      }
    }
  }
  // 加载学生列表
  loadingStudents.value = true
  try {
    const res = await evalApi.getIndicatorStudents(id) as any
    students.value = res.students || []
    // 初始化 scoreMap
    for (const s of students.value) {
      scoreMap.value[s.student_id] = s.latest_score ?? null
      remarkMap.value[s.student_id] = s.latest_remark || ''
    }
  } catch {
    message.error('加载学生列表失败')
  } finally {
    loadingStudents.value = false
  }
}

// --- 保存 ---
async function handleBatchSave() {
  if (!selectedIndicatorId.value || !selectedTemplateId.value) return
  const records: any[] = []
  for (const sid of changedIds.value) {
    const score = scoreMap.value[sid]
    if (score != null) {
      records.push({
        student_id: sid,
        score: score,
        remark: remarkMap.value[sid] || ''
      })
    }
  }
  if (records.length === 0) {
    message.warning('没有需要保存的分数')
    return
  }
  saving.value = true
  try {
    await evalApi.batchCreateRecords({
      template_id: selectedTemplateId.value,
      indicator_id: selectedIndicatorId.value,
      records: records
    })
    message.success(`成功保存 ${records.length} 条评分`)
    changedIds.value = new Set()
    // 刷新学生列表
    const res = await evalApi.getIndicatorStudents(selectedIndicatorId.value) as any
    students.value = res.students || []
  } catch (e: any) {
    message.error(e?.detail || '保存失败')
  } finally {
    saving.value = false
  }
}

onMounted(() => {
  loadTemplates()
})
</script>

<style scoped>
.score-entry-container {
  max-width: 1200px;
  margin: 0 auto;
}
</style>
