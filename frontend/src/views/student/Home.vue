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
            <span class="hero-stat-label">已完成</span>
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
        </div>
      </div>
    </div>

    <!-- 快捷入口 -->
    <div class="section-title">快捷入口</div>
    <div class="quick-grid">
      <div class="quick-card quick-blue" @click="router.push('/tasks')">
        <n-icon size="32"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/></svg></n-icon>
        <div>
          <div class="quick-title">开始实训</div>
          <div class="quick-desc">查看并完成编程任务</div>
        </div>
      </div>
      <div class="quick-card quick-green" @click="router.push('/submissions')">
        <n-icon size="32"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M9 16.17L4.83 12l-1.42 1.41L9 19 21 7l-1.41-1.41z"/></svg></n-icon>
        <div>
          <div class="quick-title">提交记录</div>
          <div class="quick-desc">查看历史提交和评分</div>
        </div>
      </div>
      <div class="quick-card quick-purple" @click="router.push('/scores')">
        <n-icon size="32"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M5 13.18v4L12 21l7-3.82v-4L12 17l-7-3.82zM12 3L1 9l11 6 9-4.91V17h2V9L12 3z"/></svg></n-icon>
        <div>
          <div class="quick-title">我的成绩</div>
          <div class="quick-desc">查看成绩单和排名</div>
        </div>
      </div>
    </div>

    <!-- 最近任务 -->
    <div class="section-title" style="margin-top: 32px;">最近任务</div>
    <div class="task-list">
      <div v-for="task in recentTasks" :key="task.id" class="task-row" @click="router.push(`/tasks/${task.id}`)">
        <div class="task-row-left">
          <n-tag :type="getCategoryType(task.category)" size="small" round>{{ task.category || '未分类' }}</n-tag>
          <span class="task-row-title">{{ task.title }}</span>
        </div>
        <div class="task-row-right">
          <n-tag :type="getDifficultyType(task.difficulty)" size="small">{{ task.difficulty }}星</n-tag>
          <span class="task-row-steps">{{ task.total_steps }}步</span>
          <n-button type="primary" size="small" quaternary>开始</n-button>
        </div>
      </div>
      <n-empty v-if="recentTasks.length === 0" description="暂无任务" style="padding: 40px 0;" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import { useUserStore } from '@/stores/user'
import { taskApi, submissionApi } from '@/api'

const router = useRouter()
const userStore = useUserStore()
const message = useMessage()

const stats = ref({
  completedTasks: 0,
  totalSubmissions: 0,
  aiHintsUsed: 0,
  averageScore: 0
})

const recentTasks = ref<any[]>([])

const greeting = computed(() => {
  const h = new Date().getHours()
  if (h < 12) return '早上好'
  if (h < 18) return '下午好'
  return '晚上好'
})

function getCategoryType(category: string) {
  const types: Record<string, string> = { 'Python': 'info', 'Web': 'success', 'YOLO': 'warning' }
  return types[category] as any || 'info'
}

function getDifficultyType(difficulty: number) {
  if (difficulty <= 2) return 'success'
  if (difficulty <= 3) return 'warning'
  return 'error'
}

async function loadData() {
  try {
    const tasks = await taskApi.getList() as any
    recentTasks.value = tasks.slice(0, 5)
    const submissions = await submissionApi.getList() as any
    stats.value.totalSubmissions = submissions.length
    const scoredSubmissions = submissions.filter((s: any) => s.ai_score)
    if (scoredSubmissions.length > 0) {
      stats.value.averageScore = scoredSubmissions.reduce((sum: number, s: any) => sum + s.ai_score, 0) / scoredSubmissions.length
    }
  } catch (error: any) {
    message.error(error?.detail || '加载数据失败')
  }
}

onMounted(() => { loadData() })
</script>

<style scoped>
.home-container {
  max-width: 960px;
  margin: 0 auto;
}

.hero-banner {
  background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
  border-radius: 16px;
  padding: 32px 40px;
  margin-bottom: 28px;
  color: white;
}

.hero-content {
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.hero-text h1 {
  margin: 0 0 8px;
  font-size: 24px;
  font-weight: 700;
}

.hero-text p {
  margin: 0;
  opacity: 0.85;
  font-size: 15px;
}

.hero-stats {
  display: flex;
  align-items: center;
  gap: 24px;
}

.hero-stat {
  text-align: center;
}

.hero-stat-num {
  display: block;
  font-size: 28px;
  font-weight: 700;
  line-height: 1.2;
}

.hero-stat-label {
  font-size: 12px;
  opacity: 0.75;
}

.hero-stat-divider {
  width: 1px;
  height: 36px;
  background: rgba(255,255,255,0.25);
}

.section-title {
  font-size: 16px;
  font-weight: 600;
  margin-bottom: 16px;
  color: #1e1e2d;
}

.quick-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.quick-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 20px 24px;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.2s;
  background: #fff;
  border: 1px solid #e8e8ec;
}

.quick-card:hover {
  transform: translateY(-2px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.08);
}

.quick-blue { color: #2080f0; }
.quick-green { color: #18a058; }
.quick-purple { color: #7c3aed; }

.quick-title {
  font-size: 15px;
  font-weight: 600;
  color: #1e1e2d;
}

.quick-desc {
  font-size: 13px;
  color: #999;
  margin-top: 2px;
}

.task-list {
  background: #fff;
  border-radius: 12px;
  border: 1px solid #e8e8ec;
  overflow: hidden;
}

.task-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 14px 20px;
  cursor: pointer;
  transition: background 0.15s;
  border-bottom: 1px solid #f0f0f4;
}

.task-row:last-child { border-bottom: none; }
.task-row:hover { background: #f8f8fc; }

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

.task-row-steps {
  font-size: 13px;
  color: #999;
}

/* 移动端适配 */
@media (max-width: 768px) {
  .hero-banner {
    padding: 20px;
    border-radius: 12px;
  }

  .hero-content {
    flex-direction: column;
    align-items: flex-start;
    gap: 16px;
  }

  .hero-text h1 {
    font-size: 18px;
  }

  .hero-stats {
    gap: 16px;
  }

  .hero-stat-num {
    font-size: 22px;
  }

  .quick-grid {
    grid-template-columns: 1fr;
    gap: 12px;
  }

  .quick-card {
    padding: 16px;
  }

  .task-row {
    flex-direction: column;
    align-items: flex-start;
    gap: 8px;
    padding: 12px 16px;
  }

  .task-row-right {
    align-self: flex-end;
  }
}

@media (min-width: 769px) and (max-width: 1024px) {
  .quick-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}
</style>
