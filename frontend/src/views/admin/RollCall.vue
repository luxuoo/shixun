<template>
  <div class="roll-call-container">
    <!-- 顶部控制栏 -->
    <div class="top-bar">
      <h2>课堂点名</h2>
      <n-space>
        <n-tag v-if="settings.rollcall_auto_score" type="success" size="small">
          自动出勤分 +{{ settings.rollcall_score }}
        </n-tag>
        <n-select
          v-model:value="selectedClass"
          :options="classOptions"
          placeholder="选择班级"
          clearable
          style="width: 200px;"
          @update:value="loadStudents"
        />
      </n-space>
    </div>

    <!-- 主体 -->
    <div class="main-area">
      <!-- 左侧：点名核心区域 -->
      <div class="call-zone">
        <!-- 点名展示区 -->
        <div class="call-display" :class="{ rolling: isRolling, called: calledStudent }">
          <!-- 未开始状态 -->
          <div v-if="!calledStudent && !isRolling" class="init-state">
            <div class="init-icon">
              <n-icon size="64" color="#c0c4cc">
                <svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/></svg>
              </n-icon>
            </div>
            <p class="init-text">选择班级后点击按钮开始点名</p>
          </div>
          <!-- 滚动中状态 -->
          <div v-else-if="isRolling" class="rolling-state">
            <div class="rolling-label">正在随机抽取...</div>
            <div class="rolling-name">{{ rollingName }}</div>
          </div>
          <!-- 已点名结果 -->
          <div v-else-if="calledStudent" class="result-state">
            <div class="result-label">本次点名结果</div>
            <div class="result-avatar">{{ calledStudent.name?.charAt(0) }}</div>
            <div class="result-name">{{ calledStudent.name }}</div>
            <div class="result-info">
              <span v-if="calledStudent.student_id">学号 {{ calledStudent.student_id }}</span>
              <span>{{ calledStudent.username }}</span>
            </div>
          </div>
        </div>

        <!-- 操作按钮 -->
        <div class="call-actions">
          <n-button
            type="primary"
            size="large"
            round
            :disabled="students.length === 0 || isRolling"
            @click="startRollCall"
            style="min-width: 140px;"
          >
            <template #icon>
              <n-icon><svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm-2 15l-5-5 1.41-1.41L10 14.17l7.59-7.59L19 8l-9 9z"/></svg></n-icon>
            </template>
            {{ calledStudent ? '再次点名' : '开始点名' }}
          </n-button>
          <n-button
            v-if="isRolling"
            type="error"
            size="large"
            round
            @click="stopRollCall"
            style="min-width: 140px;"
          >
            停止点名
          </n-button>
          <n-button
            v-if="calledStudent"
            type="success"
            size="large"
            round
            :loading="addScoreLoading"
            @click="addBonusScore"
            style="min-width: 140px;"
          >
            <template #icon>
              <n-icon><svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm5 10h-4v4h-2v-4H7v-2h4V6h2v4h4v2z"/></svg></n-icon>
            </template>
            +1分
          </n-button>
          <n-button
            v-if="calledStudent"
            size="large"
            round
            @click="calledStudent = null"
          >
            清除
          </n-button>
        </div>

        <!-- 统计信息 -->
        <div class="call-stats">
          共 <strong>{{ students.length }}</strong> 名学生
          &middot; 已点名 <strong>{{ calledHistory.length }}</strong> 人
          &middot; 未点名 <strong>{{ uncalledStudents.length }}</strong> 人
        </div>
      </div>

      <!-- 右侧：历史和未点名 -->
      <div class="side-panel">
        <div class="panel-card">
          <div class="panel-title">点名历史</div>
          <div v-if="calledHistory.length === 0" class="panel-empty">暂无记录</div>
          <div v-else class="history-list">
            <div v-for="(item, index) in calledHistory" :key="index" class="history-item">
              <span class="history-badge" :class="{ recent: index === 0 }">
                {{ index === 0 ? '最新' : `#${calledHistory.length - index}` }}
              </span>
              <span class="history-name">{{ item.name }}</span>
              <span class="history-score" v-if="sessionScores[item.id]">
                +{{ sessionScores[item.id] }}分
              </span>
              <span class="history-id">{{ item.student_id || '' }}</span>
            </div>
          </div>
        </div>

        <div class="panel-card">
          <div class="panel-title">未点名 ({{ uncalledStudents.length }})</div>
          <div v-if="uncalledStudents.length === 0" class="panel-empty">全部已点名</div>
          <div v-else class="uncalled-grid">
            <span v-for="s in uncalledStudents" :key="s.id" class="uncalled-tag">
              {{ s.name }}
            </span>
          </div>
        </div>
      </div>
    </div>

    <!-- 底部：加分排行 -->
    <div class="rank-section" v-if="rankedStudents.length > 0">
      <div class="rank-header">
        <h3>本次会话加分排行</h3>
        <n-tag type="warning" size="small">仅统计本次页面操作</n-tag>
      </div>
      <div class="rank-list">
        <div
          v-for="(item, index) in rankedStudents"
          :key="item.id"
          class="rank-item"
          :class="{ 'rank-top': index < 3 }"
        >
          <span class="rank-medal" v-if="index === 0">🥇</span>
          <span class="rank-medal" v-else-if="index === 1">🥈</span>
          <span class="rank-medal" v-else-if="index === 2">🥉</span>
          <span class="rank-num" v-else>{{ index + 1 }}</span>
          <span class="rank-name">{{ item.name }}</span>
          <span class="rank-score">+{{ item.score }}分</span>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useMessage } from 'naive-ui'
