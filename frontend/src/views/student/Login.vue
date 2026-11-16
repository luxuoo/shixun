<template>
  <div class="auth mono-theme" :class="{ dark: themeStore.isDark }">
    <!-- 背景角色：大、在下、跟随鼠标，不抢内容 -->
    <div class="bg-bot" aria-hidden="true">
      <AoraBot
        shape="circle"
        :color="bgBotColor"
        state="reading"
        face="eyes"
        :sizePx="400"
        followPointer
        seed="login-bg-bot"
      />
    </div>

    <!-- 左：墨色信息面板 -->
    <aside class="pane-info">
      <div class="info-top">
        <AoraBot shape="bot" color="cyan" face="eyes" :sizePx="24" :lineWeight="1.15" seed="login-logo" />
        <span class="brand-name">实训教学平台</span>
      </div>

      <div class="info-body">
        <div class="mascot">
          <AoraBot
            shape="circle"
            color="cyan"
            face="eyes"
            :state="loading ? 'thinking' : errorMsg ? 'shy' : 'reading'"
            :sizePx="92"
            seed="login-mascot"
          />
        </div>
        <p class="eyebrow">PROGRAMMING PRACTICUM</p>
        <h2 class="tagline">写代码这件事<br />得一步一步来</h2>

        <ol class="steps">
          <li v-for="s in steps" :key="s.title">
            <span class="idx">{{ s.num }}</span>
            <div>
              <strong>{{ s.title }}</strong>
              <p>{{ s.desc }}</p>
            </div>
          </li>
        </ol>
      </div>

      <div class="info-foot">
        <span>提示分级 · 思路引导 → API 指引 → 关键代码</span>
      </div>
    </aside>

    <!-- 右：表单 -->
    <main class="pane-form">
      <button class="theme" type="button" @click="themeStore.toggle()">
        {{ themeStore.isDark ? '日间' : '夜间' }}
      </button>

      <div class="form-wrap">
        <div class="mobile-brand">
          <AoraBot shape="bot" color="cyan" face="eyes" :sizePx="22" :lineWeight="1.15" seed="login-logo" />
          <span>实训教学平台</span>
        </div>

        <div class="intro">
          <h1>登录</h1>
          <p>使用教师分配的账号进入实训环境。</p>
        </div>

        <form class="form" novalidate @submit.prevent="handleLogin">
          <label class="field">
            <span class="field-label">账号</span>
            <n-input
              v-model:value="formData.username"
              placeholder="用户名或学号"
              :input-props="{ autocomplete: 'username', 'aria-label': '账号' }"
            />
          </label>

          <label class="field">
            <span class="field-label">密码</span>
            <n-input
              v-model:value="formData.password"
              type="password"
              placeholder="登录密码"
              show-password-on="click"
              :input-props="{ autocomplete: 'current-password', 'aria-label': '密码' }"
            />
          </label>

          <p v-if="errorMsg" class="error">
            <span class="error-bar"></span>{{ errorMsg }}
          </p>

          <div class="row">
            <n-checkbox v-model:checked="rememberMe" size="small">记住账号</n-checkbox>
            <button class="link" type="button" @click="showHelp = true">忘记密码</button>
          </div>

          <button class="submit" type="submit" :disabled="loading">
            {{ loading ? '正在验证' : '登录' }}
          </button>

          <p v-if="registerEnabled" class="alt">
            还没有账号？<button class="link" type="button" @click="openRegister">申请开通</button>
          </p>
          <p v-else class="alt muted">注册已关闭，账号由任课教师统一发放。</p>
        </form>
      </div>

      <footer class="foot">
        <span>本系统用于课堂教学，账号问题请联系任课教师</span>
        <span class="foot-meta">v1.0</span>
      </footer>
    </main>

    <!-- 学生注册 -->
    <n-modal
      v-model:show="showRegister"
      preset="card"
      title="申请开通账号"
      :style="modalStyle('520px')"
      :bordered="false"
    >
      <n-form
        ref="registerFormRef"
        class="reg-form"
        :model="registerData"
        :rules="registerRules"
        label-placement="left"
        label-width="70"
      >
        <n-form-item label="账号" path="username">
          <n-input v-model:value="registerData.username" placeholder="用于登录，建议填学号" />
        </n-form-item>
        <n-form-item label="密码" path="password">
          <n-input v-model:value="registerData.password" type="password" placeholder="至少 6 位" show-password-on="click" />
        </n-form-item>
        <n-form-item label="姓名" path="name">
          <n-input v-model:value="registerData.name" placeholder="真实姓名" />
        </n-form-item>
        <n-form-item label="学号" path="student_id">
          <n-input v-model:value="registerData.student_id" placeholder="学号" />
        </n-form-item>
        <n-form-item label="邮箱" path="email">
          <n-input v-model:value="registerData.email" placeholder="选填" />
        </n-form-item>
        <n-form-item label="班级" path="class_id">
          <n-select
            v-model:value="registerData.class_id"
            :options="classOptions"
            :loading="classLoading"
            placeholder="请选择班级"
            clearable
          />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end" class="mod-actions">
          <n-button class="btn-plain" @click="showRegister = false">取消</n-button>
          <n-button
            class="btn-ink"
            :color="inkBtn.bg"
            :text-color="inkBtn.ink"
            :loading="registerLoading"
            @click="handleRegister"
          >
            提交
          </n-button>
        </n-space>
      </template>
    </n-modal>

    <!-- 忘记密码 -->
    <n-modal v-model:show="showHelp" preset="card" title="忘记密码" :style="modalStyle('420px')" :bordered="false">
      <div class="help">
        <p>出于账号安全考虑，密码需由管理员或任课教师重置。</p>
        <p>请告知教师你的<strong>账号或学号</strong>，教师可在「用户管理」中重设密码。</p>
      </div>
      <template #footer>
        <n-space justify="end" class="mod-actions">
          <n-button class="btn-ink" :color="inkBtn.bg" :text-color="inkBtn.ink" @click="showHelp = false">
            知道了
          </n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import type { FormInst, FormRules } from 'naive-ui'
