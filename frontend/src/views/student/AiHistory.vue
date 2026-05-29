<template>
  <div class="ai-history-container">
    <div class="page-header">
      <h2>AI 对话历史</h2>
      <n-select v-model:value="filterType" :options="typeOptions" placeholder="筛选类型" clearable style="width: 140px;" @update:value="loadHistory" />
    </div>

    <n-spin :show="loading">
      <n-empty v-if="!loading && history.length === 0" description="暂无 AI 对话记录" style="padding: 80px 0;" />
      <div v-else class="history-list">
        <div v-for="item in history" :key="item.id" class="history-card">
          <div class="history-header">
            <n-tag :type="getTypeTag(item.request_type)" size="small" round>{{ getTypeLabel(item) }}</n-tag>
            <span class="history-time">{{ formatTime(item.created_at) }}</span>
          </div>
          <div class="history-content markdown-body" v-html="renderMarkdown(truncate(item.response_content, 500))"></div>
        </div>
      </div>
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { marked } from 'marked'
import { aiApi } from '@/api'

marked.setOptions({ breaks: true, gfm: true } as any)

const loading = ref(false)
const history = ref<any[]>([])
const filterType = ref<string | null>(null)

const typeOptions = [
  { label: '提示', value: 'hint' },
  { label: '代码分析', value: 'analyze' },
  { label: 'AI 评分', value: 'score' }
]

function getTypeTag(type: string) {
  return ({ hint: 'info', analyze: 'success', score: 'warning' } as any)[type] || 'default'
}

function getTypeLabel(item: any) {
  const m: Record<string, string> = { hint: '获取提示', analyze: '代码分析', score: 'AI 评分' }
  let label = m[item.request_type] || item.request_type
  if (item.request_type === 'hint' && item.hint_level) label += ` L${item.hint_level}`
  return label
}

function truncate(text: string, max: number) {
  if (!text) return ''
  return text.length > max ? text.substring(0, max) + '...' : text
}

function renderMarkdown(content: string): string {
  try { return marked.parse(content || '') as string } catch { return content }
}

function formatTime(time: string) {
  if (!time) return ''
  return new Date(time).toLocaleString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
}

async function loadHistory() {
  loading.value = true
  try {
    const data = await aiApi.getHistory() as any
    let items = Array.isArray(data) ? data : []
    if (filterType.value) items = items.filter((i: any) => i.request_type === filterType.value)
    history.value = items
  } catch {} finally { loading.value = false }
}

onMounted(() => { loadHistory() })
</script>

<style scoped>
.ai-history-container { max-width: 900px; margin: 0 auto; }

.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 24px; }
.page-header h2 { margin: 0; font-size: 20px; }

.history-list { display: flex; flex-direction: column; gap: 12px; }

.history-card {
  background: #fff;
  border: 1px solid #e8e8ec;
  border-radius: 12px;
  padding: 16px 20px;
}

.history-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 10px;
}

.history-time {
  font-size: 12px;
  color: #999;
}

.history-content {
  font-size: 14px;
  line-height: 1.7;
  color: #333;
}

.history-content :deep(p) { margin: 0 0 6px; }
.history-content :deep(p:last-child) { margin-bottom: 0; }
.history-content :deep(code) { background: #f0f0f4; padding: 2px 6px; border-radius: 4px; font-size: 13px; }
.history-content :deep(pre) { background: #1e1e2d; color: #e0e0e0; padding: 12px; border-radius: 8px; overflow-x: auto; margin: 8px 0; }
.history-content :deep(pre code) { background: none; padding: 0; color: inherit; }
.history-content :deep(ul), .history-content :deep(ol) { padding-left: 20px; margin: 4px 0; }
.history-content :deep(strong) { font-weight: 600; }
</style>
