<template>
  <div class="scores-container">
    <h2 class="page-title">我的成绩</h2>

    <!-- 成绩查看关闭提示 -->
    <n-card v-if="gradesDisabled">
      <n-empty description="成绩查看功能暂未开放，请等待教师开启" style="padding: 60px 0;" />
    </n-card>

    <template v-else>
      <!-- 方案信息 -->
      <n-card v-if="gradeData.scheme" style="margin-bottom: 20px;">
        <n-space align="center" justify="space-between">
          <n-space align="center" :size="16">
            <n-tag type="info" size="large">{{ gradeData.scheme.name }}</n-tag>
            <span v-if="gradeData.total_score !== null && gradeData.total_score !== undefined" style="font-size: 28px; font-weight: 700;" :style="{ color: getScoreColor(gradeData.total_score) }">
              {{ gradeData.total_score }}分
            </span>
          </n-space>
          <n-text depth="3">小数位数: {{ gradeData.scheme.decimal_places }}</n-text>
        </n-space>
      </n-card>

      <!-- 各项分数 -->
      <n-card v-if="gradeData.items?.length">
        <n-data-table :columns="columns" :data="gradeData.items" :bordered="false" />
      </n-card>

      <n-empty v-if="!gradeData.items?.length && !loading" description="暂无成绩数据" style="padding: 60px 0;" />
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted, h } from 'vue'
import { NTag, NProgress } from 'naive-ui'
import { adminApi } from '@/api'

const loading = ref(false)
const gradesDisabled = ref(false)
const gradeData = ref<any>({ scheme: null, items: [], total_score: null })

const columns = [
  { title: '项目', key: 'item_name', render: (row: any) => h('span', { style: 'font-weight: 500;' }, row.item_name) },
  { title: '权重', key: 'weight', width: 80, render: (row: any) => `${row.weight}%` },
  { title: '满分', key: 'max_score', width: 80 },
  { title: '得分', key: 'score', width: 100, render: (row: any) => {
    if (row.score === null || row.score === undefined) return h('span', { style: 'color: #ccc' }, '未录入')
    if (row.status === 'absent') return h(NTag, { type: 'error', size: 'small' }, { default: () => '缺考' })
    const pct = row.score / row.max_score
    const color = pct >= 0.9 ? '#18a058' : pct >= 0.6 ? '#f0a020' : '#d03050'
    return h('span', { style: `color: ${color}; font-weight: 600; font-size: 16px;` }, `${row.score}`)
  }},
  { title: '得分率', key: 'rate', width: 140, render: (row: any) => {
    if (row.score === null || row.score === undefined) return '-'
    const pct = Math.round(row.score / row.max_score * 100)
    return h(NProgress, { type: 'line', percentage: pct, status: pct >= 90 ? 'success' : pct >= 60 ? 'info' : 'error', showIndicator: true, indicatorPlacement: 'inside' })
  }},
  { title: '备注', key: 'remark', width: 100, render: (row: any) => row.remark || '-' }
]

function getScoreColor(score: number) {
  if (score >= 90) return '#18a058'
  if (score >= 60) return '#f0a020'
  return '#d03050'
}

async function loadGrades() {
  loading.value = true
  try {
    const data = await adminApi.getStudentGrades() as any
    gradeData.value = data
  } catch (e: any) {
    if (e?.detail?.includes('暂未开放')) {
      gradesDisabled.value = true
    }
  } finally { loading.value = false }
}

onMounted(() => { loadGrades() })
</script>

<style scoped>
.scores-container { max-width: 900px; margin: 0 auto; }
.page-title { margin: 0 0 24px; font-size: 20px; }
</style>
