<template>
  <div class="grade-manage-container">
    <div class="page-header">
      <h2>成绩管理</h2>
      <n-space>
        <n-select v-model:value="selectedScheme" :options="schemeOptions" placeholder="选择方案" style="width: 180px;" @update:value="loadRecords" />
        <n-select v-model:value="selectedClass" :options="classOptions" placeholder="选择班级" clearable style="width: 160px;" @update:value="loadRecords" />
        <n-button @click="openRecord">录入成绩</n-button>
        <n-button @click="openBatchImport">批量导入</n-button>
        <n-button @click="openStatistics">统计</n-button>
        <n-button @click="handleExport">导出</n-button>
      </n-space>
    </div>

    <n-spin :show="loading">
      <n-card>
        <n-data-table :columns="columns" :data="students" :bordered="false" :scroll-x="scrollX" :max-height="600" :row-key="(row: any) => row.student_id" />
      </n-card>
    </n-spin>

    <!-- 录入成绩弹窗 -->
    <n-modal v-model:show="showRecord" preset="card" title="录入成绩" style="width: 600px">
      <n-form label-placement="left" label-width="80">
        <n-form-item label="学生">
          <n-select v-model:value="recordForm.student_id" :options="studentOptions" placeholder="选择学生" filterable />
        </n-form-item>
        <n-divider>各项分数</n-divider>
        <n-form-item v-for="item in gradeItems" :key="item.id" :label="item.name">
          <n-space align="center">
            <n-input-number v-model:value="recordForm.scores[item.id]" :min="0" :max="item.max_score" style="width: 120px;" />
            <span style="color: #999;">/ {{ item.max_score }}</span>
          </n-space>
        </n-form-item>
        <n-form-item label="备注">
          <n-input v-model:value="recordForm.remark" placeholder="可选：缺考/缓考等" />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showRecord = false">取消</n-button>
          <n-button type="primary" :loading="recordLoading" @click="handleSaveRecord">保存</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 批量导入弹窗 -->
    <n-modal v-model:show="showBatchImport" preset="card" title="批量导入成绩" style="width: 700px">
      <n-space vertical :size="16">
        <n-alert type="info">
          格式：每行一条记录，格式为 "学号 项目名 分数"（空格分隔）。例如：<br>
          2024001 平时分 85<br>
          2024001 考试分 90
        </n-alert>
        <n-input v-model:value="batchText" type="textarea" placeholder="每行格式：学号 项目名 分数" :rows="10" style="font-family: monospace;" />
        <div v-if="batchResult">
          <n-alert :type="batchResult.errors?.length ? 'warning' : 'success'" style="margin-bottom: 8px;">
            成功导入 {{ batchResult.success }} 条
            <span v-if="batchResult.errors?.length">，{{ batchResult.errors.length }} 条失败</span>
          </n-alert>
        </div>
      </n-space>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showBatchImport = false">关闭</n-button>
          <n-button type="primary" :loading="batchLoading" :disabled="!batchText.trim()" @click="handleBatchImport">导入</n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 统计弹窗 -->
    <n-modal v-model:show="showStats" preset="card" title="成绩统计" style="width: 700px">
      <n-spin :show="statsLoading">
        <n-descriptions v-if="statsData.total_stats?.count" bordered :column="2" style="margin-bottom: 20px;">
          <n-descriptions-item label="总人数">{{ statsData.total_stats.count }}</n-descriptions-item>
          <n-descriptions-item label="平均分">{{ statsData.total_stats.avg }}</n-descriptions-item>
          <n-descriptions-item label="最高分">{{ statsData.total_stats.max }}</n-descriptions-item>
          <n-descriptions-item label="最低分">{{ statsData.total_stats.min }}</n-descriptions-item>
          <n-descriptions-item label="及格率">{{ statsData.total_stats.pass_rate }}%</n-descriptions-item>
        </n-descriptions>
        <n-data-table :columns="statsColumns" :data="statsData.statistics || []" :bordered="false" />
      </n-spin>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue'
import { useMessage } from 'naive-ui'
import { NButton, NTag } from 'naive-ui'
import { adminApi, authApi } from '@/api'

