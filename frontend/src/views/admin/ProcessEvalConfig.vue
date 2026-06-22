<template>
  <div class="process-eval-config">
    <h2 class="page-title">过程性评价配置</h2>

    <!-- 权重校验提示 -->
    <n-alert
      v-if="currentTemplate"
      :type="weightValidation.valid ? 'success' : 'error'"
      :title="weightValidation.valid ? '权重校验通过' : '权重校验未通过'"
      style="margin-bottom: 16px;"
    >
      <template v-if="weightValidation.valid">
        所有阶段权重合计 100%，配置正确。
      </template>
      <template v-else>
        <div>阶段权重合计 {{ weightValidation.phase_total }}%，需为 100%。</div>
        <div v-for="(msg, idx) in weightValidation.messages" :key="idx">{{ msg }}</div>
      </template>
    </n-alert>

    <!-- 顶部操作栏 -->
    <n-card title="模板管理" style="margin-bottom: 20px;">
      <n-space align="center" wrap>
        <n-select
          v-model:value="selectedTemplateId"
          :options="templateOptions"
          placeholder="选择评价模板"
          clearable
          style="width: 280px;"
          @update:value="handleTemplateChange"
        />
        <n-button type="primary" @click="openCreateTemplate">新建模板</n-button>
        <n-button type="info" @click="openAiGenerateTemplate">AI 生成模板</n-button>
        <n-popconfirm @positive-click="handleInitDefault">
          <template #trigger>
            <n-button type="warning">初始化默认模板</n-button>
          </template>
          确定要初始化默认评价模板吗？这将创建一套标准的课前/课中/课后评价体系。
        </n-popconfirm>
        <n-button
          v-if="selectedTemplateId"
          type="success"
          @click="handleActivateTemplate"
        >
          {{ currentTemplate?.is_active ? '已激活' : '激活模板' }}
        </n-button>
        <n-popconfirm v-if="selectedTemplateId" @positive-click="handleDeleteTemplate">
          <template #trigger>
            <n-button type="error">删除模板</n-button>
          </template>
          确定删除模板 "{{ currentTemplate?.name }}" 及其所有配置？
        </n-popconfirm>
      </n-space>
      <div v-if="currentTemplate" style="margin-top: 12px; color: #666;">
        <n-space>
          <n-tag :type="currentTemplate.is_active ? 'success' : 'default'" size="small">
            {{ currentTemplate.is_active ? '已激活' : '未激活' }}
          </n-tag>
          <span v-if="currentTemplate.description">{{ currentTemplate.description }}</span>
        </n-space>
      </div>
    </n-card>

    <!-- 模板内容区域 -->
    <n-spin :show="loading">
      <template v-if="currentTemplate">
        <!-- 阶段列表 -->
        <n-collapse v-model:expanded-names="expandedPhases" style="margin-bottom: 20px;">
          <n-collapse-item
            v-for="phase in currentTemplate.phases"
            :key="phase.id"
            :name="phase.id"
          >
            <template #header>
              <n-space align="center">
                <span style="font-weight: 600; font-size: 15px;">{{ phase.name }}</span>
                <n-tag :type="getPhaseWeightTagType(phase)" size="small">
                  权重: {{ phase.weight }}%
                </n-tag>
                <n-tag v-if="phase.indicators" size="small" type="info">
                  {{ phase.indicators.length }} 个指标
                </n-tag>
              </n-space>
            </template>
            <template #header-extra>
              <n-space size="small" @click.stop>
                <n-popconfirm @positive-click="handleDeletePhase(phase)">
                  <template #trigger>
                    <n-button type="error" size="small">删除阶段</n-button>
                  </template>
                  确定删除阶段 "{{ phase.name }}" 及其下所有指标？
                </n-popconfirm>
              </n-space>
            </template>

            <!-- 阶段详情 -->
            <div style="padding: 8px 0;">
              <n-space align="center" style="margin-bottom: 16px;">
                <span>阶段名称：</span>
                <n-input
                  :value="phase.name"
                  size="small"
                  style="width: 160px;"
                  @update:value="(val: string) => handleUpdatePhaseName(phase, val)"
                />
                <span style="margin-left: 16px;">权重：</span>
                <n-slider
                  :value="phase.weight"
                  :min="0"
                  :max="100"
                  :step="1"
                  style="width: 200px;"
                  @update:value="(val: number) => handlePhaseWeightChange(phase, val)"
                />
                <n-input-number
                  :value="phase.weight"
                  :min="0"
                  :max="100"
                  size="small"
                  style="width: 100px;"
                  @update:value="(val: number | null) => handlePhaseWeightChange(phase, val ?? 0)"
                />
                <span>%</span>
              </n-space>

              <!-- 指标表格 -->
              <n-data-table
                :columns="indicatorColumns"
                :data="phase.indicators || []"
                :bordered="true"
                :single-line="false"
                size="small"
                :row-key="(row: any) => row.id"
                :expanded-row-keys="expandedIndicators"
                @update:expanded-row-keys="handleExpandedRowsChange"
              />

              <n-space style="margin-top: 12px; width: 100%;">
                <n-button
                  type="primary"
                  dashed
                  size="small"
                  style="flex: 1;"
                  @click="openCreateIndicator(phase)"
                >
                  + 添加评价指标
                </n-button>
                <n-button
                  type="info"
                  dashed
                  size="small"
                  style="flex: 1;"
                  @click="handleAiSuggestIndicators(phase)"
                >
                  AI 推荐
                </n-button>
              </n-space>
            </div>
          </n-collapse-item>
        </n-collapse>

        <n-button
          type="primary"
          dashed
          style="width: 100%; margin-bottom: 20px;"
          @click="openCreatePhase"
        >
          + 添加评价阶段
        </n-button>
      </template>

      <n-empty v-else-if="!loading" description="请先选择或创建一个评价模板" style="padding: 60px 0;" />
    </n-spin>

    <!-- 新建模板弹窗 -->
    <n-modal v-model:show="showTemplateModal" preset="card" title="新建评价模板" style="width: 500px;">
      <n-form label-placement="left" label-width="80">
        <n-form-item label="模板名称">
          <n-input v-model:value="templateForm.name" placeholder="如：2024春季过程评价" />
        </n-form-item>
        <n-form-item label="描述">
          <n-input v-model:value="templateForm.description" type="textarea" placeholder="可选，模板说明" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showTemplateModal = false">取消</n-button>
          <n-button type="primary" @click="handleCreateTemplate">创建</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- AI 生成模板弹窗 -->
    <n-modal v-model:show="showAiGenerateModal" preset="card" title="AI 生成评价模板" style="width: 560px;">
      <n-spin :show="aiGenerateLoading">
        <n-form label-placement="left" label-width="100">
          <n-form-item label="课程名称" required>
            <n-input
              v-model:value="aiGenerateForm.course_name"
              placeholder="如：Python程序设计、Web前端开发"
            />
          </n-form-item>
          <n-form-item label="课程描述">
            <n-input
              v-model:value="aiGenerateForm.course_description"
              type="textarea"
              placeholder="课程简介、教学目标等，帮助 AI 更精准生成"
              :rows="3"
            />
          </n-form-item>
          <n-form-item label="课程分类">
            <n-select
              v-model:value="aiGenerateForm.category"
              :options="courseCategoryOptions"
              placeholder="选择课程分类"
              clearable
            />
          </n-form-item>
          <n-form-item label="适用班级">
            <n-select
              v-model:value="aiGenerateForm.class_id"
              :options="classOptions"
              placeholder="选择班级（可选）"
              clearable
              :loading="classLoading"
            />
          </n-form-item>
          <n-form-item label="学生人数">
            <n-input-number
              v-model:value="aiGenerateForm.student_count"
              :min="1"
              :max="500"
              placeholder="预计学生人数"
            />
          </n-form-item>
          <n-form-item label="任务数量">
            <n-input-number
              v-model:value="aiGenerateForm.task_count"
              :min="1"
              :max="50"
              placeholder="课程包含的任务/项目数"
            />
          </n-form-item>
        </n-form>
      </n-spin>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showAiGenerateModal = false" :disabled="aiGenerateLoading">取消</n-button>
          <n-button type="primary" :loading="aiGenerateLoading" @click="handleAiGenerateTemplate">生成</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- AI 推荐指标弹窗 -->
    <n-modal v-model:show="showAiSuggestModal" preset="card" title="AI 推荐评价指标" style="width: 700px;">
      <n-spin :show="aiSuggestLoading">
        <template v-if="aiSuggestResult && aiSuggestResult.length > 0">
          <n-alert type="info" size="small" style="margin-bottom: 16px;">
            以下指标由 AI 根据阶段特点推荐，点击"采用"直接添加到当前阶段。
          </n-alert>
          <n-list bordered>
            <n-list-item v-for="(item, idx) in aiSuggestResult" :key="idx">
              <n-space align="center" justify="space-between" style="width: 100%;">
                <div style="flex: 1;">
                  <n-space align="center" style="margin-bottom: 4px;">
                    <span style="font-weight: 600;">{{ item.name }}</span>
                    <n-tag size="small" type="info">{{ capabilityDimMap[item.capability_dim] || item.capability_dim || '未分类' }}</n-tag>
                    <n-tag size="small">{{ dataSourceMap[item.data_source] || item.data_source || '未指定' }}</n-tag>
                    <n-tag size="small" type="warning">权重: {{ item.weight }}%</n-tag>
                  </n-space>
                  <div v-if="item.reason" style="color: #888; font-size: 13px; margin-top: 2px;">{{ item.reason }}</div>
                </div>
                <n-button
                  type="success"
                  size="small"
                  :loading="adoptingIndex === idx"
                  @click="handleAdoptIndicator(item, idx)"
                >
                  采用
                </n-button>
              </n-space>
            </n-list-item>
          </n-list>
        </template>
        <n-empty v-else-if="!aiSuggestLoading && aiSuggestFetched" description="暂无推荐指标，请尝试调整阶段信息后重试。" style="padding: 40px 0;" />
      </n-spin>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showAiSuggestModal = false">关闭</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 新建阶段弹窗 -->
    <n-modal v-model:show="showPhaseModal" preset="card" title="添加评价阶段" style="width: 460px;">
      <n-form label-placement="left" label-width="80">
        <n-form-item label="阶段名称">
          <n-select
            v-model:value="phaseForm.name"
            :options="phaseNameOptions"
            placeholder="选择或自定义"
            tag
            filterable
          />
        </n-form-item>
        <n-form-item label="权重">
          <n-space align="center">
            <n-slider v-model:value="phaseForm.weight" :min="0" :max="100" :step="1" style="width: 200px;" />
            <n-input-number v-model:value="phaseForm.weight" :min="0" :max="100" style="width: 100px;" />
            <span>%</span>
          </n-space>
        </n-form-item>
        <n-form-item label="排序">
          <n-input-number v-model:value="phaseForm.sort_order" :min="0" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showPhaseModal = false">取消</n-button>
          <n-button type="primary" @click="handleCreatePhase">添加</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 新建/编辑指标弹窗 -->
    <n-modal v-model:show="showIndicatorModal" preset="card" :title="editingIndicator ? '编辑评价指标' : '添加评价指标'" style="width: 600px;">
      <n-form label-placement="left" label-width="100">
        <n-form-item label="指标名称">
          <n-input v-model:value="indicatorForm.name" placeholder="如：课堂参与度、代码质量" />
        </n-form-item>
        <n-form-item label="权重">
          <n-space align="center">
            <n-slider v-model:value="indicatorForm.weight" :min="0" :max="100" :step="1" style="width: 200px;" />
            <n-input-number v-model:value="indicatorForm.weight" :min="0" :max="100" style="width: 100px;" />
            <span>%</span>
          </n-space>
        </n-form-item>
        <n-form-item label="能力维度">
          <n-select
            v-model:value="indicatorForm.capability_dim"
            :options="capabilityDimOptions"
            placeholder="选择能力维度"
          />
        </n-form-item>
        <n-form-item label="数据来源">
          <n-select
            v-model:value="indicatorForm.data_source"
            :options="dataSourceOptions"
            placeholder="选择数据来源"
          />
        </n-form-item>
        <n-form-item label="自动采集">
          <n-switch v-model:value="indicatorForm.auto_collect" />
          <span style="margin-left: 8px; color: #666;">开启后系统将自动采集该指标数据</span>
        </n-form-item>
        <n-form-item label="描述">
          <n-input v-model:value="indicatorForm.description" type="textarea" placeholder="可选，指标说明" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showIndicatorModal = false">取消</n-button>
          <n-button type="primary" @click="handleSaveIndicator">{{ editingIndicator ? '保存' : '添加' }}</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 评分主体配置弹窗 -->
    <n-modal v-model:show="showScorerModal" preset="card" title="评分主体配置" style="width: 600px;">
      <div style="margin-bottom: 16px;">
        <n-alert type="info" size="small">
          为指标 "{{ scorerIndicator?.name }}" 配置评分主体及其权重，权重之和应为 100%。
        </n-alert>
      </div>
      <n-data-table
        :columns="scorerColumns"
        :data="scorerConfigs"
        :bordered="true"
        size="small"
        style="margin-bottom: 16px;"
      />
      <n-divider style="margin: 12px 0;" />
      <n-space align="center">
        <span>新增评分主体：</span>
        <n-select
          v-model:value="newScorer.scorer_role"
          :options="scorerRoleOptions"
          placeholder="选择角色"
          style="width: 160px;"
        />
        <n-input-number
          v-model:value="newScorer.weight"
          :min="0"
          :max="100"
          style="width: 120px;"
          placeholder="权重"
        />
        <span>%</span>
        <n-button type="primary" size="small" @click="handleAddScorer">添加</n-button>
      </n-space>
      <div style="margin-top: 12px;">
        <n-tag :type="scorerWeightTotal === 100 ? 'success' : scorerWeightTotal > 100 ? 'error' : 'warning'" size="small">
          评分权重合计: {{ scorerWeightTotal }}%
        </n-tag>
      </div>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, h, watch } from 'vue'
