<template>
  <div class="system-stats-container">
    <n-space justify="space-between" align="center" style="margin-bottom: 24px;">
      <h2>系统统计</h2>
    </n-space>

    <n-spin :show="loading">
      <!-- 概览卡片 -->
      <n-grid :cols="4" :x-gap="16" style="margin-bottom: 24px;">
        <n-gi>
          <n-card>
            <n-statistic label="总用户数" :value="stats.total_users" />
          </n-card>
        </n-gi>
        <n-gi>
          <n-card>
            <n-statistic label="活跃用户" :value="stats.active_users" />
          </n-card>
        </n-gi>
        <n-gi>
          <n-card>
            <n-statistic label="总班级数" :value="stats.total_classes" />
          </n-card>
        </n-gi>
        <n-gi>
          <n-card>
            <n-statistic label="总任务数" :value="stats.total_tasks" />
          </n-card>
        </n-gi>
      </n-grid>

      <n-grid :cols="4" :x-gap="16" style="margin-bottom: 24px;">
        <n-gi>
          <n-card>
            <n-statistic label="总提交次数" :value="stats.total_submissions" />
          </n-card>
        </n-gi>
        <n-gi>
          <n-card>
            <n-statistic label="AI 调用次数" :value="stats.total_ai_calls" />
          </n-card>
        </n-gi>
        <n-gi>
          <n-card>
            <n-statistic label="Token 消耗" :value="stats.total_tokens" />
          </n-card>
        </n-gi>
        <n-gi>
          <n-card>
            <n-statistic label="禁用用户" :value="(stats.total_users || 0) - (stats.active_users || 0)" />
          </n-card>
        </n-gi>
      </n-grid>

      <n-grid :cols="2" :x-gap="16">
        <!-- 角色分布 -->
        <n-gi>
          <n-card title="用户角色分布">
            <n-space vertical :size="12">
              <div v-for="(count, role) in stats.role_distribution" :key="role" style="display: flex; align-items: center; gap: 12px;">
                <span style="width: 60px;">{{ getRoleName(String(role)) }}</span>
                <n-progress
                  type="line"
                  :percentage="Math.round(((Number(count)) / (stats.total_users || 1)) * 100)"
                  :status="getRoleStatus(String(role))"
                  style="flex: 1;"
                />
                <span style="width: 40px; text-align: right;">{{ count }}</span>
              </div>
            </n-space>
          </n-card>
        </n-gi>

        <!-- 注册趋势 -->
        <n-gi>
          <n-card title="最近 7 天注册趋势">
            <n-space vertical :size="8">
              <div v-for="item in stats.registration_trend" :key="item.date" style="display: flex; align-items: center; gap: 12px;">
                <span style="width: 100px;">{{ item.date }}</span>
                <n-progress
                  type="line"
                  :percentage="Math.min(100, item.count * 10)"
                  style="flex: 1;"
                />
                <span style="width: 40px; text-align: right;">{{ item.count }}</span>
              </div>
              <n-empty v-if="!stats.registration_trend || stats.registration_trend.length === 0" description="暂无数据" />
            </n-space>
          </n-card>
        </n-gi>

        <!-- 提交趋势 -->
        <n-gi>
          <n-card title="最近 7 天提交趋势">
            <n-space vertical :size="8">
              <div v-for="item in stats.submission_trend" :key="item.date" style="display: flex; align-items: center; gap: 12px;">
                <span style="width: 100px;">{{ item.date }}</span>
                <n-progress
                  type="line"
                  :percentage="Math.min(100, Math.round(item.count / Math.max(...(stats.submission_trend || []).map((s: any) => s.count), 1) * 100))"
                  style="flex: 1;"
                />
                <span style="width: 40px; text-align: right;">{{ item.count }}</span>
              </div>
              <n-empty v-if="!stats.submission_trend || stats.submission_trend.length === 0" description="暂无数据" />
            </n-space>
          </n-card>
        </n-gi>

        <!-- 系统概览 -->
        <n-gi>
          <n-card title="系统概览">
            <n-descriptions bordered :column="1">
              <n-descriptions-item label="总用户数">{{ stats.total_users }}</n-descriptions-item>
              <n-descriptions-item label="活跃用户">{{ stats.active_users }}</n-descriptions-item>
              <n-descriptions-item label="总班级数">{{ stats.total_classes }}</n-descriptions-item>
              <n-descriptions-item label="总任务数">{{ stats.total_tasks }}</n-descriptions-item>
              <n-descriptions-item label="总提交次数">{{ stats.total_submissions }}</n-descriptions-item>
              <n-descriptions-item label="AI 调用次数">{{ stats.total_ai_calls }}</n-descriptions-item>
              <n-descriptions-item label="Token 总消耗">{{ stats.total_tokens }}</n-descriptions-item>
            </n-descriptions>
          </n-card>
        </n-gi>
      </n-grid>
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { adminApi } from '@/api'

const loading = ref(false)
const stats = ref<any>({})

function getRoleName(role: string) {
  const map: Record<string, string> = { student: '学生', teacher: '教师', admin: '管理员' }
  return map[role] || role
}

function getRoleStatus(role: string) {
  const map: Record<string, string> = { student: 'info', teacher: 'warning', admin: 'error' }
  return (map[role] || 'info') as any
}

async function loadStats() {
  loading.value = true
  try {
    const data = await adminApi.getSystemStats() as any
    stats.value = data
  } catch (error) {
    console.error('加载系统统计失败', error)
  } finally {
    loading.value = false
  }
}

onMounted(() => {
  loadStats()
})
</script>

<style scoped>
.system-stats-container {
  max-width: 1400px;
  margin: 0 auto;
}
</style>
