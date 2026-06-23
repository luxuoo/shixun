<template>
  <div class="scores-container">
    <h2 class="page-title">我的成绩</h2>

    <n-spin :show="loading">
      <!-- Empty state -->
      <template v-if="!loading && !dashboardData">
        <n-card>
          <n-empty description="暂无过程性评价成绩数据" style="padding: 60px 0;" />
        </n-card>
      </template>

      <template v-else-if="dashboardData">
        <!-- Total score card -->
        <n-card class="total-score-card" style="margin-bottom: 20px;">
          <n-space align="center" justify="space-between">
            <n-space align="center" :size="24">
              <div>
                <div style="font-size: 14px; color: #999; margin-bottom: 4px;">过程性评价总分</div>
                <div
                  class="total-score-number"
                  :style="{ color: getScoreColor(dashboardData.total_score) }"
                >
                  {{ dashboardData.total_score ?? '--' }}
                  <span style="font-size: 16px; color: #999; font-weight: 400;">/ 100</span>
                </div>
              </div>
              <n-divider vertical />
              <n-statistic label="评价模板">
                <template #default>
                  <n-tag type="info" size="large">{{ dashboardData.template_name || '默认模板' }}</n-tag>
                </template>
              </n-statistic>
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
            </n-space>
          </n-space>
        </n-card>

        <!-- Phase scores table -->
        <n-card title="阶段得分" style="margin-bottom: 20px;">
          <n-data-table
            :columns="phaseColumns"
            :data="phaseScores"
            :bordered="false"
            :pagination="false"
          />
          <n-empty v-if="!phaseScores.length" description="暂无阶段数据" size="small" style="padding: 40px 0;" />
        </n-card>

        <!-- Radar chart -->
        <n-card title="能力维度雷达图" style="margin-bottom: 20px;">
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

        <!-- Detail table of all indicators -->
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
import { ref, onMounted, onBeforeUnmount, nextTick, h } from 'vue'
import { NTag, NProgress } from 'naive-ui'
import { evalApi } from '@/api'
import { useUserStore } from '@/stores/user'

interface Indicator {
  name: string
  score: number | null
  max_score: number
  weight: number
  normalized_score: number | null
}

interface PhaseScore {
  phase_name: string
  phase_weight: number
  score: number | null
  weighted_score: number | null
  indicators: Indicator[]
}

interface DimScore {
  dimension: string
  dim_label: string
  score: number
  count: number
}

interface DashboardData {
  total_score: number | null
  phase_scores: PhaseScore[]
  dim_scores: DimScore[]
  template_name: string
  student_name: string
}

const userStore = useUserStore()
const loading = ref(false)
const dashboardData = ref<DashboardData | null>(null)
const phaseScores = ref<PhaseScore[]>([])
const radarData = ref<DimScore[]>([])
const detailTableData = ref<any[]>([])

const radarCanvasRef = ref<HTMLCanvasElement | null>(null)

// ---- Columns ----

const phaseColumns = [
  {
    title: '阶段名称',
    key: 'phase_name',
    render: (row: PhaseScore) => h('span', { style: 'font-weight: 500;' }, row.phase_name)
  },
  {
    title: '权重',
    key: 'phase_weight',
    width: 100,
    render: (row: PhaseScore) => `${row.phase_weight}%`
  },
  {
    title: '阶段得分',
    key: 'score',
    width: 120,
    render: (row: PhaseScore) => {
      if (row.score === null || row.score === undefined) {
        return h('span', { style: 'color: #ccc;' }, '未录入')
      }
      const color = getScoreColor(row.score)
      return h('span', { style: `color: ${color}; font-weight: 600; font-size: 16px;` }, `${row.score}`)
    }
  },
  {
    title: '加权得分',
    key: 'weighted_score',
    width: 120,
    render: (row: PhaseScore) => {
      if (row.weighted_score === null || row.weighted_score === undefined) {
        return h('span', { style: 'color: #ccc;' }, '--')
      }
      return h('span', { style: 'font-weight: 600;' }, `${row.weighted_score}`)
    }
  },
  {
    title: '得分率',
    key: 'rate',
    width: 150,
    render: (row: PhaseScore) => {
      if (row.score === null || row.score === undefined) return '-'
      const pct = Math.round(row.score)
      return h(NProgress, {
        type: 'line',
        percentage: pct,
        status: pct >= 90 ? 'success' : pct >= 60 ? 'info' : 'error',
        showIndicator: true,
        indicatorPlacement: 'inside'
      })
    }
  }
]

