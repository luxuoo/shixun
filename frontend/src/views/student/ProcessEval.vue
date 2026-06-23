<template>
  <div class="process-eval-container">
    <h2 class="page-title">过程性评价</h2>

    <n-spin :show="loading">
      <template v-if="!loading && !gradesVisible">
        <n-empty description="成绩暂未开放查看，请等待教师开放" style="padding: 60px 0;" />
      </template>

      <template v-else-if="!loading && !dashboardData">
        <n-empty description="暂无过程性评价数据" style="padding: 60px 0;" />
      </template>

      <template v-else-if="dashboardData">
        <!-- 总分卡片 -->
        <n-card class="total-score-card" style="margin-bottom: 20px;">
          <n-grid :cols="3" :x-gap="20" responsive="screen" item-responsive>
            <n-gi>
              <n-statistic label="过程性评价总分" :value="dashboardData.total_score ?? 0">
                <template #suffix>
                  <span style="font-size: 14px; color: #999;">/ 100</span>
                </template>
              </n-statistic>
            </n-gi>
            <n-gi>
              <n-statistic label="评价模板">
                <template #default>
                  <n-tag type="info" size="large">{{ dashboardData.template_name || '默认模板' }}</n-tag>
                </template>
              </n-statistic>
            </n-gi>
            <n-gi>
              <n-statistic label="得分等级">
                <template #default>
                  <n-tag
                    :type="getScoreTagType(dashboardData.total_score)"
                    size="large"
                  >
                    {{ getScoreLevel(dashboardData.total_score) }}
                  </n-tag>
                </template>
              </n-statistic>
            </n-gi>
          </n-grid>
        </n-card>

        <!-- 阶段分数 -->
        <n-card title="阶段得分" style="margin-bottom: 20px;">
          <n-grid :cols="3" :x-gap="16" responsive="screen" item-responsive>
            <n-gi v-for="phase in phaseScores" :key="phase.phase_id || phase.phase_name">
              <div class="phase-card">
                <div class="phase-name">{{ phase.phase_name }}</div>
                <div class="phase-score" :style="{ color: getScoreColor(phase.score) }">
                  {{ phase.score ?? '--' }}
                </div>
                <div class="phase-weight">权重: {{ phase.phase_weight }}%</div>
                <div class="phase-bar">
                  <div
                    class="phase-bar-fill"
                    :style="{
                      width: (phase.score ?? 0) + '%',
                      backgroundColor: getScoreColor(phase.score)
                    }"
                  ></div>
                </div>
              </div>
            </n-gi>
          </n-grid>
          <n-empty v-if="!phaseScores.length" description="暂无阶段数据" size="small" />
        </n-card>

        <!-- 阶段得分饼图 -->
        <n-card title="阶段得分占比" style="margin-bottom: 20px;">
          <div class="chart-wrapper">
            <canvas
              ref="pieCanvasRef"
              :width="400"
              :height="320"
              class="pie-canvas"
            ></canvas>
          </div>
          <div v-if="!hasPieData" class="chart-empty">
            <n-empty description="暂无阶段得分数据" size="small" />
          </div>
        </n-card>

        <!-- 雷达图与趋势图 -->
        <n-grid :cols="2" :x-gap="20" style="margin-bottom: 20px;" responsive="screen" item-responsive>
          <!-- 能力维度雷达图 -->
          <n-gi>
            <n-card title="能力维度雷达图">
              <div class="chart-wrapper">
                <canvas
                  ref="radarCanvasRef"
                  :width="480"
                  :height="380"
                  class="radar-canvas"
                ></canvas>
              </div>
              <div v-if="!radarData.length" class="chart-empty">
                <n-empty description="暂无维度数据" size="small" />
              </div>
            </n-card>
          </n-gi>

          <!-- 分数趋势图 -->
          <n-gi>
            <n-card title="分数趋势">
              <div class="chart-wrapper">
                <canvas
                  ref="trendCanvasRef"
                  :width="500"
                  :height="300"
                  class="trend-canvas"
                ></canvas>
              </div>
              <div v-if="!trendPoints.length" class="chart-empty">
                <n-empty description="暂无趋势数据" size="small" />
              </div>
            </n-card>
          </n-gi>
        </n-grid>

        <!-- AI 诊断报告 -->
        <n-card title="AI 诊断报告" style="margin-bottom: 20px;">
          <div style="margin-bottom: 16px;">
            <n-button
              type="primary"
              :loading="diagnoseLoading"
              :disabled="diagnoseLoading"
              @click="generateDiagnoseReport"
            >
              <template #icon>
                <n-icon>
                  <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                    <path d="M12 2a10 10 0 1 0 0 20 10 10 0 0 0 0-20z" />
                    <path d="M12 16v-4" />
                    <path d="M12 8h.01" />
                  </svg>
                </n-icon>
              </template>
              {{ diagnoseLoading ? '正在生成...' : (diagnoseReport ? '重新生成诊断报告' : '生成诊断报告') }}
            </n-button>
          </div>

          <n-spin :show="diagnoseLoading">
            <div v-if="diagnoseReport" class="ai-report-content">
              <div v-html="renderMarkdown(diagnoseReport)"></div>
            </div>
            <div v-else-if="!diagnoseLoading" style="text-align: center; padding: 40px 0; color: #999;">
              点击上方按钮，AI 将根据您的过程性评价数据生成个性化诊断报告
            </div>
          </n-spin>
        </n-card>

        <!-- 评分明细表 -->
        <n-card title="评分明细">
          <n-data-table
            :columns="detailColumns"
            :data="detailTableData"
            :bordered="false"
            :pagination="{ pageSize: 10 }"
          />
          <n-empty v-if="!detailTableData.length" description="暂无评分明细" size="small" style="padding: 40px 0;" />
        </n-card>
      </template>
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, nextTick, watch, h } from 'vue'
import { NTag } from 'naive-ui'
import { evalApi, authApi } from '@/api'
import { useUserStore } from '@/stores/user'