import { useMessage, useDialog } from 'naive-ui'
import {
  NButton,
  NTag,
  NSpace,
  NTooltip,
  NIcon,
  NPopconfirm
} from 'naive-ui'
import { evalApi, adminApi } from '@/api'

const message = useMessage()
const dialog = useDialog()

// ==================== 常量选项 ====================

const capabilityDimOptions = [
  { label: '知识基础', value: 'knowledge' },
  { label: '工法能力', value: 'skill' },
  { label: '职业素养', value: 'quality' },
  { label: '创新贡献', value: 'innovation' }
]

const dataSourceOptions = [
  { label: '手动录入', value: 'manual' },
  { label: '代码提交', value: 'submission' },
  { label: '出勤', value: 'attendance' },
  { label: 'AI评分', value: 'ai_score' },
  { label: 'API', value: 'api' }
]

const capabilityDimMap: Record<string, string> = {
  knowledge: '知识基础',
  skill: '工法能力',
  quality: '职业素养',
  innovation: '创新贡献'
}

const dataSourceMap: Record<string, string> = {
  manual: '手动录入',
  submission: '代码提交',
  attendance: '出勤',
  ai_score: 'AI评分',
  api: 'API'
}

const phaseNameOptions = [
  { label: '课前', value: '课前' },
  { label: '课中', value: '课中' },
  { label: '课后', value: '课后' }
]

