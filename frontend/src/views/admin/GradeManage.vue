<template>
  <div class="grade-manage-container">
    <h2 style="margin: 0 0 24px; font-size: 20px;">成绩管理</h2>

    <!-- 成绩体系总览 -->
    <n-card title="成绩体系总览" style="margin-bottom: 20px;">
      <n-alert type="info" style="margin-bottom: 16px;">
        系统有两套成绩，互相关联但独立运作：
        <strong>任务成绩</strong>（代码提交 → AI评分 → 教师评分）和
        <strong>过程性评价</strong>（多维度指标 → 自动采集/手动录入/自评互评）。
      </n-alert>

      <!-- 数据流向图 -->
      <div class="flow-diagram">
        <div class="flow-section">
          <div class="flow-title">📥 数据来源</div>
          <div class="flow-items">
            <div class="flow-item blue">学生提交代码</div>
            <div class="flow-item green">课堂点名出勤</div>
            <div class="flow-item orange">学生自评/互评</div>
            <div class="flow-item purple">教师手动录入</div>
          </div>
        </div>
        <div class="flow-arrow">→</div>
        <div class="flow-section">
          <div class="flow-title">⚙️ 计算引擎</div>
          <div class="flow-items">
            <div class="flow-item blue">AI 自动评分 (4维度)</div>
            <div class="flow-item green">任务综合分 = AI×{{ weights.ai }}% + 教师×{{ weights.teacher }}%</div>
            <div class="flow-item orange">过程性评价 = Σ(阶段分×阶段权重)</div>
          </div>
        </div>
        <div class="flow-arrow">→</div>
        <div class="flow-section">
          <div class="flow-title">📊 最终成绩</div>
          <div class="flow-items">
            <div class="flow-item red">学生看到的「成绩总览」和「过程性评价」</div>
          </div>
        </div>
      </div>
    </n-card>

    <!-- 任务成绩权重配置 -->
    <n-card title="任务成绩权重" style="margin-bottom: 20px;">
      <template #header-extra>
        <n-tag :type="weightsSaved ? 'success' : 'warning'" size="small">
          {{ weightsSaved ? '已保存' : '未保存' }}
        </n-tag>
      </template>

      <div style="margin-bottom: 16px; padding: 16px; background: #f8f9fa; border-radius: 8px;">
        <div style="font-weight: 600; margin-bottom: 8px;">计算公式：</div>
        <div style="font-family: monospace; font-size: 15px; color: #333;">
          任务最终分 = AI评分 × <strong>{{ weights.ai }}%</strong>
          + 教师评分 × <strong>{{ weights.teacher }}%</strong>
          <template v-if="weights.attendance > 0">
            + 出勤分 × <strong>{{ weights.attendance }}%</strong>
          </template>
        </div>
        <div style="font-size: 13px; color: #999; margin-top: 8px;">
          ※ 当教师未评分时，教师权重自动归入 AI 权重<br>
          ※ 出勤分来自课堂点名，每次 +{{ settings.rollcall_score }}分（可在系统设置中调整）
        </div>
      </div>

      <n-form label-placement="left" label-width="100">
        <n-form-item label="AI 评分权重">
          <n-slider v-model:value="weights.ai" :min="0" :max="100" :step="5" style="width: 300px;" />
          <span style="margin-left: 12px; font-weight: 600;">{{ weights.ai }}%</span>
        </n-form-item>
        <n-form-item label="教师评分权重">
          <n-slider v-model:value="weights.teacher" :min="0" :max="100" :step="5" style="width: 300px;" />
          <span style="margin-left: 12px; font-weight: 600;">{{ weights.teacher }}%</span>
        </n-form-item>
        <n-form-item label="出勤权重">
          <n-slider v-model:value="weights.attendance" :min="0" :max="100" :step="5" style="width: 300px;" />
          <span style="margin-left: 12px; font-weight: 600;">{{ weights.attendance }}%</span>
        </n-form-item>
        <n-form-item>
          <n-space>
            <n-tag :type="totalWeight === 100 ? 'success' : totalWeight > 100 ? 'error' : 'warning'">
              权重合计: {{ totalWeight }}%
            </n-tag>
            <n-button type="primary" @click="saveWeights" :disabled="totalWeight !== 100">
              保存权重
            </n-button>
            <n-button @click="resetWeights">恢复默认</n-button>
          </n-space>
        </n-form-item>
      </n-form>
    </n-card>

    <!-- 过程性评价说明 -->
    <n-card title="过程性评价" style="margin-bottom: 20px;">
      <n-grid :cols="2" :x-gap="16">
        <n-gi>
          <div style="padding: 16px; background: #f8f9fa; border-radius: 8px; height: 100%;">
            <div style="font-weight: 600; margin-bottom: 12px;">评价体系结构</div>
            <div style="font-size: 14px; line-height: 2;">
              <div>📋 <strong>评价模板</strong> → 包含多个阶段</div>
              <div style="padding-left: 24px;">📅 <strong>阶段</strong>（如课前/课中/课后）→ 包含多个指标</div>
              <div style="padding-left: 48px;">📐 <strong>指标</strong>（如出勤、代码质量）→ 设置权重和数据来源</div>
              <div style="padding-left: 72px;">👤 <strong>评分主体</strong>（教师/AI/自评/互评）→ 设置权重</div>
            </div>
          </div>
        </n-gi>
        <n-gi>
          <div style="padding: 16px; background: #f8f9fa; border-radius: 8px; height: 100%;">
            <div style="font-weight: 600; margin-bottom: 12px;">数据录入方式</div>
            <div style="font-size: 14px; line-height: 2;">
              <div>🔄 <strong>自动采集</strong> — 从提交/出勤/AI评分自动拉取</div>
              <div>✏️ <strong>手动录入</strong> — 教师在「评分明录」页打分</div>
              <div>🙋 <strong>学生自评</strong> — 学生在「自评互评」页给自己打分</div>
              <div>👥 <strong>同学互评</strong> — 学生在「自评互评」页给同学打分</div>
            </div>
          </div>
        </n-gi>
      </n-grid>

      <div style="margin-top: 16px;">
        <n-space>
          <n-button type="primary" @click="$router.push({ name: 'AdminProcessEval' })">
            查看班级看板
          </n-button>
          <n-button type="info" @click="$router.push({ name: 'AdminProcessEvalConfig' })">
            配置评价方案
          </n-button>
          <n-button type="warning" @click="$router.push({ name: 'AdminScoreEntry' })">
            评分明录
          </n-button>
        </n-space>
      </div>
    </n-card>

    <!-- 学生成绩概览 -->
    <n-card title="学生成绩概览">
      <template #header-extra>
        <n-space>
          <n-select
            v-model:value="selectedClassId"
            :options="classOptions"
            placeholder="选择班级"
            clearable
            style="width: 200px;"
            @update:value="loadStudentScores"
          />
          <n-button @click="loadStudentScores" :loading="loadingScores">刷新</n-button>
        </n-space>
      </template>

      <n-spin :show="loadingScores">
        <n-data-table
          :columns="scoreColumns"
          :data="studentScores"
          :bordered="false"
          :pagination="{ pageSize: 20 }"
          :scroll-x="800"
        />
        <n-empty v-if="!studentScores.length && !loadingScores" description="选择班级查看学生成绩" style="padding: 40px 0;" />
      </n-spin>
    </n-card>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, h } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage, NTag, NProgress } from 'naive-ui'