interface PhaseScore {
  phase_id: number
  phase_name: string
  phase_weight: number
  score: number | null
  weighted_score: number
  indicators: Array<{ id: number; name: string; score: number; max_score: number; weight: number; normalized_score: number }>
}

interface DashboardData {
  total_score: number | null
  phase_scores: PhaseScore[]
  dim_scores: RadarItem[]
  template_name: string
}

interface RadarItem {
  dimension: string
  dim_label: string
  score: number
  count: number
}

interface TrendPoint {
  date: string
  total_score: number
  phase_scores?: Record<string, number>
  dim_scores?: Record<string, number>
}

interface TrendData {
  points: TrendPoint[]
}

const userStore = useUserStore()
const loading = ref(false)
const gradesVisible = ref(true)
const dashboardData = ref<DashboardData | null>(null)
const radarData = ref<RadarItem[]>([])
const trendPoints = ref<TrendPoint[]>([])

const radarCanvasRef = ref<HTMLCanvasElement | null>(null)
const trendCanvasRef = ref<HTMLCanvasElement | null>(null)
const pieCanvasRef = ref<HTMLCanvasElement | null>(null)

const phaseScores = ref<PhaseScore[]>([])
const detailTableData = ref<any[]>([])

// AI 诊断报告相关状态
const diagnoseLoading = ref(false)
const diagnoseReport = ref<string | null>(null)

// 是否有饼图数据
const hasPieData = computed(() => {
  if (!dashboardData.value?.phase_scores) return false
  return dashboardData.value.phase_scores.some(
    (p: any) => p.weighted_score !== undefined && p.weighted_score !== null
  ) || dashboardData.value.phase_scores.some(
    (p) => p.score !== null && p.score !== undefined
  )
})

const detailColumns = [
  {
    title: '指标名称',
    key: 'indicator_name',
    render: (row: any) => h('span', { style: 'font-weight: 500;' }, row.indicator_name)
  },
  {
    title: '所属阶段',
    key: 'phase_name',
    width: 100,
    render: (row: any) => h(NTag, { size: 'small', type: 'info' }, { default: () => row.phase_name })
  },
  {
    title: '权重',
    key: 'weight',
    width: 80,
    render: (row: any) => `${row.weight}%`
  },
  {
    title: '得分',
    key: 'score',
    width: 100,
    render: (row: any) => {
      if (row.score === null || row.score === undefined) {
        return h('span', { style: 'color: #ccc;' }, '--')
      }
      const color = getScoreColor(row.score)
      return h('span', { style: `color: ${color}; font-weight: 600; font-size: 15px;` }, `${row.score}`)
    }
  },
  {
    title: '维度',
    key: 'dimension_label',
    width: 100,
    render: (row: any) => row.dimension_label || '--'
  },
  {
    title: '得分率',
    key: 'rate',
    width: 120,
    render: (row: any) => {
      if (row.score === null || row.score === undefined) return '--'
      const pct = Math.round(row.score)
      const color = pct >= 90 ? '#18a058' : pct >= 60 ? '#f0a020' : '#d03050'
      return h('span', { style: `color: ${color};` }, `${pct}%`)
    }
  }
]

