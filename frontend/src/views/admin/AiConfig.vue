<template>
  <div class="ai-config-container">
    <div class="page-head">
      <div>
        <h2>AI 服务配置</h2>
        <p class="sub">
          配置保存在数据库里，优先于服务器 .env 文件，保存后即时生效、无需重启。
        </p>
      </div>
      <n-space>
        <n-button :loading="testing" @click="testCurrent">测试当前服务商</n-button>
        <n-button type="primary" :loading="saving" :disabled="!dirty" @click="save">
          保存配置
        </n-button>
      </n-space>
    </div>

    <n-spin :show="loading">
      <!-- 默认服务商 -->
      <n-card size="small" class="block">
        <template #header>默认服务商</template>
        <n-space align="center">
          <n-radio-group v-model:value="form.provider" name="provider">
            <n-radio-button v-for="p in providers" :key="p.name" :value="p.name">
              {{ p.label }}
            </n-radio-button>
          </n-radio-group>
          <n-tag v-if="p0" :type="p0.configured ? 'success' : 'warning'" size="small">
            {{ p0.configured ? '已配置密钥' : '未配置密钥' }}
          </n-tag>
          <n-tag v-if="p1" :type="p1.configured ? 'success' : 'warning'" size="small">
            {{ p1.configured ? '已配置密钥' : '未配置密钥' }}
          </n-tag>
        </n-space>
        <p v-if="info.active_fallback" class="fallback-note">
          首选「{{ labelOf(info.provider) }}」未配置密钥，系统当前实际使用
          「{{ labelOf(info.active) }}」——为首选填好密钥并保存后即恢复。
        </p>
      </n-card>

      <!-- 两个服务商的连接配置 -->
      <n-grid :cols="2" :x-gap="16" responsive="screen" item-responsive style="margin-top: 16px">
        <n-gi span="24 m:12" v-for="p in providers" :key="p.name">
          <n-card size="small" class="provider-card">
            <template #header>
              <n-space align="center" :size="8">
                <span>{{ p.label }}</span>
                <n-tag :type="p.configured ? 'success' : 'error'" size="small" :bordered="false">
                  {{ p.configured ? '可用' : '不可用' }}
                </n-tag>
              </n-space>
            </template>
            <template #header-extra>
              <n-button quaternary size="tiny" :loading="testingOf[p.name]" @click="testOne(p.name)">
                测试连接
              </n-button>
            </template>

            <n-space vertical :size="14">
              <div class="field">
                <label>API Key</label>
                <n-input
                  v-model:value="form.providers[p.name].api_key"
                  type="password"
                  show-password-on="click"
                  :placeholder="p.key_masked ? `当前：${p.key_masked}（留空保持不变）` : '尚未配置，粘贴密钥后保存'"
                  :input-props="{ autocomplete: 'new-password' }"
                />
                <div class="field-meta">
                  <n-tag size="tiny" :bordered="false">
                    {{ p.source.api_key === 'db' ? '来源：数据库（后台配置）' : '来源：.env / 默认' }}
                  </n-tag>
                  <n-popconfirm v-if="p.source.api_key === 'db'" @positive-click="clearOverride(p.name, 'api_key')">
                    <template #trigger>
                      <n-button quaternary size="tiny" type="warning">
                        恢复 .env 值
                      </n-button>
                    </template>
                    删除数据库里的覆盖值，回退到服务器 .env 配置（需要 .env 里配置过才有值）。
                  </n-popconfirm>
                </div>
              </div>

              <div class="field">
                <label>API 地址</label>
                <n-input v-model:value="form.providers[p.name].api_url" :placeholder="p.api_url" />
                <div class="field-meta">
                  <n-tag size="tiny" :bordered="false">
                    {{ p.source.api_url === 'db' ? '来源：数据库' : '来源：.env / 默认' }}
                  </n-tag>
                </div>
              </div>

              <div class="field">
                <label>模型</label>
                <n-input v-model:value="form.providers[p.name].model" :placeholder="p.model" />
                <div class="field-meta">
                  <n-tag size="tiny" :bordered="false">
                    {{ p.source.model === 'db' ? '来源：数据库' : '来源：.env / 默认' }}
                  </n-tag>
                </div>
              </div>

              <n-alert v-if="testResult[p.name]" :type="testResult[p.name].ok ? 'success' : 'error'"
                       size="small" :show-icon="false" class="test-result">
                <template v-if="testResult[p.name].ok">
                  连接正常（{{ testResult[p.name].latency_ms }}ms）：{{ testResult[p.name].reply }}
                </template>
                <template v-else>
                  {{ testResult[p.name].error }}
                </template>
              </n-alert>
            </n-space>
          </n-card>
        </n-gi>
      </n-grid>
    </n-spin>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, reactive, ref } from 'vue'
import { useMessage } from 'naive-ui'
import { adminApi } from '@/api'

const message = useMessage()
const loading = ref(false)
const saving = ref(false)
const testing = ref(false)
const testingOf = reactive<Record<string, boolean>>({})
const testResult = reactive<Record<string, { ok: boolean; latency_ms?: number; reply?: string; error?: string }>>({})

interface ProviderInfo {
  name: string
  label: string
  api_url: string
  model: string
  configured: boolean
  key_masked: string
  source: { api_key: string; api_url: string; model: string }
}