import { authApi, adminApi } from '@/api'

const router = useRouter()
const message = useMessage()

const weights = ref({ ai: 40, teacher: 30, attendance: 20 })
const defaultWeights = { ai: 40, teacher: 30, attendance: 20 }
const weightsSaved = ref(true)
const settings = ref({ rollcall_score: 5, rollcall_auto_score: false })

const selectedClassId = ref<number | null>(null)
const classOptions = ref<{ label: string; value: number }[]>([])
const studentScores = ref<any[]>([])
const loadingScores = ref(false)

const totalWeight = computed(() => weights.value.ai + weights.value.teacher + weights.value.attendance)

// 学生成绩表格列
const scoreColumns = [
  { title: '学号', key: 'username', width: 100 },
  { title: '姓名', key: 'name', width: 100 },
  {
    title: '任务平均分',
    key: 'avg_score',
    width: 110,
    render: (row: any) => {
      if (row.avg_score == null) return h('span', { style: 'color: #ccc;' }, '--')
      const color = row.avg_score >= 90 ? '#18a058' : row.avg_score >= 60 ? '#f0a020' : '#d03050'
      return h('span', { style: `color: ${color}; font-weight: 600;` }, row.avg_score.toFixed(1))
    }
  },
  {
    title: 'AI平均分',
    key: 'avg_ai',
    width: 100,
    render: (row: any) => row.avg_ai != null ? h('span', {}, row.avg_ai.toFixed(1)) : '--'
  },
  {
    title: '教师平均分',
    key: 'avg_teacher',
    width: 100,
    render: (row: any) => row.avg_teacher != null ? h('span', {}, row.avg_teacher.toFixed(1)) : '--'
  },
  {
    title: '提交次数',
    key: 'total_submissions',
    width: 90,
  },
  {
    title: '完成率',
    key: 'completion_rate',
    width: 130,
    render: (row: any) => {
      const pct = Math.round(row.completion_rate || 0)
      return h(NProgress, {
        type: 'line',
        percentage: pct,
        status: pct >= 80 ? 'success' : pct >= 50 ? 'info' : 'error',
        showIndicator: true,
        indicatorPlacement: 'inside'
      })
    }
  }
]