function getScoreColor(score: number | null | undefined): string {
  if (score === null || score === undefined) return '#999'
  if (score >= 90) return '#18a058'
  if (score >= 60) return '#f0a020'
  return '#d03050'
}

function getScoreTagType(score: number | null | undefined): 'success' | 'warning' | 'error' | 'default' {
  if (score === null || score === undefined) return 'default'
  if (score >= 90) return 'success'
  if (score >= 60) return 'warning'
  return 'error'
}

function getScoreLevel(score: number | null | undefined): string {
  if (score === null || score === undefined) return '未评'
  if (score >= 90) return '优秀'
  if (score >= 80) return '良好'
  if (score >= 70) return '中等'
  if (score >= 60) return '及格'
  return '不及格'
}

function buildDetailTable(dashboard: DashboardData): any[] {
  const rows: any[] = []
  const dimMap: Record<string, string> = {
    knowledge: '知识基础', skill: '工法能力', quality: '职业素养', innovation: '创新贡献'
  }
  if (dashboard.phase_scores) {
    for (const phase of dashboard.phase_scores) {
      // 展示指标级别明细
      if (phase.indicators && phase.indicators.length > 0) {
        for (const ind of phase.indicators) {
          rows.push({
            indicator_name: ind.name,
            phase_name: phase.phase_name,
            weight: ind.weight,
            score: ind.normalized_score ?? ind.score,
            dimension_label: '--'
          })
        }
      } else if (phase.score !== null && phase.score !== undefined) {
        // 无指标明细时展示阶段汇总
        rows.push({
          indicator_name: phase.phase_name + ' (阶段汇总)',
          phase_name: phase.phase_name,
          weight: phase.phase_weight,
          score: phase.score,
          dimension_label: '--'
        })
      }
    }
  }
  if (dashboard.dim_scores) {
    for (const item of dashboard.dim_scores) {
      rows.push({
        indicator_name: item.dim_label || item.dimension,
        phase_name: '维度',
        weight: 25,
        score: item.score,
        dimension_label: item.dim_label || item.dimension
      })
    }
  }
  return rows
}

/**
 * 简易 Markdown 转 HTML，支持标题、加粗、斜体、列表、换行等基本语法
 */
