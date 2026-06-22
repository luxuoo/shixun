<template>
  <div class="process-eval-container">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
      <h2>过程性评价看板</h2>
      <n-space>
        <n-select
          v-model:value="selectedClassId"
          :options="classOptions"
          placeholder="请选择班级"
          clearable
          style="width: 200px;"
          @update:value="handleClassChange"
        />
        <n-select
          v-model:value="selectedTemplateId"
          :options="templateOptions"
          placeholder="选择评价模板"
          clearable
          style="width: 200px;"
          :disabled="!selectedClassId"
          @update:value="loadDashboard"
        />
        <n-button
          type="primary"
          :loading="collecting"
          :disabled="!selectedClassId || !selectedTemplateId"
          @click="handleAutoCollect"
        >
          自动采集
        </n-button>
      </n-space>
    </div>

    <n-alert v-if="!selectedClassId" type="info" style="margin-bottom: 24px;">
      请先选择一个班级以查看过程性评价数据。
    </n-alert>

    <n-spin :show="loading">
      <template v-if="selectedClassId && dashboard">
        <!-- 汇总统计卡片 -->
        <n-grid :cols="4" :x-gap="16" :y-gap="16" style="margin-bottom: 24px;">
          <n-gi>
            <n-card>
              <n-statistic label="学生总数" :value="dashboard.distribution.total_students">
                <template #prefix>
                  <n-icon color="#2080f0" size="24">
                    <svg viewBox="0 0 24 24"><path fill="currentColor" d="M16 11c1.66 0 2.99-1.34 2.99-3S17.66 5 16 5c-1.66 0-3 1.34-3 3s1.34 3 3 3zm-8 0c1.66 0 2.99-1.34 2.99-3S9.66 5 8 5C6.34 5 5 6.34 5 8s1.34 3 3 3zm0 2c-2.33 0-7 1.17-7 3.5V19h14v-2.5c0-2.33-4.67-3.5-7-3.5z"/></svg>
                  </n-icon>
                </template>
              </n-statistic>
            </n-card>
          </n-gi>
          <n-gi>
            <n-card>
              <n-statistic label="平均分" :value="dashboard.distribution.average_score" :precision="1">
                <template #prefix>
                  <n-icon color="#18a058" size="24">
                    <svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg>
                  </n-icon>
                </template>
              </n-statistic>
            </n-card>
          </n-gi>
          <n-gi>
            <n-card>
              <n-statistic label="及格率" :value="dashboard.distribution.pass_rate" :precision="1">
                <template #suffix>%</template>
                <template #prefix>
                  <n-icon color="#f0a020" size="24">
                    <svg viewBox="0 0 24 24"><path fill="currentColor" d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/></svg>
                  </n-icon>
                </template>
              </n-statistic>
            </n-card>
          </n-gi>
          <n-gi>
            <n-card>
              <n-statistic label="优秀率" :value="dashboard.distribution.excellent_rate" :precision="1">
                <template #suffix>%</template>
                <template #prefix>
                  <n-icon color="#d03050" size="24">
                    <svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 17.27L18.18 21l-1.64-7.03L22 9.24l-7.19-.61L12 2 9.19 8.63 2 9.24l5.46 4.73L5.82 21z"/></svg>
                  </n-icon>
                </template>
              </n-statistic>
            </n-card>
          </n-gi>
        </n-grid>

        <!-- 成绩分布图 + 薄弱维度分析 -->
        <n-grid :cols="2" :x-gap="16" :y-gap="16" style="margin-bottom: 24px;">
          <n-gi>
            <n-card title="成绩分布">
              <div class="chart-wrapper">
                <canvas ref="chartCanvas" width="520" height="320"></canvas>
              </div>
            </n-card>
          </n-gi>
          <n-gi>
            <n-card title="薄弱维度分析">
              <template #header-extra>
                <n-tag type="warning" size="small">班级平均最低维度</n-tag>
              </template>
              <n-space vertical :size="16">
                <div v-for="(dim, index) in dashboard.weak_dims" :key="dim.dimension" class="weak-dim-item">
                  <div class="weak-dim-header">
                    <n-space align="center" :size="8">
                      <n-tag :type="index === 0 ? 'error' : index === 1 ? 'warning' : 'info'" size="small">
                        {{ index + 1 }}
                      </n-tag>
                      <span class="weak-dim-label">{{ dim.label }}</span>
                    </n-space>
                    <span class="weak-dim-score">{{ dim.avg_score.toFixed(1) }}分</span>
                  </div>
                  <n-progress
                    type="line"
                    :percentage="dim.avg_score"
                    :color="getDimProgressColor(dim.avg_score)"
                    :rail-color="getDimRailColor(dim.avg_score)"
                    style="margin-top: 6px;"
                  />
                </div>
                <n-empty v-if="!dashboard.weak_dims || dashboard.weak_dims.length === 0" description="暂无维度数据" />
              </n-space>
            </n-card>
          </n-gi>
        </n-grid>

        <!-- 排名表格 -->
        <n-card title="学生成绩排名" style="margin-bottom: 24px;">
          <template #header-extra>
            <n-space align="center" :size="8">
              <n-tag type="success" size="small">共 {{ dashboard.ranking.length }} 名学生</n-tag>
            </n-space>
          </template>
          <n-data-table
            :columns="rankingColumns"
            :data="dashboard.ranking"
            :bordered="false"
            :single-line="false"
            :max-height="400"
            striped
          />
        </n-card>

        <!-- AI 学情洞察 -->
        <n-card title="AI 学情洞察">
          <template #header-extra>
            <n-button
              type="primary"
              :loading="insightLoading"
              :disabled="!selectedClassId"
              @click="handleGenerateInsight"
            >
              生成洞察报告
            </n-button>
          </template>
          <n-spin :show="insightLoading">
            <div v-if="insightReport" class="insight-report">
              {{ insightReport }}
            </div>
            <n-empty
              v-else
              description="点击右上角「生成洞察报告」按钮，AI 将自动分析班级学情并生成洞察报告。"
              style="padding: 40px 0;"
            />
          </n-spin>
        </n-card>
      </template>

      <n-empty
        v-else-if="selectedClassId && !loading && !dashboard"
        description="暂无评价数据，请尝试选择评价模板或执行自动采集"
        style="margin-top: 80px;"
      />
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, watch, nextTick, h } from 'vue'
import { NTag, NIcon, useMessage } from 'naive-ui'
import { evalApi, adminApi } from '@/api'

