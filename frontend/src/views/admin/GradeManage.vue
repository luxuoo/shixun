<template>
  <div class="grade-manage-container">
    <h2 style="margin: 0 0 24px; font-size: 20px;">成绩管理</h2>

    <n-tabs type="line" animated>
      <!-- ==================== Tab 1: 使用指南 ==================== -->
      <n-tab-pane name="guide" tab="📖 使用指南">
        <!-- 快速理解 -->
        <n-card title="一、成绩系统快速理解" style="margin-bottom: 20px;">
          <div class="guide-section">
            <p>本系统的成绩由<strong>两部分</strong>组成，可以只用其中一部分，也可以两部分配合使用：</p>

            <div class="concept-cards">
              <div class="concept-card blue">
                <div class="concept-num">A</div>
                <div class="concept-title">任务成绩</div>
                <div class="concept-desc">
                  学生每完成一个编程任务，系统自动计算该任务的分数。<br>
                  <strong>公式：</strong>AI评分 × {{ weights.ai }}% + 教师评分 × {{ weights.teacher }}% + 出勤 × {{ weights.attendance }}%<br>
                  <strong>特点：</strong>全自动，学生提交代码后 AI 立即评分，教师可后续调整
                </div>
              </div>
              <div class="concept-card green">
                <div class="concept-num">B</div>
                <div class="concept-title">过程性评价</div>
                <div class="concept-desc">
                  把成绩拆分成多个维度（如出勤、课堂表现、代码质量、创新能力），每个维度单独打分。<br>
                  <strong>公式：</strong>阶段1得分×权重 + 阶段2得分×权重 + ...<br>
                  <strong>特点：</strong>更灵活，支持自动采集、教师手动打分、学生自评、同学互评
                </div>
              </div>
            </div>
          </div>
        </n-card>

        <!-- 任务成绩操作指南 -->
        <n-card title="二、任务成绩 — 操作步骤" style="margin-bottom: 20px;">
          <div class="guide-section">
            <n-steps :current="0" vertical size="small">
              <n-step title="创建教学任务">
                <div class="step-content">
                  进入 <n-button text type="primary" @click="$router.push({name:'AdminTasks'})">任务管理</n-button>，
                  点击「新建任务」或使用「AI 分解」自动生成步骤。<br>
                  例：创建「YOLO 智慧交通系统」，包含 9 个步骤
                </div>
              </n-step>
              <n-step title="学生提交代码">
                <div class="step-content">
                  学生在「教学任务」页面逐个步骤提交代码。<br>
                  每次提交后，<strong>AI 自动评分</strong>（代码正确性、风格、完整性、创新性 4 个维度）。
                </div>
              </n-step>
              <n-step title="教师审核评分（可选）">
                <div class="step-content">
                  进入 <n-button text type="primary" @click="$router.push({name:'AdminSubmissions'})">提交记录</n-button>，
                  查看学生的代码和 AI 评分，给出教师评分。<br>
                  <strong>不评也没关系</strong> — 如果教师不评分，任务分数 = AI 评分 × 100%。
                </div>
              </n-step>
              <n-step title="查看成绩">
                <div class="step-content">
                  学生在「成绩总览」页面看到自己的任务成绩。<br>
                  教师在下方「学生成绩概览」表格中查看全班成绩。
                </div>
              </n-step>
            </n-steps>
          </div>
        </n-card>

        <!-- 过程性评价操作指南 -->
        <n-card title="三、过程性评价 — 操作步骤" style="margin-bottom: 20px;">
          <div class="guide-section">
            <n-steps :current="0" vertical size="small">
              <n-step title="创建评价模板">
                <div class="step-content">
                  进入 <n-button text type="primary" @click="$router.push({name:'AdminProcessEvalConfig'})">评价配置</n-button>，
                  点击「新建模板」或「AI 生成模板」或「初始化默认模板」。<br>
                  <strong>推荐：</strong>先点「初始化默认模板」，会自动创建 课前10% + 课中35% + 课后10% 的标准方案。
                </div>
              </n-step>
              <n-step title="配置阶段和指标">
                <div class="step-content">
                  每个模板包含多个<strong>阶段</strong>（如课前、课中、课后），每个阶段包含多个<strong>指标</strong>。<br><br>
                  <strong>指标的关键设置：</strong><br>
                  • <strong>权重</strong>：该指标在阶段内的占比（同一阶段内所有指标权重合计 = 100%）<br>
                  • <strong>数据来源</strong>：决定分数从哪里来（见下表）<br>
                  • <strong>自动采集</strong>：开启后系统自动从数据来源拉取分数<br>
                  • <strong>评分主体</strong>：谁来打分（教师/AI/学生自评/同学互评）
                </div>
              </n-step>
              <n-step title="录入分数">
                <div class="step-content">
                  分数进入系统有 <strong>4 种方式</strong>（根据指标的「数据来源」设置选择）：<br><br>
                  <n-table :bordered="true" :single-line="false" size="small">
                    <thead>
                      <tr><th>数据来源</th><th>怎么录入</th><th>适合场景</th></tr>
                    </thead>
                    <tbody>
                      <tr><td><n-tag size="small" type="info">自动采集</n-tag> 任务综合分</td><td>点击「自动采集」按钮，从任务成绩自动拉取</td><td>编程作业成绩直接算入评价</td></tr>
                      <tr><td><n-tag size="small" type="info">自动采集</n-tag> 代码提交</td><td>点击「自动采集」按钮，从提交记录拉取</td><td>只看提交分数</td></tr>
                      <tr><td><n-tag size="small" type="info">自动采集</n-tag> 出勤</td><td>点击「自动采集」按钮，从学生登录记录自动统计</td><td>出勤自动计分（学生登录系统即算出勤）</td></tr>
                      <tr><td><n-tag size="small" type="info">自动采集</n-tag> AI评分</td><td>点击「自动采集」按钮，从 AI 评分拉取</td><td>只看 AI 评分</td></tr>
                      <tr><td><n-tag size="small" type="warning">手动录入</n-tag></td><td>进入 <n-button text type="primary" @click="$router.push({name:'AdminScoreEntry'})">评分明录</n-button>，逐个学生打分</td><td>课堂表现、答辩等</td></tr>
                      <tr><td><n-tag size="small" type="success">学生自评</n-tag></td><td>学生在「自评互评」页面给自己打分</td><td>自我反思</td></tr>
                      <tr><td><n-tag size="small" type="success">同学互评</n-tag></td><td>学生在「自评互评」页面给同学打分</td><td>小组协作评价</td></tr>
                    </tbody>
                  </n-table>
                </div>
              </n-step>
              <n-step title="激活模板并查看看板">
                <div class="step-content">
                  在评价配置页点击「激活模板」，然后进入 <n-button text type="primary" @click="$router.push({name:'AdminProcessEval'})">过程性评价</n-button> 看板查看班级成绩分布、排名、薄弱维度分析。
                </div>
              </n-step>
            </n-steps>
          </div>
        </n-card>

        <!-- 常见问题 -->
        <n-card title="四、常见问题" style="margin-bottom: 20px;">
          <n-collapse>
            <n-collapse-item title="Q: 任务成绩和过程性评价是什么关系？" name="q1">
              <div class="faq-content">
                <p><strong>任务成绩</strong>是系统自动算的，学生提交代码就有分。</p>
                <p><strong>过程性评价</strong>是一个更全面的评价框架，你可以把任务成绩作为其中一个数据来源「自动采集」进来，也可以单独设置其他评价维度。</p>
                <p>两套成绩独立存在，学生在「成绩总览」看过程性评价，在「提交记录」看任务成绩。</p>
              </div>
            </n-collapse-item>
            <n-collapse-item title="Q: 我只想用任务成绩，不想搞过程性评价？" name="q2">
              <div class="faq-content">
                <p>完全可以。不用管过程性评价相关的页面。学生提交代码 → AI 自动评分 → 教师在「提交记录」审核 → 学生在「提交记录」看分。</p>
              </div>
            </n-collapse-item>
            <n-collapse-item title="Q: 我想让出勤、课堂表现也算进成绩？" name="q3">
              <div class="faq-content">
                <p>需要用过程性评价。步骤：</p>
                <ol>
                  <li>创建评价模板，添加「出勤」指标（数据来源选「出勤」，开启自动采集）</li>
                  <li>添加「课堂表现」指标（数据来源选手动录入）</li>
                  <li>学生登录系统学习自动记录考勤，点「自动采集」拉取出勤分</li>
                  <li>在「评分明录」页给课堂表现打分</li>
                </ol>
              </div>
            </n-collapse-item>
            <n-collapse-item title="Q: 自动采集为什么没有数据？" name="q4">
              <div class="faq-content">
                <p>检查以下几点：</p>
                <ol>
                  <li>指标的「自动采集」开关是否打开</li>
                  <li>指标的「数据来源」是否选了非「手动录入」的选项</li>
                  <li>学生是否真的有对应数据（提交过代码？参加过点名？）</li>
                  <li>24小时内同一指标不会重复采集</li>
                </ol>
              </div>
            </n-collapse-item>
            <n-collapse-item title="Q: 权重合计不是 100% 会怎样？" name="q5">
              <div class="faq-content">
                <p>任务成绩权重：必须合计 100% 才能保存。</p>
                <p>过程性评价权重：阶段权重合计应为 100%，指标权重在各自阶段内合计应为 100%。系统会在配置页顶部显示校验结果。</p>
              </div>
            </n-collapse-item>
          </n-collapse>
        </n-card>
      </n-tab-pane>

      <!-- ==================== Tab 2: 权重配置 ==================== -->
      <n-tab-pane name="weights" tab="⚙️ 权重配置">
        <n-card title="任务成绩权重" style="margin-bottom: 20px;">
          <template #header-extra>
            <n-tag :type="weightsSaved ? 'success' : 'warning'" size="small">
              {{ weightsSaved ? '已保存' : '未保存' }}
            </n-tag>
          </template>

          <div class="formula-box">
            <div class="formula-title">当前计算公式</div>
            <div class="formula-text">
              任务最终分 = AI评分 × <strong>{{ weights.ai }}%</strong>
              + 教师评分 × <strong>{{ weights.teacher }}%</strong>
              <template v-if="weights.attendance > 0">
                + 出勤分 × <strong>{{ weights.attendance }}%</strong>
              </template>
            </div>
            <div class="formula-example">
              例：学生 AI 评分 85 分，教师评分 90 分，出勤分 80 分<br>
              → 最终分 = 85×{{ weights.ai/100 }} + 90×{{ weights.teacher/100 }}
              <template v-if="weights.attendance > 0"> + 80×{{ weights.attendance/100 }}</template>
              = <strong>{{ (85*weights.ai/100 + 90*weights.teacher/100 + 80*weights.attendance/100).toFixed(1) }}</strong> 分
            </div>
          </div>

          <n-form label-placement="left" label-width="100" style="margin-top: 20px;">
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

        <n-alert type="warning">
          <strong>注意：</strong>修改权重后，已有的任务分数不会自动重算。
          学生下次提交新代码时会按新权重计算。教师在「提交记录」重新评分也会触发重算。
        </n-alert>
      </n-tab-pane>

      <!-- ==================== Tab 3: 学生成绩 ==================== -->
      <n-tab-pane name="students" tab="📊 学生成绩">
        <n-card>
          <template #header>
            <n-space align="center" justify="space-between" style="width: 100%;">
              <span>学生成绩概览</span>
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
            </n-space>
          </template>

          <n-alert type="info" size="small" style="margin-bottom: 16px;">
            以下数据来自「班级管理」的统计接口，展示的是任务维度的成绩。过程性评价的详细分数请到「过程性评价」看板查看。
          </n-alert>

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
      </n-tab-pane>
    </n-tabs>
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
  { title: '提交次数', key: 'total_submissions', width: 90 },
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

