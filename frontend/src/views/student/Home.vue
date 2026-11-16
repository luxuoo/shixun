<template>
  <div class="home-container">
    <!-- 欢迎横幅 -->
    <div class="hero-banner">
      <div class="hero-content">
        <div class="hero-text">
          <h1>{{ greeting }}，{{ userStore.user?.name || userStore.user?.username }}</h1>
          <p>今天也要加油学习哦，坚持就是胜利</p>
        </div>
        <div class="hero-stats">
          <div class="hero-stat">
            <span class="hero-stat-num">{{ stats.completedTasks }}</span>
            <span class="hero-stat-label">已完成任务</span>
          </div>
          <div class="hero-stat-divider"></div>
          <div class="hero-stat">
            <span class="hero-stat-num">{{ stats.averageScore.toFixed(0) }}</span>
            <span class="hero-stat-label">平均分</span>
          </div>
          <div class="hero-stat-divider"></div>
          <div class="hero-stat">
            <span class="hero-stat-num">{{ stats.totalSubmissions }}</span>
            <span class="hero-stat-label">提交次数</span>
          </div>
          <div class="hero-stat-divider"></div>
          <div class="hero-stat">
            <span class="hero-stat-num">{{ stats.aiHintsUsed }}</span>
            <span class="hero-stat-label">AI 提问</span>
          </div>
        </div>
      </div>
    </div>

    <!-- 快捷入口 -->
    <div class="quick-grid">
      <div class="quick-card quick-blue" @click="router.push('/tasks')">
        <div class="quick-icon">
          <AoraBot shape="bulb" color="yellow" face="eyes" :sizePx="36" :lineWeight="1.15" seed="q-tasks" />
        </div>
        <div>
          <div class="quick-title">教学任务</div>
          <div class="quick-desc">{{ taskCount }} 个任务可学习</div>
        </div>
      </div>
      <div class="quick-card quick-green" @click="router.push('/submissions')">
        <div class="quick-icon">
          <AoraBot shape="drop" color="cyan" face="eyes" :sizePx="36" :lineWeight="1.15" seed="q-subs" />
        </div>
        <div>
          <div class="quick-title">提交记录</div>
          <div class="quick-desc">查看历史提交和评分</div>
        </div>
      </div>
      <div class="quick-card quick-purple" @click="router.push('/scores')">
        <div class="quick-icon">
          <AoraBot shape="star" color="orange" face="eyes" :sizePx="36" :lineWeight="1.15" seed="q-scores" />
        </div>
        <div>
          <div class="quick-title">成绩总览</div>
          <div class="quick-desc">过程性评价和排名</div>
        </div>
      </div>
      <div class="quick-card quick-orange" @click="router.push('/self-eval')">
        <div class="quick-icon">
          <AoraBot shape="clover" color="green" face="eyes" :sizePx="36" :lineWeight="1.15" seed="q-eval" />
        </div>
        <div>
          <div class="quick-title">自评互评</div>
          <div class="quick-desc">给自己和同学打分</div>
        </div>
      </div>
    </div>

    <!-- 中间区域：学习进度 + 最近提交 -->
    <div class="middle-grid">
      <!-- 学习进度 -->
      <div class="card-section">
        <div class="card-header">
          <span class="card-title">学习进度</span>
        </div>
        <div class="progress-list">
          <div v-for="task in recentTasks" :key="task.id" class="progress-item" @click="router.push(`/tasks/${task.id}`)">
            <div class="progress-info">
              <n-tag :type="getCategoryType(task.category)" size="tiny" round>{{ task.category || '未分类' }}</n-tag>
              <span class="progress-name">{{ task.title }}</span>
            </div>
            <div class="progress-bar-wrap">
              <div class="progress-bar">
                <div class="progress-fill" :style="{ width: getTaskProgress(task) + '%' }"></div>
              </div>
              <span class="progress-pct">{{ getTaskProgress(task) }}%</span>
            </div>
          </div>
          <EmptyState
            v-if="recentTasks.length === 0"
            text="还没有实训任务，等老师布置吧"
            shape="blob" color="violet" state="idle" :sizePx="60"
            seed="home-task-empty"
            class="compact"
          />
        </div>
      </div>

      <!-- 最近提交 -->
      <div class="card-section">
        <div class="card-header">
          <span class="card-title">最近提交</span>
          <n-button text type="primary" size="small" @click="router.push('/submissions')">查看全部</n-button>
        </div>
        <div class="submit-list">
          <div v-for="sub in recentSubmissions" :key="sub.id" class="submit-item">
            <div class="submit-left">
              <span class="submit-task">{{ sub.task_title || `任务 #${sub.task_id}` }}</span>
              <span class="submit-time">{{ formatTime(sub.submitted_at) }}</span>
            </div>
            <div class="submit-right">
              <n-tag :type="getStatusType(sub.status)" size="tiny">{{ getStatusLabel(sub.status) }}</n-tag>
              <span class="submit-score" :style="{ color: getScoreColor(sub.ai_score || sub.final_score) }">
                {{ sub.final_score || sub.ai_score || '--' }}
              </span>
            </div>
          </div>
          <EmptyState
            v-if="recentSubmissions.length === 0"
            text="还没交过作业，去任务列表看看"
            shape="mochi" color="green" state="idle" :sizePx="60"
            seed="home-sub-empty"
            class="compact"
          />
        </div>
      </div>
    </div>

    <!-- 底部：最近任务列表 -->
    <div class="card-section" style="margin-top: 20px;">
      <div class="card-header">
        <span class="card-title">全部任务</span>
        <n-button text type="primary" size="small" @click="router.push('/tasks')">查看全部</n-button>
      </div>
      <div class="task-list">
        <div v-for="task in recentTasks" :key="task.id" class="task-row" @click="router.push(`/tasks/${task.id}`)">
          <div class="task-row-left">
            <n-tag :type="getCategoryType(task.category)" size="small" round>{{ task.category || '未分类' }}</n-tag>
            <span class="task-row-title">{{ task.title }}</span>
          </div>
          <div class="task-row-right">
            <n-rate :value="task.difficulty" :count="5" size="small" readonly />
            <span class="task-row-steps">{{ task.total_steps }} 步骤</span>
            <span class="task-row-hours" v-if="task.estimated_hours">约 {{ task.estimated_hours }}h</span>
            <n-button type="primary" size="tiny" quaternary>进入 →</n-button>
          </div>
        </div>
        <EmptyState
          v-if="recentTasks.length === 0"
          text="还没有实训任务"
          shape="bulb" color="" state="bored" :sizePx="56"
          seed="home-all-tasks"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { useUserStore } from '@/stores/user'