const scorerRoleOptions = [
  { label: '教师', value: 'teacher' },
  { label: 'AI', value: 'ai' },
  { label: '学生自评', value: 'self' },
  { label: '学生互评', value: 'peer' },
  { label: '企业导师', value: 'enterprise' }
]

const scorerRoleMap: Record<string, string> = {
  teacher: '教师',
  ai: 'AI',
  self: '学生自评',
  peer: '学生互评',
  enterprise: '企业导师'
}

const courseCategoryOptions = [
  { label: 'Python', value: 'Python' },
  { label: 'Web', value: 'Web' },
  { label: 'YOLO', value: 'YOLO' },
  { label: '数据分析', value: '数据分析' },
  { label: '机器学习', value: '机器学习' },
  { label: '通用', value: '通用' }
]

// ==================== 状态 ====================

const loading = ref(false)
const templates = ref<any[]>([])
const selectedTemplateId = ref<number | null>(null)
const currentTemplate = ref<any>(null)
const expandedPhases = ref<number[]>([])
const expandedIndicators = ref<number[]>([])

// 模板弹窗
const showTemplateModal = ref(false)
const templateForm = ref({ name: '', description: '' })

// AI 生成模板弹窗
const showAiGenerateModal = ref(false)
const aiGenerateLoading = ref(false)
const aiGenerateForm = ref({
  course_name: '',
  course_description: '',
  category: null as string | null,
  class_id: null as number | null,
  student_count: undefined as number | undefined,
  task_count: undefined as number | undefined
})

