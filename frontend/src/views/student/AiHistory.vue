<template>
  <div class="ai-history-container">
    <n-space justify="space-between" align="center" style="margin-bottom: 24px;">
      <h2>AI 对话历史</h2>
      <n-space>
        <n-select
          v-model:value="filterType"
          :options="typeOptions"
          placeholder="筛选类型"
          clearable
          style="width: 150px;"
          @update:value="loadHistory"
        />
      </n-space>
    </n-space>

    <n-card>
      <n-spin :show="loading">
        <n-empty v-if="!loading && history.length === 0" description="暂无 AI 对话记录" />
        <n-timeline v-else>
          <n-timeline-item
            v-for="item in history"
            :key="item.id"
            :type="getTimelineType(item.request_type)"
            :title="getItemTitle(item)"
            :content="getItemContent(item)"
            :time="formatTime(item.created_at)"
          />
        </n-timeline>
      </n-spin>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { aiApi } from '@/api'

const loading = ref(false)
const history = ref<any[]>([])
const filterType = ref<string | null>(null)

const typeOptions = [
  { label: '提示', value: 'hint' },
  { label: '代码分析', value: 'analyze' },
  { label: 'AI 评分', value: 'score' }
]

function getTimelineType(type: string) {
  const map: Record<string, string> = {
    hint: 'info',
    analyze: 'success',
    score: 'warning'
  }
  return (map[type] || 'default') as any
}

function getItemTitle(item: any) {
  const typeMap: Record<string, string> = {
    hint: '获取提示',
    analyze: '代码分析',
    score: 'AI 评分'
  }
  let title = typeMap[item.request_type] || item.request_type
  if (item.request_type === 'hint' && item.hint_level) {
    title += ` (第${item.hint_level}级)`
  }
  return title
}

function getItemContent(item: any) {
  const response = item.response_content || ''
  // 截断过长的内容
  if (response.length > 300) {
    return response.substring(0, 300) + '...'
  }
  return response
}

function formatTime(time: string) {
  if (!time) return ''
  return new Date(time).toLocaleString('zh-CN')
}

async function loadHistory() {
  loading.value = true
  try {
    const data = await aiApi.getHistory() as any
    let items = Array.isArray(data) ? data : []
    if (filterType.value) {
      items = items.filter((i: any) => i.request_type === filterType.value)
    }
    history.value = items
  } catch (error) {
    console.error('加载 AI 历史失败', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadHistory()
})
</script>

<style scoped>
.ai-history-container {
  max-width: 1000px;
  margin: 0 auto;
}
</style>