import { authApi, adminApi } from '@/api'

const message = useMessage()
const students = ref<any[]>([])
const selectedClass = ref<number | null>(null)
const classOptions = ref<{ label: string; value: number }[]>([])
const isRolling = ref(false)
const rollingName = ref('')
const calledStudent = ref<any>(null)
const calledHistory = ref<any[]>([])
const calledIds = ref<Set<number>>(new Set())
const addScoreLoading = ref(false)
const settings = ref({ rollcall_score: 5, rollcall_auto_score: false })

// 本次会话加分统计（前端维护，页面刷新清零）
const sessionScores = ref<Record<number, number>>({})

const uncalledStudents = computed(() => students.value.filter(s => !calledIds.value.has(s.id)))

// 加分排行：按分数降序，分数相同按姓名排序
const rankedStudents = computed(() => {
  return Object.entries(sessionScores.value)
    .filter(([_, score]) => score > 0)
    .map(([id, score]) => {
      const student = students.value.find(s => s.id === Number(id))
      return { id: Number(id), name: student?.name || `学生${id}`, score }
    })
    .sort((a, b) => b.score - a.score || a.name.localeCompare(b.name, 'zh-CN'))
})

let rollTimer: ReturnType<typeof setInterval> | null = null

async function loadStudents() {
  try {
    students.value = await adminApi.getStudents(selectedClass.value || undefined) as any
    // 重置状态
    calledStudent.value = null
    calledHistory.value = []
    calledIds.value = new Set()
  } catch (error: any) {
    message.error(error?.detail || '加载学生列表失败')
  }
}

async function loadClasses() {
  try {
    const data = await authApi.getClasses() as any
    classOptions.value = data.map((c: any) => ({ label: c.name, value: c.id }))
  } catch (error: any) {
    message.error(error?.detail || '加载班级列表失败')
  }
}

async function loadSettings() {
  try {
    const data = await authApi.getSettings() as any
    settings.value.rollcall_score = data.rollcall_score || 5
    settings.value.rollcall_auto_score = data.rollcall_auto_score || false
  } catch (error: any) {
    message.error(error?.detail || '加载设置失败')
  }
}

// 开始点名
function startRollCall() {
  if (students.value.length === 0) return
  isRolling.value = true
  calledStudent.value = null

  rollTimer = setInterval(() => {
    const random = students.value[Math.floor(Math.random() * students.value.length)]
    rollingName.value = random.name
  }, 100)
}

// 停止点名
function stopRollCall() {
  if (rollTimer) {
    clearInterval(rollTimer)
    rollTimer = null
  }
  isRolling.value = false

  // 随机选一个学生作为最终结果
  const random = students.value[Math.floor(Math.random() * students.value.length)]
  calledStudent.value = random
  calledHistory.value.unshift(random)
  calledIds.value.add(random.id)

  // 记录到后端
  adminApi.recordRollcall({
    student_id: random.id,
    class_id: selectedClass.value || undefined
  }).then(() => {
    if (settings.value.rollcall_auto_score) {
      message.success(`${random.name} 已出勤 +${settings.value.rollcall_score}分`)
    }
  }).catch(() => {})
}

// +1分
async function addBonusScore() {
  if (!calledStudent.value) return
  addScoreLoading.value = true
  try {
    await adminApi.adjustScore(calledStudent.value.id, {
      adjustment: 1,
      reason: '课堂点名加分'
    })
    // 更新前端统计
    const sid = calledStudent.value.id
    sessionScores.value[sid] = (sessionScores.value[sid] || 0) + 1
    message.success(`${calledStudent.value.name} +1分`)
  } catch (error: any) {
    message.error(error?.detail || '加分失败')
  } finally {
    addScoreLoading.value = false
  }
}

onMounted(() => {
  loadClasses()
  loadStudents()
  loadSettings()
})
</script>

<style scoped>
.roll-call-container {
  max-width: 1100px;
  margin: 0 auto;
}

.top-bar {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 24px;
}
.top-bar h2 { margin: 0; font-size: 20px; }

.main-area {
  display: flex;
  gap: 24px;
}

/* 左侧点名区 */
.call-zone {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
}

