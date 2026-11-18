<template>
  <div class="ops" :class="{ dark: themeStore.isDark }">
    <header class="page-head">
      <div>
        <h2>部署运维</h2>
        <p class="sub">拉取所选源最新代码 → 构建 → 切换 → 重启；新版本启动失败会自动回滚</p>
      </div>
      <n-space :size="10" align="center">
        <n-select
          v-model:value="remote"
          :options="remoteOptions"
          size="small"
          style="width: 168px"
          :disabled="running"
          @update:value="onRemoteChange"
        />
        <BoardUI as="Button" :config="{ variant: 'ghost', size: 'small', disabled: loading, onClick: () => loadStatus(true), children: loading ? '刷新中…' : '刷新' }" />
        <BoardUI as="Button" :config="{ variant: 'ghost', size: 'small', disabled: !status.platform_ok || checking, onClick: handleCheck, children: checking ? '检查中…' : '检查更新' }" />
        <BoardUI as="Button" :config="{ variant: 'primary', disabled: !canOperate || running || deploying, onClick: handleDeploy, children: deploying ? '发布中…' : '一键更新' }" />
        <BoardUI as="Button" :config="{ variant: 'secondary', disabled: !canOperate || running || releases.length < 2 || rollingBack, onClick: () => handleRollback(), children: rollingBack ? '回滚中…' : '一键回滚' }" />
      </n-space>
    </header>

    <n-alert v-if="!status.enabled && !offline" type="warning" :bordered="false" class="hint">
      部署运维未开启。在服务器 <code>.deploy/shared/.env</code>（或 <code>backend/.env</code>）中设置
      <code>OPS_ENABLED=true</code> 后重启后端即可启用；在此之前请用命令行：
      <code>bash ops/deploy.sh</code> / <code>bash ops/rollback.sh</code>。
    </n-alert>
    <n-alert v-else-if="!status.platform_ok" type="info" :bordered="false" class="hint">
      当前环境不支持在线发布（需要 Linux + bash）。本页仅展示状态，部署请在服务器上执行 ops 脚本。
    </n-alert>

    <n-alert v-if="offline" type="warning" :bordered="false" class="hint">
      连接不上后端（服务多半正在重启）。页面会自动重连并保留上次状态，不需要手动刷新。
    </n-alert>

    <n-alert v-if="scriptsStale" type="warning" :bordered="false" class="hint">
      面板执行的是项目目录里的脚本，而目录当前检出 <code>{{ status.repo_head }}</code>，
      与线上运行的 <code>{{ status.current_commit }}</code> 不一致。
      先在服务器执行 <code>cd {{ status.project_dir }} &amp;&amp; git pull</code>，
      否则点按钮跑的是旧脚本（可能不认识新参数或带着已修的问题）。
    </n-alert>

    <n-alert v-if="drift" type="error" :bordered="false" class="hint">
      进程仍在运行 <code>{{ runningCommit }}</code>，但当前版本目录是
      <code>{{ status.current_commit }}</code> —— 说明服务没重启到新代码。
      先执行 <code>sudo systemctl restart {{ status.service }}</code>；仍无效则检查服务单元的
      WorkingDirectory 是否指向 <code>.deploy/current/backend</code>
      （可重跑 <code>sudo bash ops/install-service.sh</code>）。
    </n-alert>

    <section v-if="checkResult" class="update-box">
      <div class="update-body">
        <template v-if="checkResult.ok">
          <div class="update-head">
            <n-tag v-if="checkResult.behind" type="warning" size="small" :bordered="false">
              落后 {{ checkResult.behind }} 个提交
            </n-tag>
            <n-tag v-else type="success" size="small" :bordered="false">已是最新</n-tag>
            <n-tag size="small" :bordered="false" type="info">{{ checkResult.remote || 'origin' }}</n-tag>
            <span class="mono">{{ checkResult.current_commit || '未发布' }} → {{ checkResult.latest_commit }}</span>
            <span v-if="checkResult.changed_count" class="muted">{{ checkResult.changed_count }} 个文件变更</span>
          </div>
          <ul v-if="checkResult.commits && checkResult.commits.length" class="commit-list">
            <li v-for="c in checkResult.commits.slice(0, 5)" :key="c.sha">
              <span class="mono sha">{{ c.sha }}</span>
              <span class="subject">{{ c.subject }}</span>
              <span class="muted time">{{ c.time }}</span>
            </li>
          </ul>
          <p v-if="checkResult.note" class="note muted">{{ checkResult.note }}</p>
          <p v-else-if="checkResult.behind" class="note muted">
            更新会重新安装依赖并构建前端，约 1–3 分钟；期间页面可正常访问，最后重启约 10 秒。
          </p>
        </template>
        <div v-else class="update-head">
          <n-tag type="error" size="small" :bordered="false">检查失败</n-tag>
          <span class="subject">{{ checkResult.error }}</span>
        </div>
      </div>
      <n-button text size="tiny" class="dismiss" @click="checkResult = null">关闭</n-button>
    </section>

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
        <div class="panel-label">进程运行版本</div>
        <div class="panel-main">
          <n-tag :type="status.health_ok ? 'success' : 'error'" size="small" :bordered="false">
            {{ status.health_ok ? '运行中' : '无响应' }}
          </n-tag>
          <span class="mono">{{ runningCommit || '—' }}</span>
        </div>
        <div class="panel-meta">
          <span v-if="runningInfo.started_at">启动于 {{ runningInfo.started_at }}</span>
          <span v-if="runningInfo.pid" class="mono">pid {{ runningInfo.pid }}</span>
          <span class="muted">{{ status.service }}</span>
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
          <span v-if="state.actor">操作者 {{ state.actor }}</span>
          <span v-if="state.duration_sec != null">耗时 {{ fmtDuration(state.duration_sec) }}</span>
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
        <span class="muted">服务端默认保留最近 3 个版本，可在 ops 脚本中用 RELEASE_KEEP 调整</span>
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
        <h3>操作记录</h3>
        <span class="muted">最近 15 条，命令行与后台触发都会记录</span>
      </div>
      <n-table :bordered="false" size="small" :single-line="false">
        <thead>
          <tr>
            <th style="width: 150px;">时间</th>
            <th style="width: 70px;">动作</th>
            <th style="width: 230px;">版本</th>
            <th style="width: 85px;">提交</th>
            <th style="width: 80px;">结果</th>
            <th style="width: 130px;">操作者</th>
            <th>说明</th>
          </tr>
        </thead>
        <tbody>
          <tr v-for="(h, i) in history" :key="i">
            <td class="mono muted">{{ h.time }}</td>
            <td>{{ h.action === 'rollback' ? '回滚' : '更新' }}</td>
            <td class="mono">{{ h.release }}</td>
            <td class="mono">{{ h.commit }}</td>
            <td>
              <n-tag size="small" :bordered="false" :type="h.result === 'success' ? 'success' : h.result === 'skipped' ? 'default' : 'error'">
                {{ resultLabel(h.result) }}
              </n-tag>
            </td>
            <td>{{ h.actor }}</td>
            <td class="subject">{{ h.detail }}</td>
          </tr>
          <tr v-if="history.length === 0">
            <td colspan="7" class="empty">还没有操作记录</td>
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
const checking = ref(false)
const remote = ref('origin')
const remoteOptions = [
  { label: 'origin · 主仓库', value: 'origin' },
  { label: 'github · 镜像', value: 'github' },
  { label: 'cnb · 镜像', value: 'cnb' }
]
function onRemoteChange() {
  checkResult.value = null
}
const offline = ref(false)
const checkResult = ref<any>(null)
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
  current_commit: '',
  repo_head: '',
  scripts_stale: false,
  running_info: {},
  drift: false,
  releases: [],
  history: [],
  state: {},
  log_tail: [],
  server_time: ''
})