async function loadSettings() {
  try {
    const data = await authApi.getSettings() as any
    weights.value = data.grade_weights || { ai: 40, teacher: 30, attendance: 20 }
    settings.value = data
    weightsSaved.value = true
  } catch {}
}

async function loadClasses() {
  try {
    const data = await adminApi.getClasses() as any
    classOptions.value = (Array.isArray(data) ? data : []).map((c: any) => ({
      label: c.name, value: c.id
    }))
  } catch {}
}

async function loadStudentScores() {
  if (!selectedClassId.value) {
    studentScores.value = []
    return
  }
  loadingScores.value = true
  try {
    const data = await adminApi.getClassStats(selectedClassId.value) as any
    studentScores.value = data.rankings || []
  } catch (e: any) {
    message.error(e?.detail || '加载学生成绩失败')
  } finally {
    loadingScores.value = false
  }
}

async function saveWeights() {
  if (totalWeight.value !== 100) {
    message.warning('权重合计必须为 100%')
    return
  }
  try {
    await authApi.updateSettings({ grade_weights: weights.value })
    message.success('权重已保存')
    weightsSaved.value = true
  } catch (e: any) {
    message.error(e?.detail || '保存失败')
  }
}

function resetWeights() {
  weights.value = { ...defaultWeights }
  weightsSaved.value = false
}

onMounted(() => {
  loadSettings()
  loadClasses()
})
</script>

<style scoped>
.grade-manage-container {
  max-width: 1200px;
  margin: 0 auto;
}

.flow-diagram {
  display: flex;
  align-items: center;
  gap: 16px;
  overflow-x: auto;
  padding: 8px 0;
}

.flow-section {
  flex: 1;
  min-width: 200px;
}

.flow-title {
  font-weight: 600;
  font-size: 14px;
  margin-bottom: 8px;
}

.flow-items {
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.flow-item {
  padding: 8px 12px;
  border-radius: 6px;
  font-size: 13px;
  border-left: 3px solid;
}

.flow-item.blue { background: #f0f6ff; border-color: #2080f0; }
.flow-item.green { background: #f0faf0; border-color: #18a058; }
.flow-item.orange { background: #fff8f0; border-color: #f0a020; }
.flow-item.purple { background: #f5f0ff; border-color: #8b5cf6; }
.flow-item.red { background: #fff0f0; border-color: #d03050; }

.flow-arrow {
  font-size: 24px;
  color: #999;
  flex-shrink: 0;
}

@media (max-width: 768px) {
  .flow-diagram {
    flex-direction: column;
    align-items: stretch;
  }
  .flow-arrow {
    text-align: center;
    transform: rotate(90deg);
  }
}
</style>
