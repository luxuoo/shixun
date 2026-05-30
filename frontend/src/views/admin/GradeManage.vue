<template>
  <div class="grade-manage-container">
    <n-space justify="space-between" align="center" style="margin-bottom: 24px;">
      <h2>成绩管理</h2>
      <n-space>
        <n-select
          v-model:value="selectedClass"
          :options="classOptions"
          placeholder="选择班级"
          clearable
          style="width: 200px;"
          @update:value="loadGrades"
        />
        <n-button @click="exportCSV" :disabled="!gradeData.students?.length">
          导出 CSV
        </n-button>
      </n-space>
    </n-space>

    <n-spin :show="loading">
      <!-- 汇总表格 -->
      <n-card>
        <n-data-table
          :columns="columns"
          :data="gradeData.students || []"
          :bordered="false"
          :scroll-x="scrollX"
          :max-height="600"
          :row-key="(row: any) => row.student_id"
        />
      </n-card>
    </n-spin>

    <!-- 学生详情弹窗 -->
    <n-modal v-model:show="showDetail" preset="card" :title="`${detailStudent?.name} 的成绩详情`" style="width: 700px">
      <n-space vertical :size="16">
        <n-descriptions bordered :column="2">
          <n-descriptions-item label="姓名">{{ detailStudent?.name }}</n-descriptions-item>
          <n-descriptions-item label="学号">{{ detailStudent?.student_no || '-' }}</n-descriptions-item>
          <n-descriptions-item label="班级">{{ detailStudent?.class_name || '-' }}</n-descriptions-item>
          <n-descriptions-item label="平均分">{{ detailStudent?.average_score }}</n-descriptions-item>
          <n-descriptions-item label="总加减分">{{ detailStudent?.total_bonus > 0 ? '+' : '' }}{{ detailStudent?.total_bonus }}</n-descriptions-item>
        </n-descriptions>
        <n-data-table
          :columns="detailColumns"
          :data="detailStudent?.task_scores || []"
          :bordered="false"
        />
      </n-space>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue'
import { NButton, NTag } from 'naive-ui'
import { adminApi, authApi } from '@/api'

const loading = ref(false)
const selectedClass = ref<number | null>(null)
const classOptions = ref<{ label: string; value: number }[]>([])
const gradeData = ref<any>({})
const showDetail = ref(false)
const detailStudent = ref<any>(null)

const scrollX = computed(() => {
  const tasks = gradeData.value.tasks || []
  return 600 + tasks.length * 140
})

const columns = computed(() => {
  const tasks = gradeData.value.tasks || []
  const base = [
    { title: '学号', key: 'student_no', width: 100, fixed: 'left' as const, sorter: (a: any, b: any) => (a.student_no || '').localeCompare(b.student_no || '') },
    { title: '姓名', key: 'name', width: 90, fixed: 'left' as const },
    { title: '班级', key: 'class_name', width: 120 },
  ]
  const taskCols = tasks.map((t: any) => ({
    title: t.title,
    key: `task_${t.id}`,
    width: 130,
    render: (row: any) => {
      const ts = row.task_scores?.find((s: any) => s.task_id === t.id)
      if (!ts || ts.final_score === null) return h('span', { style: 'color: #ccc' }, '-')
      const color = ts.final_score >= 90 ? '#18a058' : ts.final_score >= 60 ? '#f0a020' : '#d03050'
      return h('span', { style: `color: ${color}; font-weight: 500;` }, `${ts.final_score}分`)
    }
  }))
  const tail = [
    { title: '出勤分', key: 'total_attendance', width: 80, render: (row: any) => {
      const a = row.total_attendance || 0
      return h('span', { style: `color: ${a > 0 ? '#2080f0' : '#999'}` }, a || '-')
    }},
    { title: '加减分', key: 'total_bonus', width: 80, render: (row: any) => {
      const b = row.total_bonus || 0
      return h('span', { style: `color: ${b > 0 ? '#18a058' : b < 0 ? '#d03050' : '#999'}` }, b > 0 ? `+${b}` : b || '-')
    }},
    { title: '平均分', key: 'average_score', width: 90, sorter: (a: any, b: any) => (a.average_score || 0) - (b.average_score || 0), render: (row: any) => {
      const s = row.average_score || 0
      const color = s >= 90 ? '#18a058' : s >= 60 ? '#f0a020' : '#d03050'
      return h('span', { style: `color: ${color}; font-weight: bold;` }, `${s}分`)
    }},
    { title: '操作', key: 'actions', width: 80, fixed: 'right' as const, render: (row: any) =>
      h(NButton, { type: 'info', size: 'small', onClick: () => { detailStudent.value = row; showDetail.value = true } }, { default: () => '详情' })
    },
  ]
  return [...base, ...taskCols, ...tail]
})