const detailColumns = [
  {
    title: '指标名称',
    key: 'indicator_name',
    render: (row: any) => h('span', { style: 'font-weight: 500;' }, row.indicator_name)
  },
  {
    title: '所属阶段',
    key: 'phase_name',
    width: 120,
    render: (row: any) => h(NTag, { size: 'small', type: 'info' }, { default: () => row.phase_name })
  },
  {
    title: '权重',
    key: 'weight',
    width: 80,
    render: (row: any) => `${row.weight}%`
  },
  {
    title: '满分',
    key: 'max_score',
    width: 80
  },
  {
    title: '得分',
    key: 'score',
    width: 100,
    render: (row: any) => {
      if (row.score === null || row.score === undefined) {
        return h('span', { style: 'color: #ccc;' }, '未录入')
      }
      const color = getScoreColor(row.normalized_score ?? row.score)
      return h('span', { style: `color: ${color}; font-weight: 600; font-size: 15px;` }, `${row.score}`)
    }
  },
  {
    title: '标准化得分',
    key: 'normalized_score',
    width: 110,
    render: (row: any) => {
      if (row.normalized_score === null || row.normalized_score === undefined) {
        return h('span', { style: 'color: #ccc;' }, '--')
      }
      const color = getScoreColor(row.normalized_score)
      return h('span', { style: `color: ${color}; font-weight: 500;` }, `${row.normalized_score}`)
    }
  },
  {
    title: '得分率',
    key: 'rate',
    width: 130,
    render: (row: any) => {
      if (row.score === null || row.score === undefined) return '--'
      const base = row.normalized_score ?? row.score
      const pct = Math.round(base)
      const color = pct >= 90 ? '#18a058' : pct >= 60 ? '#f0a020' : '#d03050'
      return h(NProgress, {
        type: 'line',
        percentage: pct,
        status: pct >= 90 ? 'success' : pct >= 60 ? 'info' : 'error',
        showIndicator: true,
        indicatorPlacement: 'inside'
      })
    }
  }
]

// ---- Helpers ----

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
  if (dashboard.phase_scores) {
    for (const phase of dashboard.phase_scores) {
      if (phase.indicators && phase.indicators.length) {
        for (const ind of phase.indicators) {
          rows.push({
            indicator_name: ind.name,
            phase_name: phase.phase_name,
            weight: ind.weight,
            max_score: ind.max_score,
            score: ind.score,
            normalized_score: ind.normalized_score
          })
        }
      } else {
        // Phase-level fallback if no indicators
        rows.push({
          indicator_name: phase.phase_name + ' (阶段汇总)',
          phase_name: phase.phase_name,
          weight: phase.phase_weight,
          max_score: 100,
          score: phase.score,
          normalized_score: phase.score
        })
      }
    }
  }
  return rows
}

// ---- Radar chart ----

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
  ctx.font = '13px sans-serif'
  ctx.textAlign = 'center'
  ctx.textBaseline = 'middle'

  for (let i = 0; i < axes; i++) {
    const angle = startAngle + i * angleStep
    const labelR = maxRadius + 28
    let x = centerX + labelR * Math.cos(angle)
    let y = centerY + labelR * Math.sin(angle)

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

// ---- Data loading ----

async function loadData() {
  const studentId = userStore.user?.id
  if (!studentId) return

  loading.value = true
  try {
    const dashboard = await evalApi.getStudentDashboard(studentId) as any as DashboardData

    dashboardData.value = dashboard
    phaseScores.value = dashboard.phase_scores || []
    radarData.value = dashboard.dim_scores || []
    detailTableData.value = buildDetailTable(dashboard)

    await nextTick()
    drawRadarChart()
  } catch (e: any) {
    console.error('Failed to load scores data:', e)
    dashboardData.value = null
    phaseScores.value = []
    radarData.value = []
    detailTableData.value = []
  } finally {
    loading.value = false
  }
}

function handleResize() {
  drawRadarChart()
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
.scores-container {
  max-width: 1000px;
  margin: 0 auto;
  padding: 0 4px;
}

.page-title {
  margin: 0 0 24px;
  font-size: 20px;
  font-weight: 600;
}

.total-score-card :deep(.n-statistic .n-statistic-value__content) {
  font-size: 28px;
  font-weight: 700;
}

.total-score-number {
  font-size: 42px;
  font-weight: 800;
  line-height: 1.2;
}

.chart-wrapper {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 300px;
}

.radar-canvas {
  display: block;
}

.chart-empty {
  display: flex;
  justify-content: center;
  align-items: center;
  min-height: 200px;
}
</style>
