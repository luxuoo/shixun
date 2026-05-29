<template>
  <div class="task-list-container">
    <div class="page-header">
      <h2>实训任务</h2>
      <n-space>
        <n-select v-model:value="selectedCategory" :options="categoryOptions" placeholder="分类" clearable style="width: 130px;" @update:value="loadTasks" />
        <n-select v-model:value="selectedDifficulty" :options="difficultyOptions" placeholder="难度" clearable style="width: 130px;" @update:value="loadTasks" />
      </n-space>
    </div>

    <n-spin :show="loading">
      <div class="task-grid">
        <div v-for="task in tasks" :key="task.id" class="task-card" @click="router.push(`/tasks/${task.id}`)">
          <div class="task-cover" :style="{ background: getGradient(task.category) }">
            <n-icon size="40" color="rgba(255,255,255,0.8)"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/></svg></n-icon>
          </div>
          <div class="task-body">
            <div class="task-tags">
              <n-tag :type="getCategoryType(task.category)" size="small" round>{{ task.category || '未分类' }}</n-tag>
              <n-tag :type="getDifficultyType(task.difficulty)" size="small">{{ task.difficulty }}星</n-tag>
            </div>
            <h3 class="task-title">{{ task.title }}</h3>
            <p class="task-desc">{{ task.description?.substring(0, 80) }}{{ task.description?.length > 80 ? '...' : '' }}</p>
            <div class="task-meta">
              <span>{{ task.estimated_hours || '? ' }}小时</span>
              <span>{{ task.total_steps }}步</span>
            </div>
          </div>
        </div>
      </div>
      <n-empty v-if="!loading && tasks.length === 0" description="暂无任务" style="padding: 80px 0;" />
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { taskApi } from '@/api'

const router = useRouter()
const loading = ref(false)
const tasks = ref<any[]>([])
const selectedCategory = ref<string | null>(null)
const selectedDifficulty = ref<number | null>(null)

const categoryOptions = [
  { label: 'Python', value: 'Python' },
  { label: 'Web', value: 'Web' },
  { label: 'YOLO', value: 'YOLO' },
  { label: '数据分析', value: '数据分析' },
  { label: '机器学习', value: '机器学习' }
]

const difficultyOptions = [
  { label: '1星 入门', value: 1 },
  { label: '2星 基础', value: 2 },
  { label: '3星 中等', value: 3 },
  { label: '4星 进阶', value: 4 },
  { label: '5星 高级', value: 5 }
]

function getGradient(category: string) {
  const g: Record<string, string> = {
    'Python': 'linear-gradient(135deg, #667eea, #764ba2)',
    'Web': 'linear-gradient(135deg, #f093fb, #f5576c)',
    'YOLO': 'linear-gradient(135deg, #4facfe, #00f2fe)',
    '数据分析': 'linear-gradient(135deg, #43e97b, #38f9d7)',
    '机器学习': 'linear-gradient(135deg, #fa709a, #fee140)'
  }
  return g[category] || 'linear-gradient(135deg, #667eea, #764ba2)'
}

function getCategoryType(category: string) {
  const t: Record<string, string> = { 'Python': 'info', 'Web': 'success', 'YOLO': 'warning' }
  return t[category] as any || 'info'
}

function getDifficultyType(d: number) {
  if (d <= 2) return 'success'
  if (d <= 3) return 'warning'
  return 'error'
}

async function loadTasks() {
  loading.value = true
  try {
    const data = await taskApi.getList(selectedCategory.value || undefined) as any
    tasks.value = data
  } catch {} finally { loading.value = false }
}

onMounted(() => { loadTasks() })
</script>

<style scoped>
.task-list-container {
  max-width: 1100px;
  margin: 0 auto;
}

.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}

.page-header h2 { margin: 0; font-size: 20px; }

.task-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.task-card {
  background: #fff;
  border-radius: 12px;
  border: 1px solid #e8e8ec;
  overflow: hidden;
  cursor: pointer;
  transition: all 0.2s;
}

.task-card:hover {
  transform: translateY(-3px);
  box-shadow: 0 8px 24px rgba(0,0,0,0.08);
  border-color: #d0d0d8;
}

.task-cover {
  height: 120px;
  display: flex;
  align-items: center;
  justify-content: center;
}

.task-body {
  padding: 16px;
}

.task-tags {
  display: flex;
  gap: 8px;
  margin-bottom: 10px;
}

.task-title {
  margin: 0 0 8px;
  font-size: 16px;
  font-weight: 600;
  color: #1e1e2d;
}

.task-desc {
  margin: 0 0 12px;
  font-size: 13px;
  color: #666;
  line-height: 1.5;
}

.task-meta {
  display: flex;
  gap: 16px;
  font-size: 12px;
  color: #999;
}
</style>