const info = ref<{ provider: string; active: string; active_fallback: boolean }>({
  provider: 'mimo', active: 'mimo', active_fallback: false
})
const providers = ref<ProviderInfo[]>([])
const loaded = reactive<Record<string, { api_url: string; model: string }>>({})

const form = reactive<{
  provider: string
  providers: Record<string, { api_key: string; api_url: string; model: string }>
}>({ provider: 'mimo', providers: {} })

const p0 = computed(() => providers.value[0])
const p1 = computed(() => providers.value[1])

const labelOf = (name: string) => providers.value.find(p => p.name === name)?.label || name

/** 有任何未保存的改动时才允许保存 */
const dirty = computed(() => {
  if (form.provider !== info.value.provider) return true
  for (const p of providers.value) {
    const f = form.providers[p.name]
    if (!f) continue
    if (f.api_key.trim() !== '') return true
    if (f.api_url !== (loaded[p.name]?.api_url ?? '')) return true
    if (f.model !== (loaded[p.name]?.model ?? '')) return true
  }
  return false
})

async function load() {
  loading.value = true
  try {
    const data = await adminApi.getAiConfig() as any
    info.value = { provider: data.provider, active: data.active, active_fallback: data.active_fallback }
    providers.value = data.providers
    form.provider = data.provider
    for (const p of data.providers) {
      form.providers[p.name] = { api_key: '', api_url: p.api_url, model: p.model }
      loaded[p.name] = { api_url: p.api_url, model: p.model }
    }
  } catch (e: any) {
    message.error(e?.detail || e?.message || '加载配置失败')
  } finally {
    loading.value = false
  }
}

async function save() {
  saving.value = true
  try {
    const payload: {
      provider?: string
      providers?: Record<string, { api_key?: string; api_url?: string; model?: string }>
    } = {}
    if (form.provider !== info.value.provider) payload.provider = form.provider

    const changed: Record<string, { api_key?: string; api_url?: string; model?: string }> = {}
    for (const p of providers.value) {
      const f = form.providers[p.name]
      if (!f) continue
      const item: { api_key?: string; api_url?: string; model?: string } = {}
      // 密钥只在填写了新值时提交（留空 = 保持现状）
      if (f.api_key.trim() !== '') item.api_key = f.api_key.trim()
      if (f.api_url !== (loaded[p.name]?.api_url ?? '')) item.api_url = f.api_url.trim()
      if (f.model !== (loaded[p.name]?.model ?? '')) item.model = f.model.trim()
      if (Object.keys(item).length) changed[p.name] = item
    }
    if (Object.keys(changed).length) payload.providers = changed

    if (!Object.keys(payload).length) {
      message.info('没有改动需要保存')
      return
    }
    await adminApi.updateAiConfig(payload)
    message.success('已保存，配置即时生效（无需重启服务）')
    await load()
  } catch (e: any) {
    message.error(e?.detail || e?.message || '保存失败')
  } finally {
    saving.value = false
  }
}

async function clearOverride(provider: string, field: string) {
  try {
    await adminApi.updateAiConfig({ clear: [`ai.${provider}.${field}`] })
    message.success(`已恢复 ${labelOf(provider)} 的 ${field} 为 .env 配置`)
    await load()
  } catch (e: any) {
    message.error(e?.detail || e?.message || '操作失败')
  }
}

async function testOne(provider: string) {
  testingOf[provider] = true
  delete testResult[provider]
  try {
    const data = await adminApi.testAi(provider) as any
    testResult[provider] = data.status === 'ok'
      ? { ok: true, latency_ms: data.latency_ms, reply: (data.test_result?.content || '').slice(0, 120) }
      : { ok: false, error: data.error || '连接失败' }
  } catch (e: any) {
    testResult[provider] = { ok: false, error: e?.detail || e?.message || '请求失败' }
  } finally {
    testingOf[provider] = false
  }
}

async function testCurrent() {
  testing.value = true
  try {
    const data = await adminApi.testAi() as any
    if (data.status === 'ok') {
      message.success(`当前服务商 ${data.provider} 连接正常（${data.latency_ms}ms）`)
    } else {
      message.error(`连接失败：${data.error || '未知错误'}`)
    }
  } catch (e: any) {
    message.error(e?.detail || e?.message || '请求失败')
  } finally {
    testing.value = false
  }
}

onMounted(load)
</script>

<style scoped>
.ai-config-container {
  max-width: 1080px;
}

.page-head {
  display: flex;
  justify-content: space-between;
  align-items: flex-start;
  gap: 16px;
  margin-bottom: 20px;
}

.page-head h2 {
  margin: 0 0 6px;
  font-size: 22px;
}

.sub {
  margin: 0;
  font-size: 13px;
  color: var(--n-text-color-3, #888);
}

.fallback-note {
  margin: 12px 0 0;
  font-size: 12.5px;
  padding: 8px 12px;
  border-radius: 4px;
  background: rgba(240, 160, 32, 0.1);
  color: #b4740f;
}

.provider-card {
  height: 100%;
}

.field label {
  display: block;
  margin-bottom: 6px;
  font-size: 12.5px;
  font-weight: 600;
  letter-spacing: 0.02em;
}

.field-meta {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 6px;
}

.test-result {
  word-break: break-all;
}

.block {
  margin-bottom: 4px;
}

@media (max-width: 640px) {
  .page-head {
    flex-direction: column;
  }
}
</style>
