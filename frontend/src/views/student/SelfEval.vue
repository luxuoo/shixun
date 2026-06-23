<template>
  <div class="self-eval-container">
    <n-space align="center" :size="4" style="margin-bottom: 24px;">
      <h2 style="margin: 0; font-size: 20px;">自评互评</h2>
      <help-icon>自我评价：给自己打分，培养自我反思能力。同学互评：给同班同学打分，促进相互学习。只有教师在评价配置中开启了对应的评分主体，这里才会显示对应的指标。</help-icon>
    </n-space>

    <n-spin :show="loading">
      <template v-if="!loading && !template">
        <n-empty description="暂无可用的评价模板，请联系教师配置" style="padding: 60px 0;" />
      </template>

      <template v-else-if="template">
        <n-alert type="info" style="margin-bottom: 20px;">
          当前评价模板：<strong>{{ template.name }}</strong>
        </n-alert>

        <!-- 自评区域 -->
        <n-card title="自我评价" style="margin-bottom: 20px;">
          <template #header-extra>
            <n-tag type="success" size="small">给自己打分</n-tag>
          </template>
          <template v-if="selfIndicators.length > 0">
            <div v-for="item in selfIndicators" :key="item.indicator.id" class="eval-item">
              <div class="eval-item-header">
                <div>
                  <span class="eval-item-name">{{ item.indicator.name }}</span>
                  <n-tag size="small" type="info" style="margin-left: 8px;">{{ item.phase_name }}</n-tag>
                  <n-tag size="small" style="margin-left: 4px;">权重: {{ item.indicator.weight }}%</n-tag>
                </div>
                <span v-if="item.latest_score != null" class="eval-latest">
                  上次评分: <strong>{{ item.latest_score }}</strong>
                </span>
              </div>
              <div class="eval-item-body">
                <n-input-number
                  v-model:value="selfScores[item.indicator.id]"
                  :min="0"
                  :max="item.indicator.max_score || 100"
                  size="small"
                  style="width: 120px;"
                  placeholder="输入分数"
                />
                <input
                  v-model="selfRemarks[item.indicator.id]"
                  class="remark-input"
                  placeholder="备注（可选）"
                />
                <n-button
                  type="primary"
                  size="small"
                  :loading="selfSaving[item.indicator.id]"
                  :disabled="selfScores[item.indicator.id] == null"
                  @click="submitSelfEval(item.indicator.id, item.template_id)"
                >
                  提交
                </n-button>
              </div>
            </div>
          </template>
          <n-empty v-else description="暂无需要自评的指标" size="small" style="padding: 40px 0;" />
        </n-card>

        <!-- 互评区域 -->
        <n-card title="同学互评" style="margin-bottom: 20px;">
          <template #header-extra>
            <n-tag type="warning" size="small">给同学打分</n-tag>
          </template>
          <template v-if="peerIndicators.length > 0">
            <div v-for="item in peerIndicators" :key="item.indicator.id" class="eval-item">
              <div class="eval-item-header">
                <div>
                  <span class="eval-item-name">{{ item.indicator.name }}</span>
                  <n-tag size="small" type="info" style="margin-left: 8px;">{{ item.phase_name }}</n-tag>
                  <n-tag size="small" style="margin-left: 4px;">权重: {{ item.indicator.weight }}%</n-tag>
                </div>
              </div>
              <div class="eval-item-body">
                <n-select
                  v-model:value="peerTargets[item.indicator.id]"
                  :options="classmateOptions"
                  placeholder="选择同学"
                  size="small"
                  style="width: 160px;"
                  clearable
                />
                <n-input-number
                  v-model:value="peerScores[item.indicator.id]"
                  :min="0"
                  :max="item.indicator.max_score || 100"
                  size="small"
                  style="width: 120px;"
                  placeholder="输入分数"
                />
                <input
                  v-model="peerRemarks[item.indicator.id]"
                  class="remark-input"
                  placeholder="备注（可选）"
                />
                <n-button
                  type="primary"
                  size="small"
                  :loading="peerSaving[item.indicator.id]"
                  :disabled="!peerTargets[item.indicator.id] || peerScores[item.indicator.id] == null"
                  @click="submitPeerEval(item.indicator.id, item.template_id)"
                >
                  提交
                </n-button>
              </div>
            </div>
          </template>
          <n-empty v-else description="暂无需要互评的指标" size="small" style="padding: 40px 0;" />
        </n-card>
      </template>
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, computed } from 'vue'
import { useMessage } from 'naive-ui'
import { evalApi, adminApi } from '@/api'
import { useUserStore } from '@/stores/user'

const message = useMessage()
const userStore = useUserStore()

const loading = ref(false)
const template = ref<any>(null)
const classmates = ref<any[]>([])

interface IndicatorItem {
  indicator: any
  phase_name: string
  template_id: number
  latest_score: number | null
}

const selfIndicators = ref<IndicatorItem[]>([])
const peerIndicators = ref<IndicatorItem[]>([])

// 自评状态
const selfScores = reactive<Record<number, number | null>>({})
const selfRemarks = reactive<Record<number, string>>({})
const selfSaving = reactive<Record<number, boolean>>({})

