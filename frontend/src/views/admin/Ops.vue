<template>
  <div class="ops" :class="{ dark: themeStore.isDark }">
    <header class="page-head">
      <div>
        <h2>部署运维</h2>
        <p class="sub">拉取 GitHub 最新代码 → 构建 → 切换 → 重启；新版本启动失败会自动回滚</p>
      </div>
      <n-space :size="10" align="center">
        <n-button text :loading="loading" @click="loadStatus(true)">刷新</n-button>
        <n-button :disabled="!canOperate || running" :loading="deploying" @click="handleDeploy">
          一键更新
        </n-button>
        <n-button
          secondary
          :disabled="!canOperate || running || releases.length < 2"
          :loading="rollingBack"
          @click="handleRollback()"
        >
          一键回滚
        </n-button>
      </n-space>
    </header>

    <n-alert v-if="!status.enabled" type="warning" :bordered="false" class="hint">
      部署运维未开启。在服务器 <code>.deploy/shared/.env</code>（或 <code>backend/.env</code>）中设置
      <code>OPS_ENABLED=true</code> 后重启后端即可启用；在此之前请用命令行：
      <code>bash ops/deploy.sh</code> / <code>bash ops/rollback.sh</code>。
    </n-alert>
    <n-alert v-else-if="!status.platform_ok" type="info" :bordered="false" class="hint">
      当前环境不支持在线发布（需要 Linux + bash）。本页仅展示状态，部署请在服务器上执行 ops 脚本。
    </n-alert>

    <section class="grid">
      <div class="panel">
        <div class="panel-label">当前版本</div>
        <div class="panel-main mono">{{ status.current || '尚未发布' }}</div>
        <div class="panel-meta">
          <span v-if="currentRelease">提交 {{ currentRelease.commit }}</span>
          <span v-if="currentRelease">构建 {{ currentRelease.built_at }}</span>
          <span v-if="!status.current" class="muted">执行一次更新后生成</span>
        </div>
      </div>

      <div class="panel">
        <div class="panel-label">服务状态</div>
        <div class="panel-main">
          <n-tag :type="status.health_ok ? 'success' : 'error'" size="small" :bordered="false">
            {{ status.health_ok ? '运行中' : '无响应' }}
          </n-tag>
          <span class="mono service">{{ status.service }}</span>
        </div>
        <div class="panel-meta">
          <span class="mono">{{ status.health_url }}</span>
          <span class="muted">服务器时间 {{ status.server_time || '—' }}</span>
        </div>
      </div>

      <div class="panel">
        <div class="panel-label">最近操作</div>
        <div class="panel-main">
          <n-tag :type="stateType" size="small" :bordered="false">{{ stateLabel }}</n-tag>
          <span class="step-text">{{ state.step || '—' }}</span>
        </div>
        <div class="panel-meta">
          <span v-if="state.sha" class="mono">{{ state.sha }}</span>
          <span v-if="state.finished_at">{{ state.finished_at }}</span>
          <span v-else-if="state.started_at">开始于 {{ state.started_at }}</span>
        </div>
      </div>
    </section>

    <n-alert v-if="state.error" type="error" :bordered="false" class="hint">
      {{ state.error }}
    </n-alert>

    <section class="block">
      <div class="block-head">
        <h3>版本历史</h3>
        <span class="muted">服务端默认保留最近 5 个版本，可在 ops 脚本中用 RELEASE_KEEP 调整</span>
      </div>
      <n-table :bordered="false" size="small" :single-line="false">
        <thead>
          <tr>
            <th style="width: 240px;">版本目录</th>
            <th style="width: 90px;">提交</th>
            <th>说明</th>
            <th style="width: 150px;">构建时间</th>
            <th style="width: 80px;">体积</th>
            <th style="width: 110px;">操作</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="r in releases" :key="r.name">
            <td class="mono">
              {{ r.name }}
              <n-tag v-if="r.current" size="small" type="success" :bordered="false" style="margin-left: 6px;">当前</n-tag>
            </td>
            <td class="mono">{{ r.commit }}</td>
            <td class="subject">{{ r.subject || '—' }}</td>
            <td class="mono muted">{{ r.built_at || '—' }}</td>
            <td class="mono muted">{{ r.size_mb }} MB</td>
            <td>
              <span v-if="r.current" class="muted">当前运行</span>
              <n-button
                v-else
                text
                size="tiny"
                :disabled="!canOperate || running"
                @click="handleRollback(r.name)"
              >
                回滚到此版本
              </n-button>
            </td>
          </tr>
          <tr v-if="releases.length === 0">
            <td colspan="6" class="empty">还没有发布记录，点右上角「一键更新」开始</td>
          </tr>
        </tbody>
      </n-table>
    </section>

    <section class="block">
      <div class="block-head">
        <h3>发布日志</h3>
        <n-space :size="8">
          <span class="muted">{{ running ? '执行中，自动刷新…' : '最近一次执行输出' }}</span>
          <n-button text size="tiny" @click="logOpen = !logOpen">{{ logOpen ? '收起' : '展开' }}</n-button>
        </n-space>
      </div>
      <pre v-if="logOpen" ref="logBox" class="log">{{ logText || '（暂无日志）' }}</pre>
    </section>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount, nextTick } from 'vue'