// 班级列表
const classOptions = ref<{ label: string; value: number }[]>([])
const classLoading = ref(false)

// AI 推荐指标弹窗
const showAiSuggestModal = ref(false)
const aiSuggestLoading = ref(false)
const aiSuggestFetched = ref(false)
const aiSuggestResult = ref<any[]>([])
const aiSuggestPhaseId = ref<number | null>(null)
const adoptingIndex = ref<number | null>(null)

// 阶段弹窗
const showPhaseModal = ref(false)
const phaseForm = ref({ name: '', weight: 30, sort_order: 0 })

// 指标弹窗
const showIndicatorModal = ref(false)
const editingIndicator = ref<any>(null)
const editingIndicatorPhaseId = ref<number | null>(null)
const indicatorForm = ref({
  name: '',
  weight: 20,
  capability_dim: null as string | null,
  data_source: null as string | null,
  auto_collect: false,
  description: ''
})

// 评分主体弹窗
const showScorerModal = ref(false)
const scorerIndicator = ref<any>(null)
const scorerConfigs = ref<any[]>([])
const newScorer = ref({ scorer_role: null as string | null, weight: 50 })

// 权重校验
const weightValidation = ref<{ valid: boolean; phase_total: number; messages: string[] }>({
  valid: false,
  phase_total: 0,
  messages: []
})

// ==================== 计算属性 ====================

const templateOptions = computed(() =>
  templates.value.map((t: any) => ({
    label: `${t.name}${t.is_active ? ' (已激活)' : ''}`,
    value: t.id
  }))
)