const message = useMessage()

// --- 类型定义 ---
interface ScoreRange {
  label?: string
  range?: string
  count: number
}

interface ClassDashboard {
  distribution: {
    score_ranges: ScoreRange[]
    total_students: number
    average_score: number
    pass_rate: number
    excellent_rate: number
  }
  ranking: {
    rank: number
    student_id: number
    student_name: string
    total_score: number
  }[]
  weak_dims: {
    dimension: string
    label: string
    avg_score: number
  }[]
}

interface ClassOption {
  label: string
  value: number
}

interface TemplateOption {
  label: string
  value: number
}

// --- 状态 ---
const loading = ref(false)
const collecting = ref(false)
const selectedClassId = ref<number | null>(null)
const selectedTemplateId = ref<number | null>(null)
const classOptions = ref<ClassOption[]>([])
const templateOptions = ref<TemplateOption[]>([])
const dashboard = ref<ClassDashboard | null>(null)
const chartCanvas = ref<HTMLCanvasElement | null>(null)
const insightLoading = ref(false)
const insightReport = ref<string | null>(null)

// --- 表格列定义 ---
const rankingColumns = [
  {
    title: '排名',
    key: 'rank',
    width: 80,
    align: 'center' as const,
    render(row: { rank: number }) {
      let tagType: 'success' | 'warning' | 'info' = 'info'
      if (row.rank === 1) tagType = 'success'
      else if (row.rank === 2) tagType = 'warning'
      else if (row.rank === 3) tagType = 'info'
      return h(
        NTag,
        { type: tagType, size: 'small', round: true },
        { default: () => `#${row.rank}` }
      )
    }
  },
  {
    title: '学号',
    key: 'student_id',
    width: 120,
    align: 'center' as const
  },
  {
    title: '姓名',
    key: 'student_name',
    width: 140
  },
  {
    title: '总评分',
    key: 'total_score',
    width: 140,
    align: 'center' as const,
    sorter(a: { total_score: number }, b: { total_score: number }) {
      return a.total_score - b.total_score
    },
    render(row: { total_score: number }) {
      const score = row.total_score
      let color = '#d03050'
      if (score >= 90) color = '#18a058'
      else if (score >= 80) color = '#2080f0'
      else if (score >= 70) color = '#f0a020'
      else if (score >= 60) color = '#f0a020'
      return h(
        'span',
        { style: `color: ${color}; font-weight: 600; font-size: 15px;` },
        { default: () => score.toFixed(1) }
      )
    }
  },
  {
    title: '等级',
    key: 'total_score',
    width: 100,
    align: 'center' as const,
    render(row: { total_score: number }) {
      const score = row.total_score
      let label = '不及格'
      let type: 'success' | 'warning' | 'info' | 'error' = 'error'
      if (score >= 90) { label = '优秀'; type = 'success' }
      else if (score >= 80) { label = '良好'; type = 'info' }
      else if (score >= 70) { label = '中等'; type = 'warning' }
      else if (score >= 60) { label = '及格'; type = 'warning' }
      return h(
        NTag,
        { type, size: 'small' },
        { default: () => label }
      )
    }
  }
]

