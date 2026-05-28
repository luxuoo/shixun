<template>
  <div class="task-list-container">
    <n-space justify="space-between" align="center" style="margin-bottom: 24px;">
      <h2>实训任务列表</h2>
      <n-space>
        <n-select
          v-model:value="selectedCategory"
          :options="categoryOptions"
          placeholder="选择分类"
          clearable
          style="width: 150px;"
          @update:value="loadTasks"
        />
        <n-select
          v-model:value="selectedDifficulty"
          :options="difficultyOptions"
          placeholder="选择难度"
          clearable
          style="width: 150px;"
          @update:value="loadTasks"
        />
      </n-space>
    </n-space>

    <n-spin :show="loading">
      <n-grid :cols="3" :x-gap="16" :y-gap="16">
        <n-gi v-for="task in tasks" :key="task.id">
          <n-card hoverable class="task-card" @click="router.push(`/tasks/${task.id}`)">
            <template #cover>
              <div class="task-cover" :style="{ background: getGradient(task.category) }">
                <n-icon size="64" color="white" style="opacity: 0.8;">
                  <svg viewBox="0 0 24 24"><path fill="currentColor" d="M19 3H5c-1.1 0-2 .9-2 2v14c0 1.1.9 2 2 2h14c1.1 0 2-.9 2-2V5c0-1.1-.9-2-2-2zm-5 14H7v-2h7v2zm3-4H7v-2h10v2zm0-4H7V7h10v2z"/></svg>
                </n-icon>
              </div>
            </template>

            <n-space vertical :size="12">
              <div>
                <n-tag :type="getCategoryType(task.category)" size="small">
                  {{ task.category || '未分类' }}
                </n-tag>
                <n-tag :type="getDifficultyType(task.difficulty)" size="small" style="margin-left: 8px;">
                  {{ task.difficulty }}星难度
                </n-tag>
              </div>

              <h3 style="margin: 0; font-size: 18px;">{{ task.title }}</h3>

              <p style="color: #666; margin: 0; font-size: 14px; line-height: 1.5;">
                {{ task.description?.substring(0, 100) }}{{ task.description?.length > 100 ? '...' : '' }}
              </p>

              <n-space justify="space-between" align="center" style="margin-top: 12px;">
                <n-space>
                  <n-icon size="16" color="#666"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z"/></svg></n-icon>
                  <span style="font-size: 14px; color: #666;">{{ task.estimated_hours || '未知' }}小时</span>
                </n-space>
                <n-space>
                  <n-icon size="16" color="#666"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M4 6H2v14c0 1.1.9 2 2 2h14v-2H4V6zm16-4H8c-1.1 0-2 .9-2 2v12c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V4c0-1.1-.9-2-2-2zm-1 9h-4v4h-2v-4H9V9h4V5h2v4h4v2z"/></svg></n-icon>
                  <span style="font-size: 14px; color: #666;">{{ task.total_steps }}步</span>
                </n-space>
              </n-space>
            </n-space>
          </n-card>
        </n-gi>
      </n-grid>

      <n-empty v-if="!loading && tasks.length === 0" description="暂无任务" style="margin-top: 80px;" />
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
  { label: '1星 - 入门', value: 1 },
  { label:  '2星 - 基础', value: 2 },
  { label: '3星 - 中等', value: 3 },
  { label: '4星 - 进阶', value: 4 },
  { label: '5星 - 高级', value: 5 }
]

function getGradient(category: string) {
  const gradients: Record<string, string> = {
    'Python': 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)',
    'Web': 'linear-gradient(135deg, #f093fb 0%, #f5576c 100%)',
    'YOLO': 'linear-gradient(135deg, #4facfe 0%, #00f2fe 100%)',
    '数据分析': 'linear-gradient(135deg, #43e97b 0%, #38f9d7 100%)',
    '机器学习': 'linear-gradient(135deg, #fa709a 0%, #fee140 100%)'
  }
  return gradients[category] || 'linear-gradient(135deg, #667eea 0%, #764ba2 100%)'
}

function getCategoryType(category: string) {
  const types: Record<string, string> = {
    'Python': 'info',
    'Web': 'success',
    'YOLO': 'warning',
    '数据分析': 'success',
    '机器学习': 'error'
  }
  return types[category] as any || 'info'
}

function getDifficultyType(difficulty: number) {
  if (difficulty <= 2) return 'success'
  if (difficulty <= 3) return 'warning'
  return 'error'
}

async function loadTasks() {
  loading.value = true
  try {
    const data = await taskApi.getList(selectedCategory.value || undefined) as any
    tasks.value = data
  } catch (error) {
    console.error('加载任务列表失败', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadTasks()
})
</script>

<style scoped>
.task-list-container {
  max-width: 1200px;
  margin: 0 auto;
}

.task-card {
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.task-card:hover {
  transform: translateY(-4px);
  box-shadow: 0 12px 24px rgba(0, 0, 0, 0.1);
}

.task-cover {
  height: 160px;
  display: flex;
  align-items: center;
  justify-content: center;
}
</style>