import { taskApi, submissionApi, evalApi, authApi } from '@/api'

const router = useRouter()
const userStore = useUserStore()
const message = useMessage()

const stats = ref({
  completedTasks: 0,
  totalSubmissions: 0,
  aiHintsUsed: 0,
  averageScore: 0
})

const taskCount = ref(0)
const recentTasks = ref<any[]>([])
const recentSubmissions = ref<any[]>([])

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 6) return '夜深了'
  if (h < 12) return '早上好'
  if (h < 14) return '中午好'
  if (h < 18) return '下午好'
  return '晚上好'
})

function getCategoryType(category: string) {
  const types: Record<string, string> = { 'Python': 'info', 'Web': 'success', 'YOLO': 'warning', '数据分析': 'purple', '机器学习': 'error' }
  return types[category] as any || 'info'
}

function getStatusType(status: string) {
  const map: Record<string, string> = { pending: 'warning', ai_scored: 'success', reviewed: 'info' }
  return map[status] as any || 'default'
}

function getStatusLabel(status: string) {
  const map: Record<string, string> = { pending: '待评分', ai_scored: 'AI已评分', reviewed: '已审核' }
  return map[status] || status
}

function getScoreColor(score: number | null) {
  if (!score) return '#5f6673'
  if (score >= 90) return '#18a058'
  if (score >= 60) return '#f0a020'
  return '#d03050'
}