// --- 工具函数 ---
function getDimProgressColor(score: number): string {
  if (score >= 90) return '#18a058'
  if (score >= 80) return '#2080f0'
  if (score >= 70) return '#f0a020'
  if (score >= 60) return '#f0a020'
  return '#d03050'
}

function getDimRailColor(score: number): string {
  if (score >= 90) return 'rgba(24,160,88,0.1)'
  if (score >= 80) return 'rgba(32,128,240,0.1)'
  if (score >= 70) return 'rgba(240,160,32,0.1)'
  if (score >= 60) return 'rgba(240,160,32,0.1)'
  return 'rgba(208,48,80,0.1)'
}

function getBarColor(label: string): string {
  if (!label) return '#d03050'
  if (label.includes('90') || label.includes('100')) return '#18a058'
  if (label.includes('80')) return '#2080f0'
  if (label.includes('70')) return '#f0a020'
  if (label.includes('60')) return '#f5a623'
  return '#d03050'
}

// --- 绘制柱状图 ---
function drawDistributionChart() {
  const canvas = chartCanvas.value
  if (!canvas || !dashboard.value) return

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const dpr = window.devicePixelRatio || 1
  const displayWidth = 520
  const displayHeight = 320
  canvas.width = displayWidth * dpr
  canvas.height = displayHeight * dpr
  canvas.style.width = displayWidth + 'px'
  canvas.style.height = displayHeight + 'px'
  ctx.scale(dpr, dpr)

  const data = dashboard.value.distribution.score_ranges
  if (!data || data.length === 0) return

  const padding = { top: 30, right: 30, bottom: 50, left: 56 }
  const chartWidth = displayWidth - padding.left - padding.right
  const chartHeight = displayHeight - padding.top - padding.bottom

  const maxCount = Math.max(...data.map(d => d.count), 1)
  const niceMax = Math.ceil(maxCount / 5) * 5 || 5

  // 清空画布
  ctx.clearRect(0, 0, displayWidth, displayHeight)

  // 绘制背景网格线
  ctx.strokeStyle = '#f0f0f0'
  ctx.lineWidth = 1
  const gridLines = 5
  for (let i = 0; i <= gridLines; i++) {
    const y = padding.top + (chartHeight / gridLines) * i
    ctx.beginPath()
    ctx.moveTo(padding.left, y)
    ctx.lineTo(displayWidth - padding.right, y)
    ctx.stroke()

    // Y 轴标签
    const value = niceMax - (niceMax / gridLines) * i
    ctx.fillStyle = '#999'
    ctx.font = '12px sans-serif'
    ctx.textAlign = 'right'
    ctx.textBaseline = 'middle'
    ctx.fillText(String(value), padding.left - 10, y)
  }

  // 绘制柱状图
  const barCount = data.length
  const totalBarArea = chartWidth
  const barGroupWidth = totalBarArea / barCount
  const barWidth = barGroupWidth * 0.6
  const barGap = (barGroupWidth - barWidth) / 2

  for (let i = 0; i < barCount; i++) {
    const item = data[i]
    const barHeight = (item.count / niceMax) * chartHeight
    const x = padding.left + barGroupWidth * i + barGap
    const y = padding.top + chartHeight - barHeight
    const color = getBarColor(item.range || item.label || '')

    // 绘制渐变柱体
    const gradient = ctx.createLinearGradient(x, y, x, y + barHeight)
    gradient.addColorStop(0, color)
    gradient.addColorStop(1, color + '99')
    ctx.fillStyle = gradient
    ctx.beginPath()
    const radius = 4
    ctx.moveTo(x + radius, y)
    ctx.lineTo(x + barWidth - radius, y)
    ctx.quadraticCurveTo(x + barWidth, y, x + barWidth, y + radius)
    ctx.lineTo(x + barWidth, y + barHeight)
    ctx.lineTo(x, y + barHeight)
    ctx.lineTo(x, y + radius)
    ctx.quadraticCurveTo(x, y, x + radius, y)
    ctx.fill()

    // 柱体上方数值
    ctx.fillStyle = '#333'
    ctx.font = 'bold 13px sans-serif'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'bottom'
    ctx.fillText(String(item.count), x + barWidth / 2, y - 6)

    // X 轴标签
    ctx.fillStyle = '#666'
    ctx.font = '12px sans-serif'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'top'
    ctx.fillText(item.range || item.label || '', x + barWidth / 2, padding.top + chartHeight + 10)
  }

  // Y 轴标题
  ctx.save()
  ctx.translate(16, padding.top + chartHeight / 2)
  ctx.rotate(-Math.PI / 2)
  ctx.fillStyle = '#666'
  ctx.font = '12px sans-serif'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText('学生人数', 0, 0)
  ctx.restore()

  // X 轴标题
  ctx.fillStyle = '#666'
  ctx.font = '12px sans-serif'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'top'
  ctx.fillText('分数段', displayWidth / 2, displayHeight - 10)
}