import { useUserStore } from '@/stores/user'
import { useThemeStore } from '@/stores/theme'
import { authApi } from '@/api'

const router = useRouter()
const message = useMessage()
const userStore = useUserStore()
const themeStore = useThemeStore()

const REMEMBER_KEY = 'remembered_username'

// 角色是「白底 + 墨线」：main.ts 里已把 ivory 色板覆写为纯白，
// 两种主题统一用 ivory（--bot-opacity 由 mono.css 按主题微调），五官始终用墨色（--aora-fg）
const bgBotColor = computed(() => 'ivory')

const registerFormRef = ref<FormInst | null>(null)
const loading = ref(false)
const registerLoading = ref(false)
const classLoading = ref(false)
const showRegister = ref(false)
const showHelp = ref(false)
const registerEnabled = ref(true)
const rememberMe = ref(false)
const errorMsg = ref('')
const classOptions = ref<{ label: string; value: number }[]>([])
const classesLoaded = ref(false)
const isMobile = ref(window.innerWidth <= 900)

const formData = ref({ username: '', password: '' })
const registerData = ref({
  username: '',
  password: '',
  name: '',
  student_id: '',
  email: '',
  class_id: null as number | null
})

const steps = [
  { num: '01', title: '阅读任务与验收标准', desc: '看清每一步要交付什么' },
  { num: '02', title: '动手编码，卡住时请求提示', desc: '三级递进，不会直接给答案' },
  { num: '03', title: '提交后获得评语与四维评分', desc: '正确性、规范性、完成度、创新性' },
  { num: '04', title: '过程性评价累计为最终成绩', desc: '课前、课中、课后全程记录' }
]

const registerRules: FormRules = {
  username: [
    { required: true, message: '请填写账号', trigger: 'blur' },
    { min: 3, message: '账号至少 3 个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请填写密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' }
  ],
  name: { required: true, message: '请填写姓名', trigger: 'blur' }
}

function handleResize() {
  isMobile.value = window.innerWidth <= 900
}

// 弹窗被 teleport 到 body，拿不到 .auth 上的 CSS 变量，颜色用计算属性传进去
const inkBtn = computed(() => (
  themeStore.isDark
    ? { bg: '#e9e9e6', ink: '#101012' }
    : { bg: '#16171a', ink: '#ffffff' }
))

function modalStyle(width: string) {
  return {
    width: isMobile.value ? '94vw' : width,
    maxWidth: '94vw',
    background: themeStore.isDark ? '#16161a' : '#ffffff',
    borderRadius: '6px',
    border: themeStore.isDark ? '1px solid rgba(255,255,255,0.12)' : '1px solid rgba(20,21,24,0.12)',
    boxShadow: 'none'
  }
}