const releases = computed<Release[]>(() => status.value.releases || [])
const history = computed<any[]>(() => status.value.history || [])
const runningInfo = computed<any>(() => status.value.running_info || {})
const runningCommit = computed(() => runningInfo.value.commit || '')
const drift = computed(() => Boolean(status.value.drift))
const scriptsStale = computed(() => Boolean(status.value.scripts_stale))
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

function fmtDuration(sec: number | null | undefined) {
  if (sec === null || sec === undefined) return '—'
  if (sec < 60) return `${sec}s`
  const m = Math.floor(sec / 60)
  const s = sec % 60
  return s ? `${m}m${s}s` : `${m}m`
}

function resultLabel(r: string) {
  if (r === 'success') return '成功'
  if (r === 'skipped') return '跳过'
  return '失败'
}

let timer: ReturnType<typeof setInterval> | null = null

async function loadStatus(silent = false) {
  if (!silent) loading.value = true
  try {
    const data = await opsApi.getStatus(80) as any
    status.value = data
    offline.value = false
    await nextTick()
    if (logBox.value) logBox.value.scrollTop = logBox.value.scrollHeight
  } catch (e: any) {
    // 发布/回滚会重启服务，这几秒连不上是正常现象：标记断线并继续重试，
    // 不清空已有数据，也不再弹 toast 干扰操作
    offline.value = true
    if (!silent && !running.value) message.error(e?.detail || '无法获取部署状态')
  } finally {
    loading.value = false
  }
}