function getTaskProgress(task: any) {
  // 简单估算：根据提交次数和步骤数估算进度
  if (!task.total_steps) return 0
  // 这里用一个简单的估算，实际可以从后端获取
  return Math.min(100, Math.round((task.total_steps * 0.5) / task.total_steps * 100))
}

function formatTime(time: string) {
  if (!time) return ''
  const d = new Date(time)
  const now = new Date()
  const diff = now.getTime() - d.getTime()
  if (diff < 3600000) return `${Math.floor(diff / 60000)} 分钟前`
  if (diff < 86400000) return `${Math.floor(diff / 3600000)} 小时前`
  if (diff < 604800000) return `${Math.floor(diff / 86400000)} 天前`
  return d.toLocaleDateString('zh-CN', { month: 'short', day: 'numeric' })
}

async function loadData() {
  try {
    const [tasks, submissions] = await Promise.all([
      taskApi.getList() as any,
      submissionApi.getList() as any
    ])

    recentTasks.value = (tasks || []).slice(0, 6)
    taskCount.value = (tasks || []).length

    const subs = submissions || []
    recentSubmissions.value = subs.slice(0, 5)
    stats.value.totalSubmissions = subs.length

    const scoredSubs = subs.filter((s: any) => s.ai_score)
    if (scoredSubs.length > 0) {
      stats.value.averageScore = scoredSubs.reduce((sum: number, s: any) => sum + s.ai_score, 0) / scoredSubs.length
    }

    // 统计已完成任务（有 ai_score 且 >= 60 的不同 task_id）
    const completedTaskIds = new Set(
      scoredSubs.filter((s: any) => s.ai_score >= 60).map((s: any) => s.task_id)
    )
    stats.value.completedTasks = completedTaskIds.size

    // 统计 AI 提问次数
    try {
      const aiHistory = await (await import('@/api')).aiApi.getHistory() as any
      stats.value.aiHintsUsed = Array.isArray(aiHistory) ? aiHistory.length : 0
    } catch {
      stats.value.aiHintsUsed = 0
    }
  } catch (error: any) {
    console.error('加载数据失败', error)
  }
}

onMounted(() => { loadData() })
</script>

<style scoped>
.compact {
  padding: 12px 0 10px;
}


.quick-emoji {
  font-size: 25px;
  line-height: 1;
}

.home-container {
  max-width: 1200px;
  margin: 0 auto;
}

/* 欢迎横幅 */
/* 与登录页同一套语言：墨色块 + 细线，不用渐变光斑 */
.hero-banner {
  background: #16171a;
  border-radius: 12px;
  padding: 30px 36px;
  margin-bottom: 20px;
  color: #f4f4f1;
  position: relative;
  overflow: hidden;
}


.hero-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
  position: relative;
  z-index: 1;
}

.hero-text h1 {
  margin: 0 0 8px;
  font-size: 24px;
  font-weight: 700;
}

.hero-text p {
  margin: 0;
  color: rgba(244, 244, 241, 0.68);
  font-size: 14px;
}

.hero-stats {
  display: flex;
  align-items: center;
  gap: 24px;
}

.hero-stat { text-align: center; }

.hero-stat-num {
  display: block;
  font-size: 26px;
  font-weight: 700;
  line-height: 1.2;
  font-variant-numeric: tabular-nums;
}

.hero-stat-label {
  font-size: 12px;
  color: rgba(244, 244, 241, 0.6);
}

.hero-stat-divider {
  width: 1px;
  height: 34px;
  background: rgba(244, 244, 241, 0.18);
}

/* 快捷入口 */
.quick-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
  margin-bottom: 24px;
}

.quick-card {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 18px 20px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  background: #fff;
  border: 1px solid #dcdfe6;
  box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
}