async function handleLogin() {
  if (!formData.value.username.trim()) {
    errorMsg.value = '请填写账号'
    return
  }
  if (!formData.value.password) {
    errorMsg.value = '请填写密码'
    return
  }
  errorMsg.value = ''
  loading.value = true
  try {
    await userStore.login(formData.value.username.trim(), formData.value.password)
    if (rememberMe.value) {
      localStorage.setItem(REMEMBER_KEY, formData.value.username.trim())
    } else {
      localStorage.removeItem(REMEMBER_KEY)
    }
    router.replace(userStore.isTeacher ? '/admin' : '/')
  } catch (error: any) {
    errorMsg.value = error?.detail || error?.message || '登录失败，请检查账号与密码'
  } finally {
    loading.value = false
  }
}

function openRegister() {
  showRegister.value = true
  if (!classesLoaded.value) loadClasses()
}

async function handleRegister() {
  try {
    await registerFormRef.value?.validate()
  } catch {
    return
  }
  registerLoading.value = true
  try {
    await authApi.register(registerData.value)
    message.success('已提交，请使用新账号登录')
    showRegister.value = false
    formData.value.username = registerData.value.username
    formData.value.password = ''
  } catch (error: any) {
    message.error(error?.detail || '提交失败')
  } finally {
    registerLoading.value = false
  }
}

async function loadClasses() {
  classLoading.value = true
  try {
    const data = (await authApi.getClasses()) as any
    classOptions.value = (data || []).map((c: any) => ({ label: c.name, value: c.id }))
    classesLoaded.value = true
  } catch (error) {
    console.error('加载班级列表失败', error)
  } finally {
    classLoading.value = false
  }
}

async function loadSettings() {
  try {
    const data = (await authApi.getSettings()) as any
    registerEnabled.value = data?.student_register_enabled !== false
  } catch {
    registerEnabled.value = true
  }
}

onMounted(() => {
  window.addEventListener('resize', handleResize, { passive: true })
  const saved = localStorage.getItem(REMEMBER_KEY)
  if (saved) {
    formData.value.username = saved
    rememberMe.value = true
  }
  loadSettings()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
})
</script>

<style scoped>
/* ================= 基础 ================= */
/* 配色统一由 src/styles/mono.css 的 .mono-theme 提供，这里只管布局 */
.auth {
  display: flex;
  min-height: 100vh;
  background: var(--paper);
  color: var(--ink);
  transition: background-color 0.3s ease, color 0.3s ease;
}

/* 背景大角色：贴底、眼睛跟随指针；内容层 z-index 在其上
   亮色=白底黑线，暗色=深底浅线，颜色来自 --bot-* 变量 */