function schedule() {
  if (timer) clearInterval(timer)
  // 执行中 2 秒一刷，空闲 10 秒一刷
  const interval = running.value || offline.value ? 2000 : 10000
  timer = setInterval(() => loadStatus(true), interval)
}

async function handleCheck() {
  checking.value = true
  try {
    const data = await opsApi.check(remote.value) as any
    checkResult.value = data
    if (data.ok && data.behind === 0) message.success('已经是最新版本')
  } catch (e: any) {
    checkResult.value = { ok: false, error: e?.detail || '检查失败，服务可能正在重启' }
  } finally {
    checking.value = false
  }
}

async function handleDeploy() {
  const sourceLabel = remoteOptions.find(o => o.value === remote.value)?.label || remote.value
  dialog.info({
    title: '确认更新到最新版本',
    content: `将从 ${sourceLabel} 拉取最新代码并重新构建，完成后自动重启后端，期间约 10 秒不可用。`,
    positiveText: '开始更新',
    negativeText: '取消',
    onPositiveClick: async () => {
      deploying.value = true
      try {
        const res = await opsApi.deploy({ remote: remote.value }) as any
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
  color: var(--t3);
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

.update-box {
  display: flex;
  align-items: flex-start;
  gap: 12px;
  padding: 14px 16px;
  margin-bottom: 16px;
  border: 1px solid var(--line-input);
  border-left: 2px solid #d0a54a;
  border-radius: 2px;
  background: var(--c-card);
}

.update-body {
  flex: 1;
  min-width: 0;
}

.update-head {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  font-size: 13px;
}

.commit-list {
  margin: 10px 0 0;
  padding: 0;
  list-style: none;
  font-size: 12.5px;
}

.commit-list li {
  display: flex;
  align-items: baseline;
  gap: 10px;
  padding: 3px 0;
}

.commit-list .sha {
  color: var(--t2);
  flex: 0 0 auto;
}

.commit-list .subject {
  flex: 1;
  min-width: 0;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.commit-list .time {
  flex: 0 0 auto;
  font-size: 11.5px;
}

.note {
  margin: 10px 0 0;
  font-size: 11.5px;
}

.dismiss {
  flex: 0 0 auto;
}

.grid {
  display: grid;
  grid-template-columns: repeat(3, minmax(0, 1fr));
  gap: 14px;
  margin-bottom: 22px;
}

.panel {
  padding: 16px 18px;
  border: 1px solid var(--line-input);
  border-radius: 4px;
  background: var(--c-card);
}

.panel-label {
  font-size: 11.5px;
  letter-spacing: 0.06em;
  color: var(--t2);
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
  color: var(--t2);
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
  color: var(--t4);
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
  color: var(--t2);
}

.empty {
  text-align: center;
  padding: 26px 0;
  font-size: 12.5px;
  color: var(--t4);
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

/* 发布日志是刻意的黑色终端区域，两种主题下都保持深色；暗色下仅微调底色与边线 */
.ops.dark .log {
  background: #101114;
  border: 1px solid rgba(233, 233, 230, 0.12);
  color: #cfd4ce;
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