.call-display {
  width: 100%;
  min-height: 300px;
  background: #fff;
  border-radius: 20px;
  border: 2px dashed #d0d4dc;
  display: flex;
  align-items: center;
  justify-content: center;
  transition: all 0.3s;
  margin-bottom: 24px;
}
.call-display.rolling {
  border-color: #3498db;
  border-style: solid;
  background: #f0f6ff;
}
.call-display.called {
  border-color: #e74c3c;
  border-style: solid;
  background: #fff5f5;
}

.init-state { text-align: center; }
.init-icon { margin-bottom: 16px; }
.init-text { color: #999; font-size: 15px; margin: 0; }

.rolling-state { text-align: center; }
.rolling-label { font-size: 16px; color: #3498db; margin-bottom: 12px; }
.rolling-name {
  font-size: 56px;
  font-weight: 800;
  color: #3498db;
  letter-spacing: 4px;
  animation: pulse 0.08s infinite alternate;
}

.result-state { text-align: center; padding: 20px; }
.result-label { font-size: 14px; color: #999; margin-bottom: 16px; }
.result-avatar {
  width: 80px; height: 80px; border-radius: 50%;
  background: linear-gradient(135deg, #e74c3c, #c0392b);
  color: white; font-size: 32px; font-weight: 700;
  display: flex; align-items: center; justify-content: center;
  margin: 0 auto 16px;
}
.result-name { font-size: 32px; font-weight: 800; color: #e74c3c; margin-bottom: 8px; }
.result-info { display: flex; gap: 20px; justify-content: center; color: #666; font-size: 14px; }

.call-actions {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
  flex-wrap: wrap;
  justify-content: center;
}

.call-stats { font-size: 14px; color: #999; }
.call-stats strong { color: #1e1e2d; font-weight: 600; }

/* 右侧面板 */
.side-panel {
  width: 320px;
  display: flex;
  flex-direction: column;
  gap: 16px;
  flex-shrink: 0;
}
.panel-card {
  background: #fff;
  border-radius: 12px;
  border: 1px solid #e8e8ec;
  padding: 16px;
}
.panel-title { font-size: 14px; font-weight: 600; color: #1e1e2d; margin-bottom: 12px; }
.panel-empty { color: #ccc; font-size: 13px; text-align: center; padding: 20px 0; }
.history-list { max-height: 300px; overflow-y: auto; }
.history-item {
  display: flex; align-items: center; gap: 10px;
  padding: 8px 0; border-bottom: 1px solid #f5f5f9;
}
.history-item:last-child { border-bottom: none; }
.history-badge {
  font-size: 11px; font-weight: 600; padding: 2px 8px;
  border-radius: 10px; background: #f0f0f4; color: #666; flex-shrink: 0;
}
.history-badge.recent { background: #6366f1; color: white; }
.history-name { font-size: 14px; font-weight: 500; color: #1e1e2d; }
.history-score {
  font-size: 12px; font-weight: 600; color: #2ecc71;
  background: #eafaf1; padding: 1px 6px; border-radius: 4px;
}
.history-id { font-size: 12px; color: #999; margin-left: auto; }
.uncalled-grid { display: flex; flex-wrap: wrap; gap: 6px; max-height: 200px; overflow-y: auto; }
.uncalled-tag { font-size: 12px; padding: 4px 10px; border-radius: 6px; background: #f5f5f9; color: #666; }

/* 加分排行 */
.rank-section {
  margin-top: 32px;
  background: #fff;
  border-radius: 16px;
  border: 1px solid #e8e8ec;
  padding: 24px;
}
.rank-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 20px;
}
.rank-header h3 { margin: 0; font-size: 18px; color: #2c3e50; }

.rank-list {
  display: flex;
  flex-wrap: wrap;
  gap: 12px;
  justify-content: center;
}
.rank-item {
  display: flex;
  align-items: center;
  gap: 8px;
  background: #f8f9fa;
  border: 1px solid #e9ecef;
  border-radius: 10px;
  padding: 10px 18px;
  min-width: 140px;
  transition: all 0.2s;
}
.rank-item.rank-top {
  background: #fff9e6;
  border-color: #f0d060;
}
.rank-medal { font-size: 20px; }
.rank-num {
  font-size: 14px; font-weight: 600; color: #999;
  width: 20px; text-align: center;
}
.rank-name { font-size: 14px; font-weight: 500; color: #1e1e2d; }
.rank-score {
  margin-left: auto;
  font-size: 16px; font-weight: 700; color: #e74c3c;
}

@keyframes pulse {
  from { opacity: 0.6; transform: scale(0.97); }
  to { opacity: 1; transform: scale(1.03); }
}

/* 响应式 */
@media (max-width: 768px) {
  .main-area { flex-direction: column; }
  .side-panel { width: 100%; }
  .call-display { min-height: 240px; }
  .rolling-name { font-size: 40px; }
  .result-name { font-size: 24px; }
  .result-avatar { width: 60px; height: 60px; font-size: 24px; }
  .rank-list { flex-direction: column; }
  .rank-item { width: 100%; }
}
</style>
