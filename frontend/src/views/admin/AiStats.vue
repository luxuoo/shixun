<template>
  <div class="ai-stats-container">
    <h2 style="margin-bottom: 24px;">AI 使用统计</h2>

    <n-spin :show="loading">
      <!-- 统计卡片 -->
      <n-grid :cols="3" :x-gap="16" :y-gap="16" style="margin-bottom: 32px;">
        <n-gi>
          <n-card>
            <n-statistic label="总调用次数" :value="stats.total_calls">
              <template #prefix>
                <n-icon color="#2080f0" size="24"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M19.35 10.04C18.67 6.59 15.64 4 12 4 9.11 4 6.6 5.64 5.35 8.04 2.34 8.36 0 10.91 0 14c0 3.31 2.69 6 6 6h13c2.76 0 5-2.24 5-5 0-2.64-2.05-4.78-4.65-4.96z"/></svg></n-icon>
              </template>
            </n-statistic>
          </n-card>
        </n-gi>
        <n-gi>
          <n-card>
            <n-statistic label="Token 使用量" :value="stats.total_tokens">
              <template #prefix>
                <n-icon color="#18a058" size="24"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg></n-icon>
              </template>
            </n-statistic>
          </n-card>
        </n-gi>
        <n-gi>
          <n-card>
            <n-statistic label="今日调用" :value="todayCalls">
              <template #prefix>
                <n-icon color="#f0a020" size="24"><svg viewBox="0 0 24 24"><path fill="currentColor" d="M11.99 2C6.47 2 2 6.48 2 12s4.47 10 9.99 10C17.52 22 22 17.52 22 12S17.52 2 11.99 2zM12 20c-4.42 0-8-3.58-8-8s3.58-8 8-8 8 3.58 8 8-3.58 8-8 8zm.5-13H11v6l5.25 3.15.75-1.23-4.5-2.67z"/></svg></n-icon>
              </template>
            </n-statistic>
          </n-card>
        </n-gi>
      </n-grid>

      <!-- 图表区域 -->
      <n-grid :cols="2" :x-gap="16" :y-gap="16" style="margin-bottom: 32px;">
        <n-gi>
          <n-card title="调用类型分布" style="height: 350px;">
            <div ref="typeChartRef" style="width: 100%; height: 280px;"></div>
          </n-card>
        </n-gi>
        <n-gi>
          <n-card title="提示级别分布" style="height: 350px;">
            <div ref="levelChartRef" style="width: 100%; height: 280px;"></div>
          </n-card>
        </n-gi>
      </n-grid>

      <!-- 每日调用趋势 -->
      <n-card title="每日调用趋势" style="margin-bottom: 32px;">
        <div ref="dailyChartRef" style="width: 100%; height: 300px;"></div>
      </n-card>

      <!-- 详细数据 -->
      <n-grid :cols="2" :x-gap="16">
        <n-gi>
          <n-card title="调用类型统计">
            <n-data-table
              :columns="typeColumns"
              :data="typeData"
              :bordered="false"
            />
          </n-card>
        </n-gi>
        <n-gi>
          <n-card title="提示级别统计">
            <n-data-table
              :columns="levelColumns"
              :data="levelData"
              :bordered="false"
            />
          </n-card>
        </n-gi>
      </n-grid>
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue'
import { NTag } from 'naive-ui'
import { adminApi } from '@/api'

const loading = ref(false)

const stats = ref({
  total_calls: 0,
  total_tokens: 0,
  type_distribution: {} as Record<string, number>,
  level_distribution: {} as Record<string, number>,
  daily_calls: [] as { date: string; count: number }[]
})

const todayCalls = computed(() => {
  const today = new Date().toISOString().split('T')[0]
  const todayData = stats.value.daily_calls.find(d => d.date === today)
  return todayData?.count || 0
})

const typeColumns = [
  { title: '类型', key: 'type' },
  { title: '次数', key: 'count' },
  {
    title: '占比',
    key: 'percentage',
    render: (row: any) => {
      const total = stats.value.total_calls || 1
      return `${((row.count / total) * 100).toFixed(1)}%`
    }
  }
]

const levelColumns = [
  { title: '级别', key: 'level' },
  { title: '次数', key: 'count' },
  {
    title: '占比',
    key: 'percentage',
    render: (row: any) => {
      const total = Object.values(stats.value.level_distribution).reduce((a, b) => a + b, 0) || 1
      return `${((row.count / total) * 100).toFixed(1)}%`
    }
  }
]

const typeData = computed(() => {
  return Object.entries(stats.value.type_distribution).map(([type, count]) => ({
    type: getTypeLabel(type),
    count
  }))
})

const levelData = computed(() => {
  return Object.entries(stats.value.level_distribution).map(([level, count]) => ({
    level: getLevelLabel(level),
    count
  }))
})

function getTypeLabel(type: string) {
  const labels: Record<string, string> = {
    'hint': '提示请求',
    'analyze': '代码分析',
    'score': '代码评分'
  }
  return labels[type] || type
}

function getLevelLabel(level: string) {
  const labels: Record<string, string> = {
    'level_1': '一级提示（思路）',
    'level_2': '二级提示（API）',
    'level_3': '三级提示（代码）'
  }
  return labels[level] || level
}

async function loadStats() {
  loading.value = true
  try {
    const data = await adminApi.getAiStats() as any
    stats.value = {
      total_calls: Object.values(data.type_distribution || {}).reduce((a: any, b: any) => a + b, 0) as number,
      total_tokens: data.total_tokens || 0,
      type_distribution: data.type_distribution || {},
      level_distribution: data.level_distribution || {},
      daily_calls: data.daily_calls || []
    }
  } catch (error) {
    console.error('加载 AI 统计失败', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.ai-stats-container {
  max-width: 1400px;
  margin: 0 auto;
}
</style>