.bg-bot {
  position: absolute;
  right: -90px;
  bottom: -150px;
  z-index: 0;
  width: 520px;
  height: 520px;
  display: grid;
  place-items: center;
  /* 两层：贴着身体轮廓的细线 + 外圈柔光，让白底角色从纸面里“浮”出来 */
  background:
    radial-gradient(circle at 50% 50%, transparent 0 197px, var(--bot-ring) 198px, transparent 200px),
    var(--bot-plate);
  opacity: var(--bot-opacity);
  pointer-events: none;
  line-height: 0;
  /* 库里角色的身体取色板 ink（暖白/米白），这里用滤镜推成纯白：
     墨色五官（#2B2420）几乎不受影响，身体则收敛到接近 #fff */
  filter: saturate(0.3) brightness(1.05);
  /* 边缘淡出，避免与内容抢注意力；中间部分保持清晰 */
  -webkit-mask-image: radial-gradient(circle at 52% 48%, #000 42%, transparent 76%);
  mask-image: radial-gradient(circle at 52% 48%, #000 42%, transparent 76%);
  transition: opacity 0.3s ease, background 0.3s ease;
  /* 角色内部的线条/纸色，跟随主题 */
  --aora-fg: var(--bot-fg);
  --aora-paper: var(--bot-paper);
  --aora-bg-base: transparent;
}

@media (max-width: 900px) {
  .bg-bot {
    right: -130px;
    bottom: -170px;
    width: 460px;
    height: 460px;
    opacity: calc(var(--bot-opacity) * 0.8);
  }
}


/* ================= 左：墨色面板 ================= */
.pane-info {
  position: relative;
  z-index: 1;
  width: 44%;
  min-width: 420px;
  max-width: 620px;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 44px 56px 36px;
  background: #16171a;
  color: #f4f4f1;
}

.auth.dark .pane-info {
  background: #08080a;
  border-right: 1px solid rgba(255, 255, 255, 0.08);
}

.info-top {
  display: flex;
  align-items: center;
  gap: 10px;
  color: rgba(244, 244, 241, 0.9);
}

.brand-name {
  font-size: 13.5px;
  font-weight: 600;
  letter-spacing: 0.08em;
}

.info-body {
  padding: 8px 0;
}

.mascot {
  margin-bottom: 18px;
  line-height: 0;
}

.eyebrow {
  margin: 0 0 18px;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 10.5px;
  letter-spacing: 0.22em;
  color: rgba(244, 244, 241, 0.6);
}

.tagline {
  margin: 0 0 40px;
  font-size: clamp(26px, 2.4vw, 34px);
  font-weight: 600;
  line-height: 1.45;
  letter-spacing: -0.01em;
  color: #f4f4f1;
}

.steps {
  list-style: none;
  margin: 0;
  padding: 0;
  max-width: 420px;
}

.steps li {
  display: flex;
  gap: 14px;
  padding: 14px 0;
  border-top: 1px solid rgba(244, 244, 241, 0.14);
}

.steps li:last-child {
  border-bottom: 1px solid rgba(244, 244, 241, 0.14);
}

.idx {
  flex: 0 0 auto;
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
  font-size: 11px;
  line-height: 1.95;
  color: rgba(244, 244, 241, 0.55);
  font-variant-numeric: tabular-nums;
}

.steps strong {
  display: block;
  font-size: 13px;
  font-weight: 600;
  line-height: 1.7;
  color: rgba(244, 244, 241, 0.95);
}

.steps p {
  margin: 2px 0 0;
  font-size: 12px;
  line-height: 1.6;
  color: rgba(244, 244, 241, 0.66);
}

.info-foot {
  font-size: 11.5px;
  letter-spacing: 0.04em;
  color: rgba(244, 244, 241, 0.62);
}

/* ================= 右：表单区 ================= */
.pane-form {
  position: relative;
  z-index: 1;
  flex: 1;
  display: flex;
  flex-direction: column;
  justify-content: center;
  align-items: center;
  padding: 48px 40px 22px;
}

.theme {
  position: absolute;
  top: 26px;
  right: 32px;
  padding: 5px 10px;
  font-size: 12px;
  letter-spacing: 0.08em;
  color: var(--muted);
  background: transparent;
  border: 1px solid var(--hair);
  border-radius: 2px;
  cursor: pointer;
  transition: color 0.2s ease, border-color 0.2s ease;
}

.theme:hover {
  color: var(--ink);
  border-color: var(--ink);
}

.form-wrap {
  width: 100%;
  max-width: 344px;
}

.mobile-brand {
  display: none;
}

.intro {
  margin-bottom: 32px;
}

.intro h1 {
  margin: 0 0 8px;
  font-size: 27px;
  font-weight: 650;
  letter-spacing: -0.01em;
  line-height: 1.2;
}

.intro p {
  margin: 0;
  font-size: 13px;
  line-height: 1.7;
  color: var(--muted);
}

/* ---- 下划线输入框 ---- */
.field {
  position: relative;
  display: block;
  padding: 22px 0 7px;
  margin-bottom: 18px;
  border-bottom: 1px solid var(--hair);
  transition: border-color 0.2s ease;
}

.field:focus-within {
  border-bottom-color: var(--accent);
}

.field-label {
  position: absolute;
  top: 0;
  left: 0;
  font-size: 11px;
  letter-spacing: 0.14em;
  color: var(--faint);
  transition: color 0.2s ease;
}

.field:focus-within .field-label {
  color: var(--accent);
}

.form :deep(.n-input) {
  --n-height: 32px;
  --n-color: transparent !important;
  --n-color-focus: transparent !important;
  --n-text-color: var(--ink) !important;
  --n-placeholder-color: var(--faint) !important;
  --n-caret-color: var(--accent) !important;
  --n-box-shadow-focus: none !important;
  background: transparent !important;
}

.form :deep(.n-input .n-input__border),
.form :deep(.n-input .n-input__state-border) {
  display: none !important;
}

.form :deep(.n-input .n-input-wrapper) {
  padding-left: 0;
  padding-right: 0;
}

.form :deep(.n-input input) {
  font-size: 14.5px;
}

.form :deep(.n-input .n-input__suffix) {
  color: var(--faint);
}

/* 错误 */
.error {
  display: flex;
  gap: 9px;
  margin: 0 0 16px;
  font-size: 12px;
  line-height: 1.6;
  color: #b4342c;
}

.auth.dark .error {
  color: #e2827a;
}

.error-bar {
  flex: 0 0 2px;
  background: currentColor;
}

.row {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 22px;
}

.form :deep(.n-checkbox__label) {
  font-size: 12px;
  color: var(--muted) !important;
}

.link {
  padding: 0;
  font-size: 12px;
  color: var(--muted);
  background: none;
  border: none;
  border-bottom: 1px solid transparent;
  cursor: pointer;
  transition: color 0.2s ease, border-color 0.2s ease;
}

.link:hover {
  color: var(--ink);
  border-bottom-color: var(--ink);
}

/* 主按钮 */
.submit {
  width: 100%;
  height: 44px;
  font-size: 13.5px;
  font-weight: 600;
  letter-spacing: 0.18em;
  color: var(--btn-ink);
  background: var(--btn-bg);
  border: 1px solid var(--btn-bg);
  border-radius: 2px;
  cursor: pointer;
  transition: opacity 0.2s ease;
}

.submit:hover:not(:disabled) {
  opacity: 0.92;
}

.submit:disabled {
  cursor: default;
  opacity: 0.6;
}

.alt {
  margin: 18px 0 0;
  font-size: 12px;
  color: var(--muted);
}

.alt.muted {
  color: var(--faint);
}

/* 底部 */
.foot {
  position: absolute;
  left: 40px;
  right: 40px;
  bottom: 22px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding-top: 14px;
  border-top: 1px solid var(--hair);
  font-size: 11px;
  color: var(--faint);
}

.foot-meta {
  font-family: ui-monospace, SFMono-Regular, Menlo, monospace;
}

.help p {
  margin: 0 0 12px;
  font-size: 13.5px;
  line-height: 1.8;
  color: var(--muted);
}

.help p:last-child {
  margin-bottom: 0;
}

/* 弹窗内元素：去掉圆角与蓝色，与整体风格一致 */
.reg-form :deep(.n-input),
.reg-form :deep(.n-base-selection),
.mod-actions :deep(.n-button) {
  --n-border-radius: 2px !important;
  border-radius: 2px !important;
}

.reg-form :deep(.n-input),
.reg-form :deep(.n-base-selection) {
  --n-border-focus: #1c6b52 !important;
  --n-border-hover: #1c6b52 !important;
  --n-box-shadow-focus: none !important;
}

.reg-form :deep(.n-form-item-label) {
  font-size: 12.5px;
}

/* ================= 响应式 ================= */
@media (max-width: 1180px) {
  .pane-info {
    width: 42%;
    min-width: 360px;
    padding: 40px 40px 32px;
  }

  .pane-form {
    padding: 48px 32px 22px;
  }
}

@media (max-width: 900px) {
  .auth {
    display: block;
    min-height: 100vh;
  }

  .pane-info {
    display: none;
  }

  .pane-form {
    min-height: 100vh;
    justify-content: flex-start;
    padding: 72px 24px 24px;
  }

  .form-wrap {
    max-width: 400px;
    margin: 0 auto;
  }

  .mobile-brand {
    display: flex;
    align-items: center;
    gap: 9px;
    margin-bottom: 34px;
    font-size: 13px;
    font-weight: 600;
    letter-spacing: 0.08em;
    color: var(--ink);
  }

  .theme {
    top: 20px;
    right: 20px;
  }

  /* 页脚沉底，避免内容上方挤、下方空 */
  .foot {
    position: static;
    margin: auto auto 0;
    width: 100%;
    max-width: 400px;
  }

  .foot span:first-child {
    font-size: 10.5px;
  }
}

@media (max-height: 700px) and (min-width: 901px) {
  .tagline {
    margin-bottom: 26px;
  }

  .steps li {
    padding: 10px 0;
  }
}

@media (prefers-reduced-motion: reduce) {
  .auth,
  .field,
  .submit,
  .link,
  .theme {
    transition: none !important;
  }
}
</style>