// --- 数据加载 ---
async function loadClasses() {
  try {
    const res = await adminApi.getClasses() as any
    const classes = Array.isArray(res) ? res : (res?.data || res?.classes || [])
    classOptions.value = classes.map((c: any) => ({
      label: c.name,
      value: c.id
    }))
  } catch (error: any) {
    console.error('加载班级列表失败', error)
    message.error('加载班级列表失败: ' + (error.message || '未知错误'))
  }
}

async function loadTemplates() {
  if (!selectedClassId.value) {
    templateOptions.value = []
    selectedTemplateId.value = null
    return
  }
  try {
    const res = await evalApi.getTemplates(selectedClassId.value) as any
    const templates = Array.isArray(res) ? res : (res?.data || res?.templates || [])
    templateOptions.value = templates.map((t: any) => ({
      label: t.name,
      value: t.id
    }))
  } catch (error: any) {
    console.error('加载模板列表失败', error)
    message.error('加载模板列表失败: ' + (error.message || '未知错误'))
    templateOptions.value = []
  }
}

async function loadDashboard() {
  if (!selectedClassId.value) return
  loading.value = true
  dashboard.value = null
  try {
    const res = await evalApi.getClassDashboard(selectedClassId.value, selectedTemplateId.value ?? undefined) as any
    dashboard.value = {
      distribution: {
        score_ranges: res?.distribution?.score_ranges || [],
        total_students: res?.distribution?.total_students || 0,
        average_score: res?.distribution?.average_score || 0,
        pass_rate: res?.distribution?.pass_rate || 0,
        excellent_rate: res?.distribution?.excellent_rate || 0
      },
      ranking: res?.ranking || [],
      weak_dims: res?.weak_dims || []
    }
    await nextTick()
    drawDistributionChart()
  } catch (error: any) {
    console.error('加载班级看板失败', error)
    message.error('加载班级看板失败: ' + (error.message || '未知错误'))
  } finally {
    loading.value = false
  }
}

function handleClassChange(classId: number | null) {
  selectedClassId.value = classId
  selectedTemplateId.value = null
  dashboard.value = null
  insightReport.value = null
  if (classId) {
    loadTemplates()
  } else {
    templateOptions.value = []
  }
}

async function handleAutoCollect() {
  if (!selectedClassId.value || !selectedTemplateId.value) return
  collecting.value = true
  try {
    await evalApi.autoCollect(selectedTemplateId.value, selectedClassId.value)
    message.success('自动采集完成')
    await loadDashboard()
  } catch (error: any) {
    console.error('自动采集失败', error)
    message.error('自动采集失败: ' + (error.message || '未知错误'))
  } finally {
    collecting.value = false
  }
}

async function handleGenerateInsight() {
  if (!selectedClassId.value) return
  insightLoading.value = true
  try {
    const res = await evalApi.aiClassInsight(selectedClassId.value) as any
    insightReport.value = typeof res === 'string' ? res : (res?.report || res?.data?.report || JSON.stringify(res))
  } catch (error: any) {
    console.error('生成 AI 洞察报告失败', error)
    message.error('生成 AI 洞察报告失败: ' + (error.message || '未知错误'))
  } finally {
    insightLoading.value = false
  }
}

// --- 生命周期 ---
onMounted(() => {
  loadClasses()
})

// 窗口大小变化时重绘图表
if (typeof window !== 'undefined') {
  window.addEventListener('resize', () => {
    drawDistributionChart()
  })
}
</script>

<style scoped>
.process-eval-container {
  max-width: 1200px;
  margin: 0 auto;
}

.chart-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  padding: 8px 0;
}

.chart-wrapper canvas {
  max-width: 100%;
}

.weak-dim-item {
  padding: 12px 16px;
  background: #fafafa;
  border-radius: 8px;
  transition: background 0.2s;
}

.weak-dim-item:hover {
  background: #f0f0f0;
}

.weak-dim-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.weak-dim-label {
  font-size: 14px;
  font-weight: 500;
  color: #333;
}

.weak-dim-score {
  font-size: 15px;
  font-weight: 600;
  color: #d03050;
}

@media (max-width: 1024px) {
  .process-eval-container {
    padding: 0 12px;
  }
}

@media (max-width: 768px) {
  .process-eval-container h2 {
    font-size: 18px;
  }
}

.insight-report {
  white-space: pre-wrap;
  word-break: break-word;
  line-height: 1.8;
  font-size: 14px;
  color: #333;
  padding: 16px 20px;
  background: linear-gradient(135deg, #f8f9ff 0%, #f0f4ff 100%);
  border-radius: 8px;
  border: 1px solid #e0e6f6;
  min-height: 120px;
}
</style>