const detailColumns = [
  { title: '任务', key: 'task_title' },
  { title: 'AI 评分', key: 'ai_score', render: (row: any) => row.ai_score ? `${row.ai_score}分` : '-' },
  { title: '教师评分', key: 'teacher_score', render: (row: any) => row.teacher_score ? `${row.teacher_score}分` : '-' },
  { title: '出勤分', key: 'attendance_score', render: (row: any) => row.attendance_score ? `${row.attendance_score}分` : '-' },
  { title: '加减分', key: 'bonus_score', render: (row: any) => {
    const b = row.bonus_score || 0
    return b ? `${b > 0 ? '+' : ''}${b}分` : '-'
  }},
  { title: '点名', key: 'rollcall_count', render: (row: any) => row.rollcall_count ? `${row.rollcall_count}次` : '-' },
  { title: '最终分数', key: 'final_score', render: (row: any) => {
    if (row.final_score === null) return '-'
    const color = row.final_score >= 90 ? '#18a058' : row.final_score >= 60 ? '#f0a020' : '#d03050'
    return h('span', { style: `color: ${color}; font-weight: bold;` }, `${row.final_score}分`)
  }},
  { title: '状态', key: 'status', render: (row: any) => {
    const map: Record<string, { label: string; type: string }> = {
      not_started: { label: '未开始', type: 'default' },
      in_progress: { label: '进行中', type: 'info' },
      completed: { label: '已完成', type: 'success' },
      reviewed: { label: '已审核', type: 'success' }
    }
    const info = map[row.status] || { label: row.status, type: 'default' }
    return h(NTag, { type: info.type as any, size: 'small' }, { default: () => info.label })
  }}
]

async function loadGrades() {
  loading.value = true
  try {
    const data = await adminApi.getGrades(selectedClass.value || undefined) as any
    gradeData.value = data
  } catch {
  } finally {
    loading.value = false
  }
}

async function loadClasses() {
  try {
    const data = await authApi.getClasses() as any
    classOptions.value = data.map((c: any) => ({ label: c.name, value: c.id }))
  } catch {}
}

function exportCSV() {
  const students = gradeData.value.students || []
  const tasks = gradeData.value.tasks || []
  if (!students.length) return

  let csv = '﻿学号,姓名,班级'
  for (const t of tasks) csv += `,${t.title}`
  csv += ',加减分,平均分\n'

  for (const s of students) {
    csv += `${s.student_no},${s.name},${s.class_name}`
    for (const t of tasks) {
      const ts = s.task_scores?.find((sc: any) => sc.task_id === t.id)
      csv += `,${ts?.final_score ?? ''}`
    }
    csv += `,${s.total_bonus || 0},${s.average_score || 0}\n`
  }

  const blob = new Blob([csv], { type: 'text/csv;charset=utf-8;' })
  const url = URL.createObjectURL(blob)
  const link = document.createElement('a')
  link.href = url
  link.download = `成绩汇总_${new Date().toISOString().slice(0, 10)}.csv`
  link.click()
  URL.revokeObjectURL(url)
}

onMounted(() => {
  loadClasses()
  loadGrades()
})
</script>

<style scoped>
.grade-manage-container {
  max-width: 1400px;
  margin: 0 auto;
}
</style>