// 互评状态
const peerScores = reactive<Record<number, number | null>>({})
const peerTargets = reactive<Record<number, number | null>>({})
const peerRemarks = reactive<Record<number, string>>({})
const peerSaving = reactive<Record<number, boolean>>({})

const classmateOptions = computed(() =>
  classmates.value
    .filter(s => s.id !== userStore.user?.id)
    .map(s => ({ label: `${s.name || s.username}`, value: s.id }))
)

async function loadData() {
  const studentId = userStore.user?.id
  if (!studentId) return
  loading.value = true
  try {
    // 获取活跃模板（通过看板接口获取 template_id）
    let tplId: number | null = null
    try {
      const tplRes = await evalApi.getStudentDashboard(studentId) as any
      tplId = tplRes.template_id
    } catch (e: any) {
      // 如果看板接口失败（如成绩未开放），尝试直接获取模板列表
      try {
        const templates = await evalApi.getTemplates() as any
        const activeTpl = (Array.isArray(templates) ? templates : []).find((t: any) => t.is_active)
        if (activeTpl) tplId = activeTpl.id
      } catch {}
    }
    if (!tplId) {
      loading.value = false
      return
    }
    const tpl = await evalApi.getTemplate(tplId) as any
    template.value = tpl

    // 获取同班同学
    const classId = userStore.user?.class_id
    if (classId) {
      const studentsRes = await adminApi.getStudents(classId) as any
      classmates.value = Array.isArray(studentsRes) ? studentsRes : []
    }

    // 分类指标
    const selfItems: IndicatorItem[] = []
    const peerItems: IndicatorItem[] = []

    for (const phase of (tpl.phases || [])) {
      for (const ind of (phase.indicators || [])) {
        const roles = (ind.scorer_configs || []).map((sc: any) => sc.scorer_role)
        const item: IndicatorItem = {
          indicator: ind,
          phase_name: phase.name,
          template_id: tpl.id,
          latest_score: null
        }

        if (roles.includes('self')) {
          selfItems.push(item)
          selfScores[ind.id] = null
          selfRemarks[ind.id] = ''
          selfSaving[ind.id] = false
        }
        if (roles.includes('peer')) {
          peerItems.push(item)
          peerScores[ind.id] = null
          peerTargets[ind.id] = null
          peerRemarks[ind.id] = ''
          peerSaving[ind.id] = false
        }
      }
    }

    selfIndicators.value = selfItems
    peerIndicators.value = peerItems

    // 获取已有评分记录
    const recordsRes = await evalApi.getRecords({ template_id: tpl.id, student_id: studentId }) as any
    const records = Array.isArray(recordsRes) ? recordsRes : []
    for (const item of selfItems) {
      const rec = records.find((r: any) => r.indicator_id === item.indicator.id && r.scorer_role === 'self')
      if (rec) {
        item.latest_score = rec.score
        selfScores[item.indicator.id] = rec.score
      }
    }
  } catch (e: any) {
    console.error('加载评价数据失败:', e)
  } finally {
    loading.value = false
  }
}

async function submitSelfEval(indicatorId: number, templateId: number) {
  const score = selfScores[indicatorId]
  if (score == null) return
  selfSaving[indicatorId] = true
  try {
    await evalApi.studentSelfEval({
      indicator_id: indicatorId,
      template_id: templateId,
      score: score,
      remark: selfRemarks[indicatorId] || ''
    })
    message.success('自评提交成功')
    // 更新 latest_score
    const item = selfIndicators.value.find(i => i.indicator.id === indicatorId)
    if (item) item.latest_score = score
  } catch (e: any) {
    message.error(e?.detail || '提交失败')
  } finally {
    selfSaving[indicatorId] = false
  }
}

async function submitPeerEval(indicatorId: number, templateId: number) {
  const score = peerScores[indicatorId]
  const targetId = peerTargets[indicatorId]
  if (score == null || !targetId) return
  peerSaving[indicatorId] = true
  try {
    await evalApi.studentPeerEval({
      indicator_id: indicatorId,
      template_id: templateId,
      student_id: targetId,
      score: score,
      remark: peerRemarks[indicatorId] || ''
    })
    message.success('互评提交成功')
    peerScores[indicatorId] = null
    peerTargets[indicatorId] = null
    peerRemarks[indicatorId] = ''
  } catch (e: any) {
    message.error(e?.detail || '提交失败')
  } finally {
    peerSaving[indicatorId] = false
  }
}

onMounted(() => {
  loadData()
})
</script>

<style scoped>
.self-eval-container {
  max-width: 900px;
  margin: 0 auto;
}

.eval-item {
  padding: 16px;
  border: 1px solid #e8e8ec;
  border-radius: 8px;
  margin-bottom: 12px;
  transition: border-color 0.2s;
}

.eval-item:hover {
  border-color: #6366f1;
}

.eval-item-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.eval-item-name {
  font-weight: 600;
  font-size: 15px;
}

.eval-latest {
  font-size: 13px;
  color: #666;
}

.eval-item-body {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
}

.remark-input {
  flex: 1;
  min-width: 120px;
  padding: 4px 8px;
  border: 1px solid #e0e0e0;
  border-radius: 4px;
  font-size: 13px;
}

.remark-input:focus {
  outline: none;
  border-color: #6366f1;
}
</style>