import { useMessage, useDialog } from 'naive-ui'
import { opsApi } from '@/api'
import { useThemeStore } from '@/stores/theme'

interface Release {
  name: string
  current: boolean
  commit: string
  built_at: string
  subject: string
  size_mb: number
}

const themeStore = useThemeStore()
const message = useMessage()
const dialog = useDialog()

const loading = ref(false)
const deploying = ref(false)
const rollingBack = ref(false)
const logOpen = ref(true)
const logBox = ref<HTMLElement | null>(null)

const status = ref<any>({
  enabled: false,
  platform_ok: false,
  service: '',
  health_url: '',
  health_ok: false,
  current: '',
  releases: [],
  state: {},
  log_tail: [],
  server_time: ''
})

const releases = computed<Release[]>(() => status.value.releases || [])
const state = computed<any>(() => status.value.state || {})
const running = computed(() => Boolean(status.value.running))
const canOperate = computed(() => status.value.enabled && status.value.platform_ok)
const logText = computed(() => (status.value.log_tail || []).join('\n'))

const currentRelease = computed<Release | undefined>(() =>
  releases.value.find(r => r.current)
)

const stateType = computed<any>(() => {
  const s = state.value.status
  if (s === 'running') return 'info'
  if (s === 'success') return 'success'
  if (s === 'failed') return 'error'
  return 'default'
})

const stateLabel = computed(() => {
  const s = state.value.status
  if (s === 'running') return state.value.action === 'rollback' ? '回滚中' : '发布中'
  if (s === 'success') return state.value.action === 'rollback' ? '已回滚' : '发布成功'
  if (s === 'failed') return '失败'
  if (s === 'unknown') return '异常中断'
  return '空闲'
})

let timer: ReturnType<typeof setInterval> | null = null

async function loadStatus(silent = false) {
  if (!silent) loading.value = true
  try {
    const data = await opsApi.getStatus(80) as any
    status.value = data
    await nextTick()
    if (logBox.value) logBox.value.scrollTop = logBox.value.scrollHeight
  } catch (e: any) {
    // 发布过程中后端会重启，短暂不可用属正常
    if (!silent) message.error(e?.detail || '无法获取部署状态，服务可能正在重启')
  } finally {
    loading.value = false
  }
}

function schedule() {
  if (timer) clearInterval(timer)
  // 执行中 2 秒一刷，空闲 10 秒一刷
  const interval = running.value ? 2000 : 10000
  timer = setInterval(() => loadStatus(true), interval)
}

async function handleDeploy() {
  dialog.info({
    title: '确认更新到最新版本',
    content: '将从远端拉取最新代码并重新构建，完成后自动重启后端，期间约 10 秒不可用。',
    positiveText: '开始更新',
    negativeText: '取消',
    onPositiveClick: async () => {
      deploying.value = true
      try {
        const res = await opsApi.deploy() as any
        message.success(res.message || '已开始发布')
        await loadStatus(true)
        schedule()
      } catch (e: any) {
        message.error(e?.detail || '触发失败')
      } finally {
        deploying.value = false
      }
    }
  })
}

