<template>
  <div class="scores-container">
    <n-space align="center" :size="4">
      <h2 class="page-title" style="margin-bottom: 0;">我的成绩</h2>
      <help-icon>这里展示你的过程性评价成绩，包含各阶段得分、能力维度雷达图和成长趋势。总分由多个评价指标按权重加权计算得出。</help-icon>
    </n-space>

    <n-spin :show="loading">
      <!-- 成绩构成说明：把两套评分讲清楚 -->
      <n-card v-if="gradesVisible" class="explain-card" style="margin-bottom: 20px;">
        <div class="explain-title">成绩是怎么算的？</div>
        <div class="explain-grid">
          <div class="explain-item">
            <div class="explain-head"><n-tag type="info" size="small">任务成绩</n-tag></div>
            <p>每次提交由 AI 从正确性、规范性、完成度、创新性四维打分，教师可复核。任务最终分 = AI×权重 + 教师×权重 + 出勤×权重 + 加分（加分直接累加、总分封顶 100）。教师未复核时其权重并入 AI。</p>
          </div>
          <div class="explain-item">
            <div class="explain-head"><n-tag type="success" size="small">过程性评价</n-tag></div>
            <p>按「课前 / 课中 / 课后」等阶段划分，每阶段内若干指标各占权重，阶段得分再按阶段权重加权汇总为过程性评价总分，反映全程表现而非单次作业。</p>
          </div>
        </div>
      </n-card>

      <!-- 任务成绩（含构成明细） -->
      <n-card v-if="gradesVisible && taskScores.length" title="任务成绩" style="margin-bottom: 20px;">
        <n-data-table
          :columns="taskColumns"
          :data="taskScores"
          :bordered="false"
          :pagination="false"
          :row-key="(r: any) => r.id"
        />
      </n-card>

      <!-- 成绩未开放 -->
      <template v-if="!loading && !gradesVisible">
        <n-card class="empty-card">
          <EmptyState text="成绩暂未开放查看，请等待教师开放" shape="bell" color="" state="shy" :sizePx="72" seed="empty-score-lock" />
        </n-card>
      </template>

      <!-- Empty state -->
      <template v-else-if="!loading && !dashboardData">
        <n-card class="empty-card">
          <EmptyState text="暂无过程性评价成绩数据" shape="star" color="" state="bored" :sizePx="72" seed="empty-score" />
        </n-card>
      </template>

      <template v-else-if="dashboardData">
        <!-- Total score card -->
        <n-card class="total-score-card" style="margin-bottom: 20px;">
          <n-space align="center" justify="space-between">
            <n-space align="center" :size="24">
              <div>
                <div style="font-size: 14px; color: var(--t3); margin-bottom: 4px;">过程性评价总分</div>
                <div
                  class="total-score-number"
                  :style="{ color: getScoreColor(dashboardData.total_score) }"
                >
                  {{ dashboardData.total_score ?? '--' }}
                  <span style="font-size: 16px; color: var(--t3); font-weight: 400;">/ 100</span>
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
import { ref, onMounted, onBeforeUnmount, nextTick, watch, h } from 'vue'
import { NTag, NProgress } from 'naive-ui'
import { evalApi, authApi, submissionApi } from '@/api'
import { useUserStore } from '@/stores/user'
import { useThemeStore } from '@/stores/theme'

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
const themeStore = useThemeStore()
const loading = ref(false)
const gradesVisible = ref(true)
const dashboardData = ref<DashboardData | null>(null)
const phaseScores = ref<PhaseScore[]>([])
const radarData = ref<DimScore[]>([])
const detailTableData = ref<any[]>([])
const taskScores = ref<any[]>([])

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
        return h('span', { style: 'color: var(--t4);' }, '未录入')
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
        return h('span', { style: 'color: var(--t4);' }, '--')
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
        return h('span', { style: 'color: var(--t4);' }, '未录入')
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
        return h('span', { style: 'color: var(--t4);' }, '--')
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

// ---- 任务成绩列 + 构成明细 ----

function scoreCell(v: number | null | undefined, bold = false) {
  if (v === null || v === undefined) return h('span', { style: 'color: var(--t4);' }, '—')
  return h('span', { style: `color: ${getScoreColor(v)}; font-weight: ${bold ? 700 : 500};` }, String(v))
}