function renderMarkdown(text: string): string {
  if (!text) return ''
  let html = text
    // Escape HTML special chars
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    // Headings: ### / ## / #
    .replace(/^### (.+)$/gm, '<h4 style="margin:16px 0 8px;font-size:15px;font-weight:600;color:#333;">$1</h4>')
    .replace(/^## (.+)$/gm, '<h3 style="margin:18px 0 10px;font-size:16px;font-weight:700;color:#222;">$1</h3>')
    .replace(/^# (.+)$/gm, '<h2 style="margin:20px 0 12px;font-size:18px;font-weight:700;color:#111;">$1</h2>')
    // Bold
    .replace(/\*\*(.+?)\*\*/g, '<strong style="font-weight:600;">$1</strong>')
    // Italic
    .replace(/\*(.+?)\*/g, '<em>$1</em>')
    // Inline code
    .replace(/`(.+?)`/g, '<code style="background:#f5f5f5;padding:2px 6px;border-radius:3px;font-size:13px;">$1</code>')
    // Unordered list items
    .replace(/^[-*] (.+)$/gm, '<li style="margin:4px 0;">$1</li>')
    // Ordered list items
    .replace(/^\d+\. (.+)$/gm, '<li style="margin:4px 0;">$1</li>')
    // Paragraphs: double newline
    .replace(/\n\n/g, '</p><p style="margin:8px 0;line-height:1.8;">')
    // Single newline to <br>
    .replace(/\n/g, '<br>')

  // Wrap list items in <ul>
  html = html.replace(/((?:<li[^>]*>.*?<\/li>(?:<br>)?)+)/gs, '<ul style="padding-left:20px;margin:8px 0;">$1</ul>')
  // Clean up <br> inside <ul>
  html = html.replace(/<ul[^>]*>(.*?)<\/ul>/gs, (match) => match.replace(/<br>/g, ''))

  return '<div style="line-height:1.8;color:#333;font-size:14px;"><p style="margin:8px 0;line-height:1.8;">' + html + '</p></div>'
}

/**
 * 生成 AI 诊断报告，已缓存则直接使用缓存
 */
async function generateDiagnoseReport() {
  const studentId = userStore.user?.id
  if (!studentId) return

  diagnoseLoading.value = true
  try {
    const res: any = await evalApi.aiDiagnoseStudent(studentId)
    diagnoseReport.value = res?.report || res?.data?.report || res?.content || (typeof res === 'string' ? res : JSON.stringify(res))
  } catch (e: any) {
    console.error('Failed to generate AI diagnose report:', e)
    diagnoseReport.value = null
  } finally {
    diagnoseLoading.value = false
  }
}

/**
 * 绘制阶段得分占比饼图
 */
function drawPieChart() {
  const canvas = pieCanvasRef.value
  if (!canvas || !dashboardData.value?.phase_scores) return

  const phases = dashboardData.value.phase_scores
  // Build pie data: prefer weighted_score from API, fall back to score
  const slices: { name: string; value: number; color: string }[] = []
  const pieColors = ['#3B82F6', '#22C55E', '#F97316', '#8B5CF6', '#EC4899', '#14B8A6']

  for (let i = 0; i < phases.length; i++) {
    const phase: any = phases[i]
    const val = phase.weighted_score ?? phase.score
    if (val !== null && val !== undefined && val > 0) {
      slices.push({
        name: phase.phase_name,
        value: Number(val),
        color: pieColors[i % pieColors.length]
      })
    }
  }

  if (!slices.length) return

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const dpr = window.devicePixelRatio || 1
  const displayWidth = 400
  const displayHeight = 320
  canvas.width = displayWidth * dpr
  canvas.height = displayHeight * dpr
  canvas.style.width = displayWidth + 'px'
  canvas.style.height = displayHeight + 'px'
  ctx.scale(dpr, dpr)

  ctx.clearRect(0, 0, displayWidth, displayHeight)

  const total = slices.reduce((sum, s) => sum + s.value, 0)
  if (total <= 0) return

  const centerX = 170
  const centerY = displayHeight / 2
  const radius = 110
  const innerRadius = 55 // donut chart
  let startAngle = -Math.PI / 2

  // Draw slices
  for (const slice of slices) {
    const sliceAngle = (slice.value / total) * 2 * Math.PI
    const endAngle = startAngle + sliceAngle

    ctx.beginPath()
    ctx.arc(centerX, centerY, radius, startAngle, endAngle)
    ctx.arc(centerX, centerY, innerRadius, endAngle, startAngle, true)
    ctx.closePath()
    ctx.fillStyle = slice.color
    ctx.fill()

    // Slice border
    ctx.strokeStyle = '#fff'
    ctx.lineWidth = 2
    ctx.stroke()

    // Percentage label on the slice
    const midAngle = startAngle + sliceAngle / 2
    const labelRadius = (radius + innerRadius) / 2
    const lx = centerX + labelRadius * Math.cos(midAngle)
    const ly = centerY + labelRadius * Math.sin(midAngle)
    const pct = ((slice.value / total) * 100).toFixed(1)

    ctx.fillStyle = '#fff'
    ctx.font = 'bold 12px sans-serif'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'middle'
    // Only draw on-slice text if slice is large enough
    if (sliceAngle > 0.25) {
      ctx.fillText(pct + '%', lx, ly)
    }

    startAngle = endAngle
  }

  // Center text
  ctx.fillStyle = '#333'
  ctx.font = 'bold 18px sans-serif'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'
  ctx.fillText(total.toFixed(1), centerX, centerY - 8)
  ctx.fillStyle = '#999'
  ctx.font = '11px sans-serif'
  ctx.fillText('总分', centerX, centerY + 12)

  // Legend on the right side
  const legendX = 300
  let legendY = 40
  ctx.textAlign = 'left'
  ctx.textBaseline = 'middle'

  for (const slice of slices) {
    const pct = ((slice.value / total) * 100).toFixed(1)

    // Color indicator
    ctx.fillStyle = slice.color
    ctx.beginPath()
    ctx.roundRect(legendX, legendY - 6, 14, 14, 3)
    ctx.fill()

    // Phase name
    ctx.fillStyle = '#333'
    ctx.font = '13px sans-serif'
    ctx.fillText(slice.name, legendX + 20, legendY + 1)

    // Score and percentage
    ctx.fillStyle = '#666'
    ctx.font = '12px sans-serif'
    ctx.fillText(slice.value.toFixed(1) + ' (' + pct + '%)', legendX + 20, legendY + 18)

    legendY += 40
  }
}

function drawRadarChart() {
  const canvas = radarCanvasRef.value
  if (!canvas || !radarData.value.length) return

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const dpr = window.devicePixelRatio || 1
  const displayWidth = 480
  const displayHeight = 380
  canvas.width = displayWidth * dpr
  canvas.height = displayHeight * dpr
  canvas.style.width = displayWidth + 'px'
  canvas.style.height = displayHeight + 'px'
  ctx.scale(dpr, dpr)

  const centerX = displayWidth / 2
  const centerY = displayHeight / 2 + 5
  const maxRadius = 130
  const axes = radarData.value.length

  ctx.clearRect(0, 0, displayWidth, displayHeight)

  const angleStep = (2 * Math.PI) / axes
  const startAngle = -Math.PI / 2

  // Draw grid rings
  for (let ring = 1; ring <= 5; ring++) {
    const r = (maxRadius / 5) * ring
    ctx.beginPath()
    for (let i = 0; i <= axes; i++) {
      const angle = startAngle + i * angleStep
      const x = centerX + r * Math.cos(angle)
      const y = centerY + r * Math.sin(angle)
      if (i === 0) ctx.moveTo(x, y)
      else ctx.lineTo(x, y)
    }
    ctx.closePath()
    ctx.strokeStyle = ring === 5 ? '#d0d5dd' : '#e8e8e8'
    ctx.lineWidth = 1
    ctx.stroke()

    // Ring labels
    if (ring % 2 === 0 || ring === 5) {
      ctx.fillStyle = '#aaa'
      ctx.font = '10px sans-serif'
      ctx.textAlign = 'right'
      ctx.fillText(String(ring * 20), centerX - 4, centerY - r + 12)
    }
  }

  // Draw axis lines
  for (let i = 0; i < axes; i++) {
    const angle = startAngle + i * angleStep
    ctx.beginPath()
    ctx.moveTo(centerX, centerY)
    ctx.lineTo(
      centerX + maxRadius * Math.cos(angle),
      centerY + maxRadius * Math.sin(angle)
    )
    ctx.strokeStyle = '#d0d5dd'
    ctx.lineWidth = 1
    ctx.stroke()
  }

  // Draw data polygon
  ctx.beginPath()
  for (let i = 0; i <= axes; i++) {
    const idx = i % axes
    const angle = startAngle + idx * angleStep
    const value = Math.min(radarData.value[idx].score, 100)
    const r = (value / 100) * maxRadius
    const x = centerX + r * Math.cos(angle)
    const y = centerY + r * Math.sin(angle)
    if (i === 0) ctx.moveTo(x, y)
    else ctx.lineTo(x, y)
  }
  ctx.closePath()
  ctx.fillStyle = 'rgba(32, 128, 240, 0.2)'
  ctx.fill()
  ctx.strokeStyle = 'rgba(32, 128, 240, 0.8)'
  ctx.lineWidth = 2
  ctx.stroke()

  // Draw data points
  for (let i = 0; i < axes; i++) {
    const angle = startAngle + i * angleStep
    const value = Math.min(radarData.value[i].score, 100)
    const r = (value / 100) * maxRadius
    const x = centerX + r * Math.cos(angle)
    const y = centerY + r * Math.sin(angle)

    ctx.beginPath()
    ctx.arc(x, y, 4, 0, 2 * Math.PI)
    ctx.fillStyle = '#2080f0'
    ctx.fill()
    ctx.strokeStyle = '#fff'
    ctx.lineWidth = 2
    ctx.stroke()
  }

  // Draw labels
  ctx.fillStyle = '#333'
  ctx.font = '13px sans-serif'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'

  for (let i = 0; i < axes; i++) {
    const angle = startAngle + i * angleStep
    const labelR = maxRadius + 28
    let x = centerX + labelR * Math.cos(angle)
    let y = centerY + labelR * Math.sin(angle)

    // Adjust text alignment based on position
    if (Math.abs(Math.cos(angle)) > 0.5) {
      ctx.textAlign = Math.cos(angle) > 0 ? 'left' : 'right'
      x += Math.cos(angle) > 0 ? -6 : 6
    }

    const label = radarData.value[i].dim_label
    const scoreText = radarData.value[i].score.toFixed(1)
    ctx.fillStyle = '#333'
    ctx.fillText(label, x, y - 8)
    ctx.fillStyle = '#2080f0'
    ctx.font = 'bold 12px sans-serif'
    ctx.fillText(scoreText, x, y + 10)
    ctx.font = '13px sans-serif'
  }
}

function drawTrendChart() {
  const canvas = trendCanvasRef.value
  if (!canvas || !trendPoints.value.length) return

  const ctx = canvas.getContext('2d')
  if (!ctx) return

  const dpr = window.devicePixelRatio || 1
  const displayWidth = 500
  const displayHeight = 300
  canvas.width = displayWidth * dpr
  canvas.height = displayHeight * dpr
  canvas.style.width = displayWidth + 'px'
  canvas.style.height = displayHeight + 'px'
  ctx.scale(dpr, dpr)

  const padding = { top: 30, right: 30, bottom: 50, left: 50 }
  const chartW = displayWidth - padding.left - padding.right
  const chartH = displayHeight - padding.top - padding.bottom

  ctx.clearRect(0, 0, displayWidth, displayHeight)

  const points = trendPoints.value
  const maxVal = 100
  const minVal = 0

  // Draw background grid
  ctx.strokeStyle = '#f0f0f0'
  ctx.lineWidth = 1
  for (let i = 0; i <= 5; i++) {
    const y = padding.top + (chartH / 5) * i
    ctx.beginPath()
    ctx.moveTo(padding.left, y)
    ctx.lineTo(padding.left + chartW, y)
    ctx.stroke()

    // Y-axis labels
    ctx.fillStyle = '#999'
    ctx.font = '11px sans-serif'
    ctx.textAlign = 'right'
    ctx.textBaseline = 'middle'
    const val = maxVal - (maxVal - minVal) * (i / 5)
    ctx.fillText(String(Math.round(val)), padding.left - 8, y)
  }

  // X-axis labels
  const stepX = chartW / Math.max(points.length - 1, 1)
  ctx.fillStyle = '#999'
  ctx.font = '11px sans-serif'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'top'

  const labelStep = Math.max(1, Math.floor(points.length / 8))
  for (let i = 0; i < points.length; i += labelStep) {
    const x = padding.left + i * stepX
    const label = points[i].date.length > 5 ? points[i].date.slice(5) : points[i].date
    ctx.fillText(label, x, padding.top + chartH + 10)
  }

  // Draw the line for total_score
  if (points.length > 1) {
    // Fill area under the line
    ctx.beginPath()
    for (let i = 0; i < points.length; i++) {
      const x = padding.left + i * stepX
      const y = padding.top + chartH - ((points[i].total_score - minVal) / (maxVal - minVal)) * chartH
      if (i === 0) ctx.moveTo(x, y)
      else ctx.lineTo(x, y)
    }
    ctx.lineTo(padding.left + (points.length - 1) * stepX, padding.top + chartH)
    ctx.lineTo(padding.left, padding.top + chartH)
    ctx.closePath()
    ctx.fillStyle = 'rgba(32, 128, 240, 0.1)'
    ctx.fill()

    // Draw the line
    ctx.beginPath()
    for (let i = 0; i < points.length; i++) {
      const x = padding.left + i * stepX
      const y = padding.top + chartH - ((points[i].total_score - minVal) / (maxVal - minVal)) * chartH
      if (i === 0) ctx.moveTo(x, y)
      else ctx.lineTo(x, y)
    }
    ctx.strokeStyle = '#2080f0'
    ctx.lineWidth = 2.5
    ctx.lineJoin = 'round'
    ctx.stroke()

    // Draw data points
    for (let i = 0; i < points.length; i++) {
      const x = padding.left + i * stepX
      const y = padding.top + chartH - ((points[i].total_score - minVal) / (maxVal - minVal)) * chartH

      ctx.beginPath()
      ctx.arc(x, y, 3.5, 0, 2 * Math.PI)
      ctx.fillStyle = '#2080f0'
      ctx.fill()
      ctx.strokeStyle = '#fff'
      ctx.lineWidth = 2
      ctx.stroke()
    }
  } else if (points.length === 1) {
    // Single point
    const x = padding.left + chartW / 2
    const y = padding.top + chartH - ((points[0].total_score - minVal) / (maxVal - minVal)) * chartH
    ctx.beginPath()
    ctx.arc(x, y, 5, 0, 2 * Math.PI)
    ctx.fillStyle = '#2080f0'
    ctx.fill()
    ctx.strokeStyle = '#fff'
    ctx.lineWidth = 2
    ctx.stroke()

    // Show score label
    ctx.fillStyle = '#333'
    ctx.font = 'bold 13px sans-serif'
    ctx.textAlign = 'center'
    ctx.textBaseline = 'bottom'
    ctx.fillText(String(points[0].total_score), x, y - 10)
  }

  // Legend
  ctx.fillStyle = '#2080f0'
  ctx.fillRect(displayWidth - padding.right - 80, 8, 14, 3)
  ctx.fillStyle = '#666'
  ctx.font = '11px sans-serif'
  ctx.textAlign = 'left'
  ctx.textBaseline = 'middle'
  ctx.fillText('总分', displayWidth - padding.right - 62, 10)

  // Chart title
  ctx.fillStyle = '#999'
  ctx.font = '11px sans-serif'
  ctx.textAlign = 'left'
  ctx.fillText('Y: 分数 (0-100)', padding.left, 12)
}

async function loadData() {
  const studentId = userStore.user?.id
  if (!studentId) return

  loading.value = true
  try {
    // 检查成绩可见性
    try {
      const settings = await authApi.getSettings() as any
      gradesVisible.value = settings.student_view_grades !== false
    } catch {
      gradesVisible.value = true
    }

    if (!gradesVisible.value) {
      loading.value = false
      return
    }

    const [dashboard, radar, trend] = await Promise.all([
      evalApi.getStudentDashboard(studentId) as any,
      evalApi.getStudentRadar(studentId) as any,
      evalApi.getStudentTrend(studentId) as any
    ])

    dashboardData.value = dashboard
    phaseScores.value = dashboard.phase_scores || []
    detailTableData.value = buildDetailTable(dashboard)
    radarData.value = radar || []
    trendPoints.value = trend?.points || []

    await nextTick()
    drawPieChart()
    drawRadarChart()
    drawTrendChart()
  } catch (e: any) {
    console.error('Failed to load process evaluation data:', e)
    dashboardData.value = null
    phaseScores.value = []
    detailTableData.value = []
    radarData.value = []
    trendPoints.value = []
  } finally {
    loading.value = false
  }
}

// Redraw on window resize
function handleResize() {
  drawPieChart()
  drawRadarChart()
  drawTrendChart()
}

onMounted(() => {
  loadData()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
.process-eval-container {
  max-width: 1200px;
  margin: 0 auto;
  padding: 0 4px;
}

.page-title {
  margin: 0 0 24px;
  font-size: 20px;
  font-weight: 600;
}

.total-score-card :deep(.n-statistic .n-statistic-value__content) {
  font-size: 36px;
  font-weight: 700;
}

.phase-card {
  text-align: center;
  padding: 20px 12px;
  border-radius: 8px;
  background: #fafafa;
  transition: box-shadow 0.2s;
}

.phase-card:hover {
  box-shadow: 0 2px 12px rgba(0, 0, 0, 0.06);
}

.phase-name {
  font-size: 14px;
  color: #666;
  margin-bottom: 8px;
  font-weight: 500;
}

.phase-score {
  font-size: 32px;
  font-weight: 700;
  line-height: 1.2;
  margin-bottom: 4px;
}

.phase-weight {
  font-size: 12px;
  color: #999;
  margin-bottom: 12px;
}

.phase-bar {
  height: 6px;
  background: #eee;
  border-radius: 3px;
  overflow: hidden;
}

.phase-bar-fill {
  height: 100%;
  border-radius: 3px;
  transition: width 0.6s ease;
}

.chart-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.radar-canvas,
.trend-canvas,
.pie-canvas {
  display: block;
}

.chart-empty {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}

.ai-report-content {
  background: #f8f9fa;
  border: 1px solid #e8e8e8;
  border-radius: 8px;
  padding: 20px 24px;
  min-height: 80px;
}

.ai-report-content :deep(h2),
.ai-report-content :deep(h3),
.ai-report-content :deep(h4) {
  border-bottom: 1px solid #eee;
  padding-bottom: 6px;
}

.ai-report-content :deep(ul) {
  list-style-type: disc;
}

.ai-report-content :deep(code) {
  background: #f0f0f0;
  padding: 1px 4px;
  border-radius: 3px;
}
</style>
