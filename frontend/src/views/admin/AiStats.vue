<template>
  <div class="ai-stats-container">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px;">
      <h2>AI 使用统计</h2>
      <n-button @click="testAiConnection(currentProvider)" :loading="testing" type="info">
        测试 AI 连接
      </n-button>
    </div>

    <!-- AI 服务商 -->
    <n-card title="AI 服务商" style="margin-bottom: 24px;">
      <n-space align="center" :size="16" wrap>
        <div class="provider-current">
          <span class="provider-label">当前使用</span>
          <n-tag :type="providerInfo?.configured ? 'success' : 'error'" size="medium" round>
            {{ providerInfo?.label || '—' }}
          </n-tag>
          <span class="provider-model">{{ providerInfo?.model }}</span>
        </div>
        <n-divider vertical />
        <n-radio-group v-model:value="selectedProvider" size="small">
          <n-radio-button
            v-for="p in providerInfo?.providers || []"
            :key="p.name"
            :value="p.name"
            :disabled="!p.configured"
          >
            {{ p.label }}{{ p.configured ? '' : '（未配置）' }}
          </n-radio-button>
        </n-radio-group>
        <n-button
          size="small"
          type="primary"
          secondary
          :loading="switching"
          :disabled="!selectedProvider || selectedProvider === providerInfo?.provider"
          @click="switchProvider"
        >
          切换
        </n-button>
        <n-button size="small" :loading="testing" @click="testAiConnection(selectedProvider || undefined)">
          测试选中
        </n-button>
      </n-space>
      <p class="provider-tip">
        服务商由 <code>.env</code> 的 <code>AI_PROVIDER</code> 决定；此处切换仅对当前运行生效，重启后以配置为准。
      </p>
    </n-card>

    <!-- AI 连接测试结果 -->
    <n-card v-if="testResult" title="AI 连接诊断" style="margin-bottom: 24px;">
      <n-descriptions bordered :column="2">
        <n-descriptions-item label="服务商">{{ testResult.provider || '—' }}</n-descriptions-item>
        <n-descriptions-item label="API 地址">{{ testResult.api_url }}</n-descriptions-item>
        <n-descriptions-item label="模型">{{ testResult.model }}</n-descriptions-item>
        <n-descriptions-item label="API Key">{{ testResult.api_key_prefix }}</n-descriptions-item>
        <n-descriptions-item label="耗时">{{ testResult.latency_ms }} ms</n-descriptions-item>
        <n-descriptions-item label="OpenAI 版本">{{ testResult.openai_version }}</n-descriptions-item>
        <n-descriptions-item label="状态" :span="2">
          <n-tag :type="testResult.status === 'ok' ? 'success' : 'error'">
            {{ testResult.status === 'ok' ? '正常' : '连接失败' }}
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
                <AoraBot shape="ghost" color="violet" face="eyes" :sizePx="28" :lineWeight="1.15" seed="aistat-calls" />
              </template>
            </n-statistic>
          </n-card>
        </n-gi>
        <n-gi>
          <n-card>
            <n-statistic label="Token 使用量" :value="stats.total_tokens">
              <template #prefix>
                <AoraBot shape="drop" color="cyan" face="eyes" :sizePx="28" :lineWeight="1.15" seed="aistat-tokens" />
              </template>
            </n-statistic>
          </n-card>
        </n-gi>
        <n-gi>
          <n-card>
            <n-statistic label="今日调用" :value="todayCalls">
              <template #prefix>
                <AoraBot shape="bell" color="orange" face="eyes" :sizePx="28" :lineWeight="1.15" seed="aistat-today" />
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
            <span style="width: 80px; font-size: 13px; color: var(--t2);">{{ item.date }}</span>
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
import { useMessage } from 'naive-ui'
import { adminApi } from '@/api'
import api from '@/api'

const message = useMessage()
const loading = ref(false)
const testing = ref(false)
const switching = ref(false)
const testResult = ref<any>(null)
const providerInfo = ref<any>(null)
const selectedProvider = ref<string>('')

const currentProvider = computed(() => providerInfo.value?.provider || '')

async function loadProvider() {
  try {
    const data = (await api.get('/admin/ai-provider')) as any
    providerInfo.value = data
    selectedProvider.value = data.provider
  } catch (error) {
    console.error('加载 AI 服务商信息失败', error)
  }
}

async function switchProvider() {
  if (!selectedProvider.value) return
  switching.value = true
  try {
    const data = (await api.put('/admin/ai-provider', { provider: selectedProvider.value })) as any
    providerInfo.value = { ...providerInfo.value, ...data }
    message.success(`已切换到 ${data.label}`)
    testResult.value = null
  } catch (error: any) {
    message.error(error?.detail || '切换失败')
  } finally {
    switching.value = false
  }
}

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
    color: colors[type] || '#5f6673'
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
    color: colors[level] || '#5f6673'
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

async function testAiConnection(provider?: string) {
  testing.value = true
  testResult.value = null
  try {
    const data = await api.get('/admin/ai-test', {
      params: provider ? { provider } : undefined
    }) as any
    testResult.value = data
  } catch (error: any) {
    testResult.value = {
      status: 'error',
      error: error?.detail || '测试请求失败'
    }
  } finally {
    testing.value = false
  }
}

onMounted(() => {
  loadStats()
  loadProvider()
})
</script>

<style scoped>
.ai-stats-container {
  max-width: 1200px;
  margin: 0 auto;
}

.provider-current {
  display: flex;
  align-items: center;
  gap: 10px;
}

.provider-label {
  font-size: 13px;
  color: var(--t3);
}

.provider-model {
  font-size: 13px;
  font-weight: 600;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}

.provider-tip {
  margin: 12px 0 0;
  font-size: 12px;
  color: var(--t3);
}

.provider-tip code {
  padding: 1px 5px;
  border-radius: 4px;
  background: rgba(148, 163, 184, 0.16);
  color: var(--t2);
  font-size: 11.5px;
}
</style>