const scorerWeightTotal = computed(() =>
  scorerConfigs.value.reduce((sum: number, s: any) => sum + (s.weight || 0), 0)
)

// ==================== 指标表格列 ====================

const indicatorColumns = [
  {
    type: 'expand' as const,
    expandable: (row: any) => true,
    renderExpand: (row: any) => {
      const scorers = row.scorer_configs || []
      if (scorers.length === 0) {
        return h('div', { style: 'padding: 8px 16px; color: #999;' }, '暂无评分主体配置')
      }
      return h('div', { style: 'padding: 8px 16px;' }, [
        h('div', { style: 'margin-bottom: 8px; font-weight: 600;' }, '评分主体配置：'),
        ...scorers.map((sc: any) =>
          h('div', { style: 'margin-bottom: 4px;' }, [
            h(NTag, { size: 'small', style: 'margin-right: 8px;' }, { default: () => scorerRoleMap[sc.scorer_role] || sc.scorer_role }),
            h('span', {}, `权重: ${sc.weight}%`)
          ])
        )
      ])
    }
  },
  { title: '指标名称', key: 'name', minWidth: 120 },
  {
    title: '权重',
    key: 'weight',
    width: 100,
    render: (row: any) => `${row.weight}%`
  },
  {
    title: '能力维度',
    key: 'capability_dim',
    width: 100,
    render: (row: any) => {
      const label = capabilityDimMap[row.capability_dim] || row.capability_dim
      if (!label) return '-'
      return h(NTag, { size: 'small', type: 'info' }, { default: () => label })
    }
  },
  {
    title: '数据来源',
    key: 'data_source',
    width: 100,
    render: (row: any) => {
      const label = dataSourceMap[row.data_source] || row.data_source
      if (!label) return '-'
      return h(NTag, { size: 'small' }, { default: () => label })
    }
  },
  {
    title: '自动采集',
    key: 'auto_collect',
    width: 80,
    render: (row: any) => h(NTag, {
      size: 'small',
      type: row.auto_collect ? 'success' : 'default'
    }, { default: () => row.auto_collect ? '是' : '否' })
  },
  {
    title: '操作',
    key: 'actions',
    width: 220,
    render: (row: any) => h(NSpace, { size: 'small' }, {
      default: () => [
        h(NButton, {
          type: 'info',
          size: 'small',
          onClick: () => openScorerConfig(row)
        }, { default: () => '评分主体' }),
        h(NButton, {
          type: 'primary',
          size: 'small',
          onClick: () => openEditIndicator(row)
        }, { default: () => '编辑' }),
        h(NPopconfirm, {
          onPositiveClick: () => handleDeleteIndicator(row)
        }, {
          trigger: () => h(NButton, { type: 'error', size: 'small' }, { default: () => '删除' }),
          default: () => `确定删除指标 "${row.name}"？`
        })
      ]
    })
  }
]

// ==================== 评分主体表格列 ====================

const scorerColumns = [
  { title: '角色', key: 'scorer_role', render: (row: any) => scorerRoleMap[row.scorer_role] || row.scorer_role },
  {
    title: '权重',
    key: 'weight',
    render: (row: any) => `${row.weight}%`
  },
  {
    title: '操作',
    key: 'actions',
    width: 80,
    render: (row: any) => h(NPopconfirm, {
      onPositiveClick: () => handleDeleteScorer(row)
    }, {
      trigger: () => h(NButton, { type: 'error', size: 'small' }, { default: () => '删除' }),
      default: () => '确定删除该评分主体？'
    })
  }
]

// ==================== 模板操作 ====================

async function loadTemplates() {
  try {
    templates.value = await evalApi.getTemplates() as any
  } catch (e: any) {
    message.error(e?.detail || '加载模板列表失败')
  }
}

async function handleTemplateChange(id: number | null) {
  if (!id) {
    currentTemplate.value = null
    weightValidation.value = { valid: false, phase_total: 0, messages: [] }
    return
  }
  await loadTemplateDetail(id)
}

async function loadTemplateDetail(id: number) {
  loading.value = true
  try {
    const data = await evalApi.getTemplate(id) as any
    currentTemplate.value = data
    expandedPhases.value = data.phases?.map((p: any) => p.id) || []
    await checkWeights()
  } catch (e: any) {
    message.error(e?.detail || '加载模板详情失败')
  } finally {
    loading.value = false
  }
}

function openCreateTemplate() {
  templateForm.value = { name: '', description: '' }
  showTemplateModal.value = true
}