function renderBreakdown(row: any) {
  const b = row.breakdown
  if (!b) return h('span', { style: 'color: var(--t4);' }, '—')
  const parts: any[] = []
  for (const c of b.components) {
    if (!c.weight) continue
    parts.push(h('span', { class: 'bd-chip' }, `${c.label} ${c.raw ?? '—'} × ${c.weight}% = ${c.contribution}`))
  }
  if (b.bonus) parts.push(h('span', { class: 'bd-chip bd-bonus' }, `+ 加分 ${b.bonus}`))
  if (!b.teacher_reviewed) parts.push(h('span', { class: 'bd-chip bd-note' }, '教师未复核，权重并入 AI'))
  return h('div', { class: 'bd' }, parts)
}

const taskColumns = [
  { title: '任务', key: 'task_title', render: (r: any) => h('span', { style: 'font-weight: 500;' }, r.task_title) },
  { title: 'AI 评分', key: 'ai_total_score', width: 90, render: (r: any) => scoreCell(r.ai_total_score) },
  { title: '教师评分', key: 'teacher_score', width: 90, render: (r: any) => scoreCell(r.teacher_score) },
  { title: '出勤', key: 'attendance_score', width: 70, render: (r: any) => scoreCell(r.attendance_score) },
  { title: '加分', key: 'bonus_score', width: 70, render: (r: any) => scoreCell(r.bonus_score) },
  { title: '最终成绩', key: 'final_score', width: 90, render: (r: any) => scoreCell(r.final_score, true) },
  { title: '构成明细', key: 'breakdown', render: renderBreakdown }
]

// ---- Helpers ----

function getScoreColor(score: number | null | undefined): string {
  if (score === null || score === undefined) return 'var(--t3)'
  if (score >= 90) return 'var(--ok)'
  if (score >= 60) return 'var(--warn-ink)'
  return 'var(--bad)'
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

function cssVar(name: string): string {
  return getComputedStyle(document.documentElement).getPropertyValue(name).trim()
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
    ctx.strokeStyle = ring === 5 ? cssVar('--line-strong') : cssVar('--line')
    ctx.lineWidth = 1
    ctx.stroke()

    // Ring labels
    if (ring % 2 === 0 || ring === 5) {
      ctx.fillStyle = cssVar('--t4')
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
    ctx.strokeStyle = cssVar('--line-strong')
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
    ctx.strokeStyle = cssVar('--c-card')
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
    ctx.fillStyle = cssVar('--t1')
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

    // 任务成绩独立加载：即使过程性评价为空，学生也能看到任务分与构成
    try {
      taskScores.value = (await submissionApi.getMyScores()) as any
    } catch {
      taskScores.value = []
    }

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

watch(() => themeStore.isDark, () => {
  nextTick(drawRadarChart)
})

onMounted(() => {
  loadData()
  window.addEventListener('resize', handleResize)
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
/* 空态卡片：高度定在内容区，并让角色垂直居中 */
.empty-card :deep(.n-card__content) {
  min-height: 320px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.scores-container {
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
  font-size: 28px;
  font-weight: 600;
}

.total-score-number {
  font-size: 42px;
  font-weight: 600;
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

/* 成绩说明 */
.explain-title { font-size: 15px; font-weight: 600; margin-bottom: 12px; color: var(--t1); }
.explain-grid { display: grid; grid-template-columns: 1fr 1fr; gap: 16px; }
.explain-item p { margin: 8px 0 0; font-size: 13px; line-height: 1.7; color: var(--t2); }
@media (max-width: 800px) { .explain-grid { grid-template-columns: 1fr; } }

/* 构成明细 chips */
.bd { display: flex; flex-wrap: wrap; gap: 6px; }
.bd-chip {
  font-size: 12px; color: var(--t2);
  background: var(--c-sunken); border: 1px solid var(--line);
  border-radius: 6px; padding: 2px 8px; white-space: nowrap;
}
.bd-bonus { color: var(--ok); border-color: color-mix(in srgb, var(--ok) 35%, var(--line)); }
.bd-note { color: var(--t3); font-style: italic; }
</style>