const message = useMessage()
const loading = ref(false)
const recordLoading = ref(false)
const batchLoading = ref(false)
const statsLoading = ref(false)

const schemes = ref<any[]>([])
const selectedScheme = ref<number | null>(null)
const selectedClass = ref<number | null>(null)
const classOptions = ref<{ label: string; value: number }[]>([])
const studentOptions = ref<{ label: string; value: number }[]>([])

const gradeItems = ref<any[]>([])
const students = ref<any[]>([])

const showRecord = ref(false)
const showBatchImport = ref(false)
const showStats = ref(false)

const recordForm = ref({ student_id: null as number | null, scores: {} as Record<number, number | null>, remark: '' })
const batchText = ref('')
const batchResult = ref<any>(null)
const statsData = ref<any>({})

const schemeOptions = computed(() => schemes.value.map(s => ({ label: s.name + (s.is_active ? ' (激活)' : ''), value: s.id })))

const scrollX = computed(() => 400 + gradeItems.value.length * 110 + 200)

const columns = computed(() => {
  const base = [
    { title: '学号', key: 'student_no', width: 100, fixed: 'left' as const, sorter: (a: any, b: any) => (a.student_no || '').localeCompare(b.student_no || '') },
    { title: '姓名', key: 'student_name', width: 90, fixed: 'left' as const },
  ]
  const itemCols = gradeItems.value.map((item: any) => ({
    title: `${item.name}(${item.weight}%)`,
    key: `item_${item.id}`,
    width: 110,
    sorter: (a: any, b: any) => {
      const sa = a.items?.find((i: any) => i.item_id === item.id)?.score ?? -1
      const sb = b.items?.find((i: any) => i.item_id === item.id)?.score ?? -1
      return sa - sb
    },
    render: (row: any) => {
      const si = row.items?.find((i: any) => i.item_id === item.id)
      if (!si || si.score === null) return h('span', { style: 'color: #ccc' }, '-')
      const pct = si.score / item.max_score
      const color = pct >= 0.9 ? '#18a058' : pct >= 0.6 ? '#f0a020' : '#d03050'
      const statusTag = si.status === 'absent' ? h(NTag, { type: 'error', size: 'tiny' }, { default: () => '缺考' }) : null
      return h('span', {}, [
        h('span', { style: `color: ${color}; font-weight: 500;` }, `${si.score}`),
        statusTag
      ])
    }
  }))
  const tail = [
    { title: '总成绩', key: 'total_score', width: 90, fixed: 'right' as const, sorter: (a: any, b: any) => (a.total_score || 0) - (b.total_score || 0), render: (row: any) => {
      const s = row.total_score
      if (s === null || s === undefined || s === 0) return h('span', { style: 'color: #ccc' }, '-')
      const color = s >= 90 ? '#18a058' : s >= 60 ? '#f0a020' : '#d03050'
      return h('span', { style: `color: ${color}; font-weight: bold; font-size: 15px;` }, `${s}`)
    }},
    { title: '操作', key: 'actions', width: 80, fixed: 'right' as const, render: (row: any) =>
      h(NButton, { type: 'info', size: 'small', onClick: () => openEditRecord(row) }, { default: () => '编辑' })
    },
  ]
  return [...base, ...itemCols, ...tail]
})

const statsColumns = [
  { title: '项目', key: 'item_name' },
  { title: '人数', key: 'count', width: 60 },
  { title: '平均分', key: 'avg', width: 80 },
  { title: '最高分', key: 'max', width: 80 },
  { title: '最低分', key: 'min', width: 80 },
  { title: '及格率', key: 'pass_rate', width: 80, render: (row: any) => `${row.pass_rate}%` },
]

function openRecord() {
  recordForm.value = { student_id: null, scores: {}, remark: '' }
  showRecord.value = true
}

function openEditRecord(row: any) {
  recordForm.value = { student_id: row.student_id, scores: {}, remark: '' }
  for (const item of row.items || []) {
    recordForm.value.scores[item.item_id] = item.score
  }
  showRecord.value = true
}