function handleRollback(release?: string) {
  const label = release || '上一个版本'
  dialog.warning({
    title: '确认回滚',
    content: `将切回 ${label} 并重启后端。回滚不重新构建，通常 5 秒内完成；回滚后仍可再更新回最新版本。`,
    positiveText: '确定回滚',
    negativeText: '取消',
    onPositiveClick: async () => {
      rollingBack.value = true
      try {
        const res = await opsApi.rollback(release) as any
        message.success(res.message || '已开始回滚')
        await loadStatus(true)
        schedule()
      } catch (e: any) {
        message.error(e?.detail || '触发失败')
      } finally {
        rollingBack.value = false
      }
    }
  })
}

onMounted(async () => {
  await loadStatus()
  schedule()
})

onBeforeUnmount(() => {
  if (timer) clearInterval(timer)
})
</script>

<style scoped>
.ops {
  max-width: 1200px;
  margin: 0 auto;
}

.page-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
}

.page-head h2 {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
}

.sub {
  margin: 6px 0 0;
  font-size: 12.5px;
  color: var(--muted-2, #5f6673);
}

.hint {
  margin-bottom: 16px;
}

.hint code {
  padding: 1px 5px;
  border-radius: 3px;
  background: rgba(127, 127, 127, 0.14);
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 12px;
}

.grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 22px;
}

.panel {
  padding: 16px 18px;
  border: 1px solid var(--hair, #dcdfe6);
  border-radius: 4px;
  background: var(--panel, #fff);
}

.panel-label {
  font-size: 11.5px;
  letter-spacing: 0.06em;
  color: var(--muted-2, #6b7280);
  margin-bottom: 10px;
}

.panel-main {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 15px;
  font-weight: 600;
  margin-bottom: 8px;
  word-break: break-all;
}

.panel-meta {
  display: flex;
  flex-wrap: wrap;
  gap: 4px 12px;
  font-size: 11.5px;
  color: var(--muted-2, #6b7280);
}

.service {
  font-size: 12.5px;
  font-weight: 400;
}

.step-text {
  font-size: 13px;
  font-weight: 400;
}

.mono {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-variant-numeric: tabular-nums;
}

.muted {
  color: var(--muted-2, #8a919e);
}

.block {
  margin-bottom: 22px;
}

.block-head {
  display: flex;
  align-items: baseline;
  justify-content: space-between;
  margin-bottom: 10px;
}

.block-head h3 {
  margin: 0;
  font-size: 14px;
  font-weight: 600;
}

.block-head .muted {
  font-size: 11.5px;
}

.subject {
  font-size: 12.5px;
  color: var(--muted-2, #4a5160);
}

.empty {
  text-align: center;
  padding: 26px 0;
  font-size: 12.5px;
  color: var(--muted-2, #8a919e);
}

.log {
  margin: 0;
  padding: 14px 16px;
  max-height: 340px;
  overflow: auto;
  border-radius: 4px;
  background: #16171a;
  color: #d7dbd6;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 12px;
  line-height: 1.65;
  white-space: pre-wrap;
  word-break: break-all;
}

/* 暗色主题：卡片不要用固定白底 */
.ops.dark .panel {
  background: #1b1c20;
  border-color: rgba(233, 233, 230, 0.14);
}

.ops.dark .panel-main {
  color: #e9e9e6;
}

.ops.dark .subject {
  color: #c3c7cd;
}

.ops.dark .muted {
  color: #9096a0;
}

.ops.dark .panel-meta,
.ops.dark .panel-label,
.ops.dark .sub {
  color: #9096a0;
}

.ops.dark .log {
  background: #101114;
  border: 1px solid rgba(233, 233, 230, 0.12);
  color: #cfd4ce;
}

.ops.dark .empty {
  color: #9096a0;
}

/* 暗色主题：卡片不要用固定白底 */
.ops.dark .panel {
  background: #1b1c20;
  border-color: rgba(233, 233, 230, 0.14);
}

.ops.dark .panel-main {
  color: #e9e9e6;
}

.ops.dark .subject {
  color: #c3c7cd;
}

.ops.dark .muted {
  color: #9096a0;
}

.ops.dark .panel-meta,
.ops.dark .panel-label,
.ops.dark .sub {
  color: #9096a0;
}

.ops.dark .log {
  background: #101114;
  border: 1px solid rgba(233, 233, 230, 0.12);
  color: #cfd4ce;
}

.ops.dark .empty {
  color: #9096a0;
}

@media (max-width: 900px) {
  .grid {
    grid-template-columns: 1fr;
  }

  .page-head {
    flex-direction: column;
  }
}
</style>