async function handleCreateTemplate() {
  if (!templateForm.value.name.trim()) {
    message.warning('请输入模板名称')
    return
  }
  try {
    await evalApi.createTemplate({
      name: templateForm.value.name,
      description: templateForm.value.description
    })
    message.success('模板创建成功')
    showTemplateModal.value = false
    await loadTemplates()
  } catch (e: any) {
    message.error(e?.detail || '创建模板失败')
  }
}

async function handleActivateTemplate() {
  if (!selectedTemplateId.value) return
  try {
    await evalApi.activateTemplate(selectedTemplateId.value)
    message.success('模板已激活')
    await loadTemplates()
    await loadTemplateDetail(selectedTemplateId.value)
  } catch (e: any) {
    message.error(e?.detail || '激活失败')
  }
}

async function handleDeleteTemplate() {
  if (!selectedTemplateId.value || !currentTemplate.value) return
  try {
    await evalApi.deleteTemplate(selectedTemplateId.value)
    message.success('模板已删除')
    selectedTemplateId.value = null
    currentTemplate.value = null
    await loadTemplates()
  } catch (e: any) {
    message.error(e?.detail || '删除失败')
  }
}

async function handleInitDefault() {
  loading.value = true
  try {
    await evalApi.initDefaultTemplate()
    message.success('默认模板初始化成功')
    await loadTemplates()
    // 自动选中最新创建的模板
    if (templates.value.length > 0) {
      const latest = templates.value[0]
      selectedTemplateId.value = latest.id
      await loadTemplateDetail(latest.id)
    }
  } catch (e: any) {
    message.error(e?.detail || '初始化默认模板失败')
  } finally {
    loading.value = false
  }
}

// ==================== AI 生成模板 ====================

async function loadClasses() {
  classLoading.value = true
  try {
    const data = await adminApi.getClasses() as any
    classOptions.value = (Array.isArray(data) ? data : []).map((c: any) => ({
      label: c.name || c.class_name || `班级${c.id}`,
      value: c.id
    }))
  } catch (e: any) {
    // 班级加载失败不阻塞主流程
    classOptions.value = []
  } finally {
    classLoading.value = false
  }
}

function openAiGenerateTemplate() {
  aiGenerateForm.value = {
    course_name: '',
    course_description: '',
    category: null,
    class_id: null,
    student_count: undefined,
    task_count: undefined
  }
  showAiGenerateModal.value = true
  loadClasses()
}

async function handleAiGenerateTemplate() {
  if (!aiGenerateForm.value.course_name.trim()) {
    message.warning('请输入课程名称')
    return
  }
  aiGenerateLoading.value = true
  try {
    await evalApi.aiGenerateTemplate({
      course_name: aiGenerateForm.value.course_name,
      course_description: aiGenerateForm.value.course_description,
      category: aiGenerateForm.value.category || undefined,
      class_id: aiGenerateForm.value.class_id || undefined,
      student_count: aiGenerateForm.value.student_count,
      task_count: aiGenerateForm.value.task_count
    })
    message.success('AI 模板生成成功')
    showAiGenerateModal.value = false
    await loadTemplates()
    // 自动选中最新模板
    if (templates.value.length > 0) {
      const latest = templates.value[0]
      selectedTemplateId.value = latest.id
      await loadTemplateDetail(latest.id)
    }
  } catch (e: any) {
    message.error(e?.detail || 'AI 生成模板失败')
  } finally {
    aiGenerateLoading.value = false
  }
}

// ==================== AI 推荐指标 ====================

async function handleAiSuggestIndicators(phase: any) {
  aiSuggestPhaseId.value = phase.id
  aiSuggestResult.value = []
  aiSuggestFetched.value = false
  aiSuggestLoading.value = true
  showAiSuggestModal.value = true

  try {
    const result = await evalApi.aiSuggestIndicators({ phase_id: phase.id }) as any
    aiSuggestResult.value = Array.isArray(result) ? result : (result?.indicators || result?.data || [])
    aiSuggestFetched.value = true
  } catch (e: any) {
    message.error(e?.detail || '获取 AI 推荐指标失败')
    aiSuggestFetched.value = true
  } finally {
    aiSuggestLoading.value = false
  }
}

async function handleAdoptIndicator(item: any, idx: number) {
  if (!aiSuggestPhaseId.value) {
    message.warning('未指定阶段，请重试')
    return
  }
  adoptingIndex.value = idx
  try {
    await evalApi.createIndicator(aiSuggestPhaseId.value, {
      name: item.name,
      weight: item.weight || 20,
      capability_dim: item.capability_dim || null,
      data_source: item.data_source || null,
      auto_collect: item.auto_collect || false,
      description: item.reason || item.description || ''
    })
    message.success(`指标 "${item.name}" 已采用`)
    // 从推荐列表中移除已采用的项
    aiSuggestResult.value.splice(idx, 1)
    // 刷新模板详情
    if (selectedTemplateId.value) {
      await loadTemplateDetail(selectedTemplateId.value)
    }
  } catch (e: any) {
    message.error(e?.detail || '采用指标失败')
  } finally {
    adoptingIndex.value = null
  }
}