async function handleSaveRecord() {
  if (!recordForm.value.student_id) { message.warning('请选择学生'); return }
  recordLoading.value = true
  try {
    for (const item of gradeItems.value) {
      const score = recordForm.value.scores[item.id]
      if (score !== null && score !== undefined) {
        await adminApi.saveGradeRecord({
          student_id: recordForm.value.student_id,
          item_id: item.id,
          score: score,
          remark: recordForm.value.remark
        })
      }
    }
    message.success('成绩已保存')
    showRecord.value = false
    await loadRecords()
  } catch (e: any) { message.error(e.detail || '保存失败') }
  finally { recordLoading.value = false }
}

function openBatchImport() {
  batchText.value = ''
  batchResult.value = null
  showBatchImport.value = true
}

async function handleBatchImport() {
  const lines = batchText.value.trim().split('\n').filter(l => l.trim())
  const records: any[] = []
  for (const line of lines) {
    const parts = line.trim().split(/\s+/)
    if (parts.length >= 3) {
      const studentNo = parts[0]
      const itemName = parts[1]
      const score = parseFloat(parts[2])
      const student = students.value.find(s => s.student_id === studentNo || s.username === studentNo)
      const item = gradeItems.value.find(i => i.name === itemName)
      if (student && item && !isNaN(score)) {
        records.push({ student_id: student.id, item_id: item.id, score })
      }
    }
  }
  if (!records.length) { message.warning('没有有效数据'); return }
  batchLoading.value = true
  try {
    const result = await adminApi.batchImportGrades({ records }) as any
    batchResult.value = result
    message.success(`成功导入 ${result.success} 条`)
    await loadRecords()
  } catch (e: any) { message.error(e.detail || '导入失败') }
  finally { batchLoading.value = false }
}

async function openStatistics() {
  showStats.value = true
  statsLoading.value = true
  try {
    statsData.value = await adminApi.getGradeStatistics({ scheme_id: selectedScheme.value || undefined, class_id: selectedClass.value || undefined }) as any
  } catch {} finally { statsLoading.value = false }
}

function handleExport() {
  const data = { scheme_id: selectedScheme.value, class_id: selectedClass.value }
  const params = new URLSearchParams()
  if (data.scheme_id) params.set('scheme_id', String(data.scheme_id))
  if (data.class_id) params.set('class_id', String(data.class_id))
  window.open(`/api/admin/grades/export?${params.toString()}`, '_blank')
}

async function loadRecords() {
  if (!selectedScheme.value) return
  loading.value = true
  try {
    // 同时加载学生列表和成绩记录
    const [studentList, gradeData] = await Promise.all([
      adminApi.getStudents(selectedClass.value || undefined) as any,
      adminApi.getGradeRecords({ scheme_id: selectedScheme.value, class_id: selectedClass.value || undefined }) as any
    ])

    gradeItems.value = gradeData.items || []
    const gradeStudents = gradeData.students || []

    // 以学生列表为基准，合并成绩数据
    const gradeMap = new Map(gradeStudents.map((s: any) => [s.student_id, s]))
    students.value = (studentList || []).map((s: any) => {
      const grade = gradeMap.get(s.id)
      return {
        student_id: s.id,
        student_no: s.student_id || '',
        student_name: s.name || '',
        class_name: '',
        items: grade?.items || gradeItems.value.map((i: any) => ({ item_id: i.id, item_name: i.name, weight: i.weight, max_score: i.max_score, score: null, remark: null, status: 'normal' })),
        total_score: grade?.total_score ?? null
      }
    })
    studentOptions.value = students.value.map(s => ({ label: `${s.student_no} ${s.student_name}`, value: s.student_id }))
  } catch {} finally { loading.value = false }
}

async function loadSchemes() {
  try {
    schemes.value = await adminApi.getGradeSchemes() as any
    const active = schemes.value.find(s => s.is_active)
    if (active) { selectedScheme.value = active.id; await loadRecords() }
  } catch {}
}

async function loadClasses() {
  try {
    const data = await authApi.getClasses() as any
    classOptions.value = data.map((c: any) => ({ label: c.name, value: c.id }))
  } catch {}
}

onMounted(() => {
  loadSchemes()
  loadClasses()
})
</script>

<style scoped>
.grade-manage-container { max-width: 1400px; margin: 0 auto; }
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.page-header h2 { margin: 0; font-size: 20px; }
</style>
