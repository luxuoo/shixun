<template>
  <div class="roll-call-container">
    <n-space justify="space-between" align="center" style="margin-bottom: 24px;">
      <h2>课堂点名</h2>
      <n-space>
        <n-select
          v-model:value="selectedClass"
          :options="classOptions"
          placeholder="选择班级"
          clearable
          style="width: 200px;"
          @update:value="loadStudents"
        />
      </n-space>
    </n-space>

    <n-grid :cols="2" :x-gap="24">
      <!-- 左侧：点名区域 -->
      <n-gi>
        <n-card>
          <n-space vertical :size="24" align="center">
            <!-- 点名显示区 -->
            <div class="roll-call-display" :class="{ rolling: isRolling, called: calledStudent }">
              <div v-if="!calledStudent && !isRolling" class="placeholder">
                <n-icon size="64" color="#ccc">
                  <svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/></svg>
                </n-icon>
                <p style="color: #999; margin-top: 12px;">点击下方按钮开始点名</p>
              </div>
              <div v-else-if="isRolling" class="rolling-name">
                {{ rollingName }}
              </div>
              <div v-else-if="calledStudent" class="called-info">
                <n-tag type="success" size="large" style="font-size: 20px; padding: 12px 24px;">
                  {{ calledStudent.name }}
                </n-tag>
                <n-descriptions bordered :column="1" style="margin-top: 16px; width: 100%;">
                  <n-descriptions-item label="姓名">{{ calledStudent.name }}</n-descriptions-item>
                  <n-descriptions-item label="学号">{{ calledStudent.student_id || '-' }}</n-descriptions-item>
                  <n-descriptions-item label="用户名">{{ calledStudent.username }}</n-descriptions-item>
                </n-descriptions>
              </div>
            </div>

            <!-- 操作按钮 -->
            <n-space>
              <n-button
                type="primary"
                size="large"
                :disabled="students.length === 0 || isRolling"
                @click="startRollCall"
              >
                {{ calledStudent ? '再次点名' : '开始点名' }}
              </n-button>
              <n-button
                v-if="calledStudent"
                size="large"
                @click="calledStudent = null"
              >
                清除
              </n-button>
            </n-space>

            <n-text depth="3">
              共 {{ students.length }} 名学生，已点名 {{ calledHistory.length }} 人
            </n-text>
          </n-space>
        </n-card>
      </n-gi>

      <!-- 右侧：点名历史和未点名列表 -->
      <n-gi>
        <n-space vertical :size="16">
          <!-- 点名历史 -->
          <n-card title="点名历史">
            <n-empty v-if="calledHistory.length === 0" description="暂无点名记录" />
            <n-list v-else bordered>
              <n-list-item v-for="(item, index) in calledHistory" :key="index">
                <n-thing>
                  <template #header>
                    <n-space align="center">
                      <n-tag :type="index === 0 ? 'error' : 'info'" size="small">
                        {{ index === 0 ? '最近' : `第${calledHistory.length - index}次` }}
                      </n-tag>
                      {{ item.name }}
                      <n-text depth="3" style="font-size: 12px;">{{ item.student_id }}</n-text>
                    </n-space>
                  </template>
                </n-thing>
              </n-list-item>
            </n-list>
          </n-card>

          <!-- 未点名学生 -->
          <n-card title="未点名学生">
            <n-empty v-if="uncalledStudents.length === 0" description="所有学生都已点名" />
            <n-space v-else wrap>
              <n-tag v-for="s in uncalledStudents" :key="s.id" size="small">
                {{ s.name }} ({{ s.student_id || s.username }})
              </n-tag>
            </n-space>
          </n-card>
        </n-space>
      </n-gi>
    </n-grid>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { authApi } from '@/api'

const students = ref<any[]>([])
const selectedClass = ref<number | null>(null)
const classOptions = ref<{ label: string; value: number }[]>([])
const isRolling = ref(false)
const rollingName = ref('')
const calledStudent = ref<any>(null)
const calledHistory = ref<any[]>([])
const calledIds = ref<Set<number>>(new Set())

const uncalledStudents = computed(() => {
  return students.value.filter(s => !calledIds.value.has(s.id))
})

async function loadStudents() {
  try {
    const data = await authApi.getClasses() as any
    classOptions.value = data.map((c: any) => ({ label: c.name, value: c.id }))
  } catch {}
  try {
    const { adminApi } = await import('@/api')
    const data = await adminApi.getStudents(selectedClass.value || undefined) as any
    students.value = data
  } catch {}
}

async function loadClasses() {
  try {
    const data = await authApi.getClasses() as any
    classOptions.value = data.map((c: any) => ({ label: c.name, value: c.id }))
  } catch {}
}

function startRollCall() {
  if (students.value.length === 0) return

  isRolling.value = true
  calledStudent.value = null

  const duration = 2000
  const interval = 80
  let elapsed = 0

  const timer = setInterval(() => {
    const random = students.value[Math.floor(Math.random() * students.value.length)]
    rollingName.value = random.name
    elapsed += interval

    if (elapsed >= duration) {
      clearInterval(timer)
      isRolling.value = false
      calledStudent.value = random
      calledHistory.value.unshift(random)
      calledIds.value.add(random.id)
    }
  }, interval)
}

onMounted(() => {
  loadClasses()
  loadStudents()
})
</script>

<style scoped>
.roll-call-container {
  max-width: 1200px;
  margin: 0 auto;
}

.roll-call-display {
  width: 100%;
  min-height: 260px;
  display: flex;
  align-items: center;
  justify-content: center;
  border-radius: 16px;
  background: #f8f8fa;
  transition: all 0.3s;
}

.roll-call-display.called {
  background: #f0faf0;
}

.placeholder {
  text-align: center;
}

.rolling-name {
  font-size: 48px;
  font-weight: bold;
  color: #2080f0;
  animation: pulse 0.1s infinite alternate;
}

.called-info {
  text-align: center;
  padding: 20px;
}

@keyframes pulse {
  from { opacity: 0.5; transform: scale(0.95); }
  to { opacity: 1; transform: scale(1.05); }
}
</style>