// ==================== 权重校验 ====================

async function checkWeights() {
  if (!selectedTemplateId.value) return
  try {
    const result = await evalApi.checkTemplateWeights(selectedTemplateId.value) as any
    weightValidation.value = {
      valid: result.valid ?? false,
      phase_total: result.phase_total ?? 0,
      messages: result.messages ?? []
    }
  } catch (e: any) {
    // 如果接口不存在或出错，本地计算
    if (currentTemplate.value?.phases) {
      const total = currentTemplate.value.phases.reduce((sum: number, p: any) => sum + (p.weight || 0), 0)
      const messages: string[] = []
      for (const phase of currentTemplate.value.phases) {
        const indicators = phase.indicators || []
        if (indicators.length > 0) {
          const indTotal = indicators.reduce((sum: number, ind: any) => sum + (ind.weight || 0), 0)
          if (indTotal !== 100) {
            messages.push(`阶段 "${phase.name}" 指标权重合计 ${indTotal}%，应为 100%`)
          }
        }
      }
      weightValidation.value = {
        valid: total === 100 && messages.length === 0,
        phase_total: total,
        messages
      }
    }
  }
}

function getPhaseWeightTagType(phase: any): 'success' | 'warning' | 'error' | 'default' {
  if (phase.weight === 0) return 'default'
  const indicators = phase.indicators || []
  if (indicators.length === 0) return 'warning'
  const indTotal = indicators.reduce((sum: number, ind: any) => sum + (ind.weight || 0), 0)
  if (indTotal === 100) return 'success'
  if (indTotal > 100) return 'error'
  return 'warning'
}

// ==================== 阶段操作 ====================

function openCreatePhase() {
  if (!currentTemplate.value) {
    message.warning('请先选择一个模板')
    return
  }
  const existingNames = (currentTemplate.value.phases || []).map((p: any) => p.name)
  const nextName = phaseNameOptions.find(o => !existingNames.includes(o.value))
  phaseForm.value = {
    name: nextName?.value || '',
    weight: 30,
    sort_order: (currentTemplate.value.phases || []).length
  }
  showPhaseModal.value = true
}

async function handleCreatePhase() {
  if (!phaseForm.value.name.trim()) {
    message.warning('请输入或选择阶段名称')
    return
  }
  if (!selectedTemplateId.value) return
  try {
    await evalApi.createPhase(selectedTemplateId.value, {
      name: phaseForm.value.name,
      weight: phaseForm.value.weight,
      sort_order: phaseForm.value.sort_order
    })
    message.success('阶段添加成功')
    showPhaseModal.value = false
    await loadTemplateDetail(selectedTemplateId.value)
  } catch (e: any) {
    message.error(e?.detail || '添加阶段失败')
  }
}

async function handleUpdatePhaseName(phase: any, newName: string) {
  if (!newName.trim() || newName === phase.name) return
  try {
    await evalApi.updatePhase(phase.id, { name: newName })
    phase.name = newName
    message.success('阶段名称已更新')
  } catch (e: any) {
    message.error(e?.detail || '更新失败')
  }
}

async function handlePhaseWeightChange(phase: any, newWeight: number) {
  const oldWeight = phase.weight
  phase.weight = newWeight
  try {
    await evalApi.updatePhase(phase.id, { weight: newWeight })
    await checkWeights()
  } catch (e: any) {
    phase.weight = oldWeight
    message.error(e?.detail || '更新权重失败')
  }
}

async function handleDeletePhase(phase: any) {
  try {
    await evalApi.deletePhase(phase.id)
    message.success('阶段已删除')
    if (selectedTemplateId.value) {
      await loadTemplateDetail(selectedTemplateId.value)
    }
  } catch (e: any) {
    message.error(e?.detail || '删除阶段失败')
  }
}

// ==================== 指标操作 ====================

function openCreateIndicator(phase: any) {
  editingIndicator.value = null
  editingIndicatorPhaseId.value = phase.id
  indicatorForm.value = {
    name: '',
    weight: 20,
    capability_dim: null,
    data_source: null,
    auto_collect: false,
    description: ''
  }
  showIndicatorModal.value = true
}