.guide-section {
  font-size: 14px;
  line-height: 1.8;
}

.guide-section p {
  margin: 8px 0;
}

.step-content {
  font-size: 13px;
  color: #555;
  padding: 4px 0;
}

.concept-cards {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin: 16px 0;
}

.concept-card {
  padding: 20px;
  border-radius: 12px;
  border: 1px solid;
}

.concept-card.blue {
  background: #f0f6ff;
  border-color: #b8d4ff;
}

.concept-card.green {
  background: #f0faf0;
  border-color: #b8e6b8;
}

.concept-num {
  display: inline-block;
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: #333;
  color: #fff;
  text-align: center;
  line-height: 28px;
  font-weight: 700;
  font-size: 14px;
  margin-bottom: 8px;
}

.concept-title {
  font-size: 17px;
  font-weight: 700;
  margin-bottom: 8px;
}

.concept-desc {
  font-size: 13px;
  color: #555;
  line-height: 1.8;
}

.faq-content {
  font-size: 13px;
  line-height: 1.8;
  padding: 8px 0;
}

.faq-content ol {
  padding-left: 20px;
}

.formula-box {
  padding: 20px;
  background: #f8f9fa;
  border-radius: 8px;
  border: 1px solid #e8e8ec;
}

.formula-title {
  font-weight: 600;
  margin-bottom: 8px;
  color: #666;
  font-size: 13px;
}

.formula-text {
  font-size: 16px;
  font-family: monospace;
  margin-bottom: 12px;
}

.formula-example {
  font-size: 13px;
  color: #888;
  padding: 12px;
  background: #fff;
  border-radius: 6px;
  border: 1px dashed #ddd;
}

@media (max-width: 768px) {
  .concept-cards {
    grid-template-columns: 1fr;
  }
}
</style>