.quick-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.08);
}

.quick-icon {
  width: 44px;
  height: 44px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}

.quick-blue .quick-icon { background: #e8f1ff; color: #1f6feb; }
.quick-green .quick-icon { background: #e8f7ee; color: #12805c; }
.quick-purple .quick-icon { background: #f1e9ff; color: #6d28d9; }
.quick-orange .quick-icon { background: #fff2e0; color: #c2740b; }

.quick-title {
  font-size: 14px;
  font-weight: 600;
  color: #1e1e2d;
}

.quick-desc {
  font-size: 12px;
  color: #5f6673;
  margin-top: 2px;
}

/* 中间两栏 */
.middle-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
}

.card-section {
  background: #fff;
  border-radius: 12px;
  border: 1px solid #dcdfe6;
  padding: 20px;
  box-shadow: 0 1px 2px rgba(16, 24, 40, 0.04);
}

.card-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.card-title {
  font-size: 15px;
  font-weight: 600;
  color: #1e1e2d;
}

/* 学习进度 */
.progress-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.progress-item {
  cursor: pointer;
  padding: 8px 0;
  border-bottom: 1px solid #f5f5f9;
}

.progress-item:last-child { border-bottom: none; }

.progress-info {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-bottom: 6px;
}

.progress-name {
  font-size: 13px;
  font-weight: 500;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.progress-bar-wrap {
  display: flex;
  align-items: center;
  gap: 8px;
}

.progress-bar {
  flex: 1;
  height: 6px;
  background: #f0f0f4;
  border-radius: 3px;
  overflow: hidden;
}

.progress-fill {
  height: 100%;
  border-radius: 3px;
  background: linear-gradient(90deg, #2080f0, #6366f1);
  transition: width 0.6s ease;
}

.progress-pct {
  font-size: 12px;
  font-weight: 600;
  color: #6366f1;
  min-width: 36px;
  text-align: right;
}

/* 最近提交 */
.submit-list {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.submit-item {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  border-bottom: 1px solid #f5f5f9;
}

.submit-item:last-child { border-bottom: none; }

.submit-left {
  display: flex;
  flex-direction: column;
  gap: 2px;
  min-width: 0;
  flex: 1;
}

.submit-task {
  font-size: 13px;
  font-weight: 500;
  color: #333;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.submit-time {
  font-size: 11px;
  color: #8a919e;
}

.submit-right {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
}

.submit-score {
  font-size: 16px;
  font-weight: 700;
  min-width: 32px;
  text-align: right;
}

/* 任务列表 */
.task-list {
  overflow: hidden;
}

.task-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 0;
  cursor: pointer;
  transition: background 0.15s;
  border-bottom: 1px solid #f5f5f9;
}

.task-row:last-child { border-bottom: none; }
.task-row:hover { background: #fafafe; margin: 0 -20px; padding: 14px 20px; border-radius: 8px; }

.task-row-left {
  display: flex;
  align-items: center;
  gap: 12px;
  min-width: 0;
  flex: 1;
}

.task-row-title {
  font-size: 14px;
  font-weight: 500;
  color: #1e1e2d;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.task-row-right {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-shrink: 0;
}

.task-row-steps, .task-row-hours {
  font-size: 12px;
  color: #5f6673;
}

/* 响应式 */
@media (max-width: 768px) {
  .hero-banner { padding: 20px; border-radius: 12px; }
  .hero-content { flex-direction: column; align-items: flex-start; gap: 16px; }
  .hero-text h1 { font-size: 18px; }
  .hero-stats { gap: 16px; }
  .hero-stat-num { font-size: 22px; }
  .quick-grid { grid-template-columns: repeat(2, 1fr); gap: 12px; }
  .quick-card { padding: 14px; }
  .middle-grid { grid-template-columns: 1fr; }
  .task-row { flex-direction: column; align-items: flex-start; gap: 8px; }
  .task-row-right { align-self: flex-end; }
}
</style>
