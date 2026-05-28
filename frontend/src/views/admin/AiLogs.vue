<template>
  <div class="ai-logs-container">
    <n-space justify="space-between" align="center" style="margin-bottom: 24px;">
      <h2>AI 调用日志</h2>
      <n-space>
        <n-select
          v-model:value="filterType"
          :options="typeOptions"
          placeholder="筛选类型"
          clearable
          style="width: 150px;"
          @update:value="loadLogs"
        />
      </n-space>
    </n-space>

    <n-card>
      <n-data-table
        :columns="columns"
        :data="logs"
        :loading="loading"
        :bordered="false"
        :pagination="pagination"
        :row-key="(row: any) => row.id"
      />
    </n-card>

    <!-- 日志详情弹窗 -->
    <n-modal v-model:show="showDetail" preset="card" title="日志详情" style="width: 800px">
      <n-space vertical :size="16">
        <n-descriptions bordered :column="2">
          <n-descriptions-item label="ID">{{ detailData.id }}</n-descriptions-item>
          <n-descriptions-item label="用户">{{ detailData.user_name || detailData.username }}</n-descriptions-item>
          <n-descriptions-item label="任务">{{ detailData.task_title || '-' }}</n-descriptions-item>
          <n-descriptions-item label="类型">{{ detailData.request_type }}</n-descriptions-item>
          <n-descriptions-item label="提示级别">{{ detailData.hint_level || '-' }}</n-descriptions-item>
          <n-descriptions-item label="Token 消耗">{{ detailData.tokens_used || 0 }}</n-descriptions-item>
          <n-descriptions-item label="时间" :span="2">{{ detailData.created_at ? new Date(detailData.created_at).toLocaleString() : '-' }}</n-descriptions-item>
        </n-descriptions>

        <div>
          <h4 style="margin: 0 0 8px 0;">请求内容</h4>
          <n-card embedded>
            <pre style="margin: 0; white-space: pre-wrap; font-family: monospace; max-height: 200px; overflow-y: auto;">{{ detailData.request_content || '-' }}</pre>
          </n-card>
        </div>

        <div>
          <h4 style="margin: 0 0 8px 0;">响应内容</h4>
          <n-card embedded>
            <pre style="margin: 0; white-space: pre-wrap; font-family: monospace; max-height: 300px; overflow-y: auto;">{{ detailData.response_content || '-' }}</pre>
          </n-card>
        </div>
      </n-space>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, h } from 'vue'
import { NButton, NTag } from 'naive-ui'
import { adminApi } from '@/api'

const loading = ref(false)
const showDetail = ref(false)
const logs = ref<any[]>([])
const filterType = ref<string | null>(null)
const detailData = ref<any>({})
const total = ref(0)

const typeOptions = [
  { label: '提示', value: 'hint' },
  { label: '代码分析', value: 'analyze' },
  { label: 'AI 评分', value: 'score' }
]

const pagination = reactive({
  page: 1,
  pageSize: 20,
  showSizePicker: true,
  pageSizes: [10, 20, 50, 100],
  itemCount: 0,
  onChange: (page: number) => { pagination.page = page; loadLogs() },
  onUpdatePageSize: (pageSize: number) => { pagination.pageSize = pageSize; pagination.page = 1; loadLogs() }
})

const columns = [
  { title: 'ID', key: 'id', width: 60 },
  {
    title: '用户',
    key: 'user_name',
    render: (row: any) => row.user_name || row.username || '-'
  },
  {
    title: '任务',
    key: 'task_title',
    render: (row: any) => row.task_title || '-'
  },
  {
    title: '类型',
    key: 'request_type',
    width: 100,
    render: (row: any) => {
      const map: Record<string, { label: string; type: string }> = {
        hint: { label: '提示', type: 'info' },
        analyze: { label: '分析', type: 'success' },
        score: { label: '评分', type: 'warning' }
      }
      const info = map[row.request_type] || { label: row.request_type, type: 'default' }
      return h(NTag, { type: info.type as any, size: 'small' }, { default: () => info.label })
    }
  },
  {
    title: '提示级别',
    key: 'hint_level',
    width: 90,
    render: (row: any) => row.hint_level ? `第${row.hint_level}级` : '-'
  },
  {
    title: 'Token',
    key: 'tokens_used',
    width: 80,
    render: (row: any) => row.tokens_used || 0
  },
  {
    title: '请求摘要',
    key: 'request_content',
    ellipsis: { tooltip: true },
    render: (row: any) => {
      const content = row.request_content || '-'
      return content.length > 50 ? content.substring(0, 50) + '...' : content
    }
  },
  {
    title: '时间',
    key: 'created_at',
    width: 160,
    render: (row: any) => row.created_at ? new Date(row.created_at).toLocaleString() : '-'
  },
  {
    title: '操作',
    key: 'actions',
    width: 80,
    render: (row: any) => h(NButton, { type: 'primary', size: 'small', onClick: () => viewDetail(row) }, { default: () => '详情' })
  }
]

function viewDetail(row: any) {
  detailData.value = row
  showDetail.value = true
}

async function loadLogs() {
  loading.value = true
  try {
    const params: any = {
      page: pagination.page,
      page_size: pagination.pageSize
    }
    if (filterType.value) params.request_type = filterType.value
    const data = await adminApi.getAiLogs(params) as any
    logs.value = data.items || []
    total.value = data.total || 0
    pagination.itemCount = data.total || 0
  } catch (error) {
    console.error('加载 AI 日志失败', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadLogs()
})
</script>

<style scoped>
.ai-logs-container {
  max-width: 1400px;
  margin: 0 auto;
}
</style>
