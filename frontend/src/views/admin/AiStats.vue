<template>
  <div class="ai-stats-container">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
      <h2>AI 使用统计</h2>
      <n-button @click="testAiConnection" :loading="testing" type="info">
        测试 AI 连接
      </n-button>
    </div>

    <!-- AI 连接测试结果 -->
    <n-card v-if="testResult" title="AI 连接诊断" style="margin-bottom: 24px;">
      <n-descriptions bordered :column="2">
        <n-descriptions-item label="API 地址">{{ testResult.api_url }}</n-descriptions-item>
        <n-descriptions-item label="模型">{{ testResult.model }}</n-descriptions-item>
        <n-descriptions-item label="API Key">{{ testResult.api_key_prefix }}</n-descriptions-item>
        <n-descriptions-item label="OpenAI 版本">{{ testResult.openai_version }}</n-descriptions-item>
        <n-descriptions-item label="状态" :span="2">
          <n-tag :type="testResult.status === 'ok' ? 'success' : testResult.status === 'content_empty' ? 'warning' : 'error'">
            {{ testResult.status === 'ok' ? '正常' : testResult.status === 'content_empty' ? '响应为空' : testResult.status === 'reasoning_only' ? '仅推理内容' : '连接失败' }}
          </n-tag>
        </n-descriptions-item>
        <n-descriptions-item v-if="testResult.test_result" label="AI 回复" :span="2">
          {{ testResult.test_result.content || '(空)' }}
        </n-descriptions-item>
        <n-descriptions-item v-if="testResult.error" label="错误信息" :span="2">
          <n-text type="error">{{ testResult.error }}</n-text>
        </n-descriptions-item>
      </n-descriptions>
    </n-card>

    <n-spin :show="loading">
      <!-- 统计卡片 -->
      <n-grid :cols="3" :x-gap="16" :y-gap="16" style="margin-bottom: 24px;">
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

      <!-- 调用类型分布 + 提示级别分布 -->
      <n-grid :cols="2" :x-gap="16" :y-gap="16" style="margin-bottom: 24px;">
        <n-gi>
          <n-card title="调用类型分布">
            <n-space vertical :size="12">
              <div v-for="item in typeData" :key="item.type" style="display: flex; align-items: center; gap: 12px;">
                <span style="width: 80px; font-size: 14px;">{{ item.type }}</span>
                <n-progress type="line" :percentage="item.percentage" :color="item.color" style="flex: 1;" />
                <span style="width: 50px; text-align: right; font-size: 14px; font-weight: 500;">{{ item.count }}</span>
              </div>
              <n-empty v-if="typeData.length === 0" description="暂无数据" />
            </n-space>
          </n-card>
        </n-gi>
        <n-gi>
          <n-card title="提示级别分布">
            <n-space vertical :size="12">
              <div v-for="item in levelData" :key="item.level" style="display: flex; align-items: center; gap: 12px;">
                <span style="width: 100px; font-size: 14px;">{{ item.level }}</span>
                <n-progress type="line" :percentage="item.percentage" :color="item.color" style="flex: 1;" />
                <span style="width: 50px; text-align: right; font-size: 14px; font-weight: 500;">{{ item.count }}</span>
              </div>
              <n-empty v-if="levelData.length === 0" description="暂无数据" />
            </n-space>
          </n-card>
        </n-gi>
      </n-grid>

      <!-- 每日调用趋势 -->
      <n-card title="每日调用趋势" style="margin-bottom: 24px;">
        <n-space vertical :size="12">
          <div v-for="item in stats.daily_calls" :key="item.date" style="display: flex; align-items: center; gap: 12px;">
            <span style="width: 80px; font-size: 13px; color: #666;">{{ item.date }}</span>
            <n-progress type="line" :percentage="getDailyPercentage(item.count)" :color="'#2080f0'" style="flex: 1;" />
            <span style="width: 40px; text-align: right; font-size: 14px; font-weight: 500;">{{ item.count }}</span>
          </div>
          <n-empty v-if="!stats.daily_calls.length" description="暂无数据" />
        </n-space>
      </n-card>
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { adminApi } from '@/api'
import api from '@/api'

const loading = ref(false)
const testing = ref(false)
const testResult = ref<any>(null)

const stats = ref({
  total_calls: 0,
  total_tokens: 0,
  type_distribution: {} as Record<string, number>,
  level_distribution: {} as Record<string, number>,
  daily_calls: [] as { date: string; count: number }[]
})

const todayCalls = computed(() => {
  const now = new Date()
  const today = `${now.getFullYear()}-${String(now.getMonth() + 1).padStart(2, '0')}-${String(now.getDate()).padStart(2, '0')}`
  const todayData = stats.value.daily_calls.find(d => d.date === today)
  return todayData?.count || 0
})

const typeData = computed(() => {
  const total = stats.value.total_calls || 1
  const colors: Record<string, string> = { hint: '#2080f0', analyze: '#18a058', score: '#f0a020' }
  const labels: Record<string, string> = { hint: '提示请求', analyze: '代码分析', score: '代码评分' }
  return Object.entries(stats.value.type_distribution).map(([type, count]) => ({
    type: labels[type] || type,
    count,
    percentage: Math.round((count / total) * 100),
    color: colors[type] || '#999'
  }))
})

const levelData = computed(() => {
  const total = Object.values(stats.value.level_distribution).reduce((a, b) => a + b, 0) || 1
  const colors: Record<string, string> = { level_1: '#2080f0', level_2: '#f0a020', level_3: '#d03050' }
  const labels: Record<string, string> = { level_1: '一级（思路）', level_2: '二级（API）', level_3: '三级（代码）' }
  return Object.entries(stats.value.level_distribution).map(([level, count]) => ({
    level: labels[level] || level,
    count,
    percentage: Math.round((count / total) * 100),
    color: colors[level] || '#999'
  }))
})

function getDailyPercentage(count: number) {
  const max = Math.max(...stats.value.daily_calls.map(d => d.count), 1)
  return Math.round((count / max) * 100)
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

async function testAiConnection() {
  testing.value = true
  testResult.value = null
  try {
    const data = await api.get('/admin/ai-test') as any
    testResult.value = data
  } catch (error: any) {
    testResult.value = {
      status: 'error',
      error: error.detail || '测试请求失败'
    }
  } finally {
    testing.value = false
  }
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.ai-stats-container {
  max-width: 1200px;
  margin: 0 auto;
}
</style>