function openEditIndicator(indicator: any) {
  editingIndicator.value = indicator
  editingIndicatorPhaseId.value = null
  indicatorForm.value = {
    name: indicator.name,
    weight: indicator.weight,
    capability_dim: indicator.capability_dim || null,
    data_source: indicator.data_source || null,
    auto_collect: indicator.auto_collect || false,
    description: indicator.description || ''
  }
  showIndicatorModal.value = true
}

async function handleSaveIndicator() {
  if (!indicatorForm.value.name.trim()) {
    message.warning('请输入指标名称')
    return
  }
  try {
    if (editingIndicator.value) {
      await evalApi.updateIndicator(editingIndicator.value.id, {
        name: indicatorForm.value.name,
        weight: indicatorForm.value.weight,
        capability_dim: indicatorForm.value.capability_dim,
        data_source: indicatorForm.value.data_source,
        auto_collect: indicatorForm.value.auto_collect,
        description: indicatorForm.value.description
      })
      message.success('指标已更新')
    } else {
      if (!editingIndicatorPhaseId.value) return
      await evalApi.createIndicator(editingIndicatorPhaseId.value, {
        name: indicatorForm.value.name,
        weight: indicatorForm.value.weight,
        capability_dim: indicatorForm.value.capability_dim,
        data_source: indicatorForm.value.data_source,
        auto_collect: indicatorForm.value.auto_collect,
        description: indicatorForm.value.description
      })
      message.success('指标已添加')
    }
    showIndicatorModal.value = false
    if (selectedTemplateId.value) {
      await loadTemplateDetail(selectedTemplateId.value)
    }
  } catch (e: any) {
    message.error(e?.detail || '保存指标失败')
  }
}

async function handleDeleteIndicator(indicator: any) {
  try {
    await evalApi.deleteIndicator(indicator.id)
    message.success('指标已删除')
    if (selectedTemplateId.value) {
      await loadTemplateDetail(selectedTemplateId.value)
    }
  } catch (e: any) {
    message.error(e?.detail || '删除指标失败')
  }
}

function handleExpandedRowsChange(keys: number[]) {
  expandedIndicators.value = keys
}

// ==================== 评分主体操作 ====================

function openScorerConfig(indicator: any) {
  scorerIndicator.value = indicator
  scorerConfigs.value = indicator.scorer_configs ? [...indicator.scorer_configs] : []
  newScorer.value = { scorer_role: null, weight: 50 }
  showScorerModal.value = true
}

async function handleAddScorer() {
  if (!newScorer.value.scorer_role) {
    message.warning('请选择评分角色')
    return
  }
  if (!scorerIndicator.value) return

  // 检查是否已有相同角色
  const exists = scorerConfigs.value.some((s: any) => s.scorer_role === newScorer.value.scorer_role)
  if (exists) {
    message.warning('该角色已存在，请勿重复添加')
    return
  }

  try {
    await evalApi.addScorer(scorerIndicator.value.id, {
      scorer_role: newScorer.value.scorer_role,
      weight: newScorer.value.weight
    })
    message.success('评分主体已添加')
    // 刷新该指标的评分配置
    if (selectedTemplateId.value) {
      await loadTemplateDetail(selectedTemplateId.value)
      // 重新打开展开的指标
      const updatedIndicator = findIndicator(scorerIndicator.value.id)
      if (updatedIndicator) {
        scorerConfigs.value = updatedIndicator.scorer_configs ? [...updatedIndicator.scorer_configs] : []
        scorerIndicator.value = updatedIndicator
      }
    }
    newScorer.value = { scorer_role: null, weight: 50 }
  } catch (e: any) {
    message.error(e?.detail || '添加评分主体失败')
  }
}

async function handleDeleteScorer(scorer: any) {
  try {
    await evalApi.deleteScorer(scorer.id)
    message.success('评分主体已删除')
    if (selectedTemplateId.value) {
      await loadTemplateDetail(selectedTemplateId.value)
      const updatedIndicator = findIndicator(scorerIndicator.value?.id)
      if (updatedIndicator) {
        scorerConfigs.value = updatedIndicator.scorer_configs ? [...updatedIndicator.scorer_configs] : []
        scorerIndicator.value = updatedIndicator
      }
    }
  } catch (e: any) {
    message.error(e?.detail || '删除评分主体失败')
  }
}

function findIndicator(indicatorId: number): any {
  if (!currentTemplate.value?.phases) return null
  for (const phase of currentTemplate.value.phases) {
    for (const ind of (phase.indicators || [])) {
      if (ind.id === indicatorId) return ind
    }
  }
  return null
}

// ==================== 初始化 ====================

onMounted(async () => {
  await loadTemplates()
})
</script>

<style scoped>
.process-eval-config {
  max-width: 1200px;
  margin: 0 auto;
}

.page-title {
  margin: 0 0 24px;
  font-size: 20px;
}
</style>
