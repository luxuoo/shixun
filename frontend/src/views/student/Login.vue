<template>
  <div class="cc-auth" :class="{ dark: themeStore.isDark }">
    <!-- 右下角保留的大表情头 -->
    <div class="bg-bot" aria-hidden="true">
      <AoraBot
        shape="circle"
        :color="bgBotColor"
        state="reading"
        face="eyes"
        :sizePx="isMobile ? 280 : 400"
        followPointer
        seed="login-bg-bot"
      />
    </div>

    <!-- 左：primary 渐变 + 四个卡通角色 -->
    <aside class="cc-left">
      <div class="cc-left-top">
        <div class="cc-brand-box">
          <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z"/><path d="M20 3v4"/><path d="M22 5h-4"/></svg>
        </div>
        <span>实训教学平台</span>
      </div>

      <div class="cc-left-mid">
        <div class="cc-chars" aria-hidden="true">
          <div ref="purpleRef" class="cc-char" :style="purpleBody">
            <div class="cc-eyes cc-eyes-slow" :style="purpleEyes">
              <TrackingEye :size="18" :pupil-size="7" :max-distance="5" :blinking="isPurpleBlinking" :force-look-x="purpleForce?.x" :force-look-y="purpleForce?.y" :mouse-x="mouseX" :mouse-y="mouseY" />
              <TrackingEye :size="18" :pupil-size="7" :max-distance="5" :blinking="isPurpleBlinking" :force-look-x="purpleForce?.x" :force-look-y="purpleForce?.y" :mouse-x="mouseX" :mouse-y="mouseY" />
            </div>
          </div>
          <div ref="blackRef" class="cc-char" :style="blackBody">
            <div class="cc-eyes cc-eyes-slow" :style="blackEyes">
              <TrackingEye :size="16" :pupil-size="6" :max-distance="4" :blinking="isBlackBlinking" :force-look-x="blackForce?.x" :force-look-y="blackForce?.y" :mouse-x="mouseX" :mouse-y="mouseY" />
              <TrackingEye :size="16" :pupil-size="6" :max-distance="4" :blinking="isBlackBlinking" :force-look-x="blackForce?.x" :force-look-y="blackForce?.y" :mouse-x="mouseX" :mouse-y="mouseY" />
            </div>
          </div>
          <div ref="orangeRef" class="cc-char" :style="orangeBody">
            <div class="cc-eyes cc-eyes-fast" :style="orangeEyes">
              <TrackingEye :show-white="false" :pupil-size="12" :max-distance="5" :force-look-x="orangeForce?.x" :force-look-y="orangeForce?.y" :mouse-x="mouseX" :mouse-y="mouseY" />
              <TrackingEye :show-white="false" :pupil-size="12" :max-distance="5" :force-look-x="orangeForce?.x" :force-look-y="orangeForce?.y" :mouse-x="mouseX" :mouse-y="mouseY" />
            </div>
          </div>
          <div ref="yellowRef" class="cc-char" :style="yellowBody">
            <div class="cc-eyes cc-eyes-fast" :style="yellowEyes">
              <TrackingEye :show-white="false" :pupil-size="12" :max-distance="5" :force-look-x="yellowForce?.x" :force-look-y="yellowForce?.y" :mouse-x="mouseX" :mouse-y="mouseY" />
              <TrackingEye :show-white="false" :pupil-size="12" :max-distance="5" :force-look-x="yellowForce?.x" :force-look-y="yellowForce?.y" :mouse-x="mouseX" :mouse-y="mouseY" />
            </div>
            <div class="cc-mouth" :style="yellowMouth"></div>
          </div>
        </div>
      </div>

      <div class="cc-left-foot">
        <span>隐私政策</span>
        <span>服务条款</span>
        <span>联系任课教师</span>
      </div>

      <div class="cc-grid" aria-hidden="true"></div>
      <div class="cc-blob cc-blob-a" aria-hidden="true"></div>
      <div class="cc-blob cc-blob-b" aria-hidden="true"></div>
    </aside>

    <!-- 右：登录表单 -->
    <main class="cc-right">
      <button class="cc-theme" type="button" @click="themeStore.toggle()">
        <span class="cc-theme-ico">{{ themeStore.isDark ? '☀' : '☾' }}</span>
        {{ themeStore.isDark ? '日间' : '夜间' }}
      </button>

      <div class="cc-form-wrap">
        <div class="cc-mobile-brand">
          <div class="cc-brand-box mobile">
            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.937 15.5A2 2 0 0 0 8.5 14.063l-6.135-1.582a.5.5 0 0 1 0-.962L8.5 9.936A2 2 0 0 0 9.937 8.5l1.582-6.135a.5.5 0 0 1 .963 0L14.063 8.5A2 2 0 0 0 15.5 9.937l6.135 1.581a.5.5 0 0 1 0 .964L15.5 14.063a2 2 0 0 0-1.437 1.437l-1.582 6.135a.5.5 0 0 1-.963 0z"/><path d="M20 3v4"/><path d="M22 5h-4"/></svg>
          </div>
          <span>实训教学平台</span>
        </div>

        <div class="cc-head">
          <h1>欢迎回来！</h1>
          <p>请输入你的账号信息</p>
        </div>

        <form class="cc-form" novalidate @submit.prevent="handleLogin">
          <div class="cc-field">
            <label for="cc-user">账号</label>
            <input
              id="cc-user"
              v-model="formData.username"
              type="text"
              placeholder="用户名或学号"
              autocomplete="username"
              @focus="isTyping = true"
              @blur="isTyping = false"
            />
          </div>

          <div class="cc-field">
            <label for="cc-pw">密码</label>
            <div class="cc-pw-wrap">
              <input
                id="cc-pw"
                v-model="formData.password"
                :type="showPassword ? 'text' : 'password'"
                placeholder="••••••••"
                autocomplete="current-password"
                @focus="isTyping = true"
                @blur="isTyping = false"
              />
              <button
                type="button"
                class="cc-eye"
                :aria-label="showPassword ? '隐藏密码' : '显示密码'"
                @click="showPassword = !showPassword"
              >
                <svg v-if="showPassword" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M9.88 9.88a3 3 0 1 0 4.24 4.24"/><path d="M10.73 5.08A10.43 10.43 0 0 1 12 5c7 0 10 7 10 7a13.16 13.16 0 0 1-1.67 2.68"/><path d="M6.61 6.61A13.526 13.526 0 0 0 2 12s3 7 10 7a9.74 9.74 0 0 0 5.39-1.61"/><line x1="2" x2="22" y1="2" y2="22"/></svg>
                <svg v-else viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round"><path d="M2 12s3-7 10-7 10 7 10 7-3 7-10 7-10-7-10-7Z"/><circle cx="12" cy="12" r="3"/></svg>
              </button>
            </div>
          </div>

          <div class="cc-row">
            <label class="cc-remember">
              <input v-model="rememberMe" type="checkbox" />
              <span class="cc-box" aria-hidden="true">
                <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"><path d="M20 6 9 17l-5-5"/></svg>
              </span>
              <span class="cc-remember-txt">30 天内记住我</span>
            </label>
            <button class="cc-link" type="button" @click="showHelp = true">忘记密码？</button>
          </div>

          <p v-if="errorMsg" class="cc-error">{{ errorMsg }}</p>

          <button class="cc-submit" type="submit" :disabled="loading">
            {{ loading ? '登录中…' : '登录' }}
          </button>
        </form>

        <p class="cc-alt">
          还没有账号？<button class="cc-alt-link" type="button" @click="openRegister">申请开通</button>
        </p>
      </div>
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
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import type { FormInst, FormRules } from 'naive-ui'
import { useUserStore } from '@/stores/user'
import { useThemeStore } from '@/stores/theme'
import { authApi } from '@/api'
import TrackingEye from '@/components/TrackingEye.vue'

const router = useRouter()
const message = useMessage()
const userStore = useUserStore()
const themeStore = useThemeStore()

const REMEMBER_KEY = 'remembered_username'
const REMEMBER_TS_KEY = 'remembered_username_expires'
const REMEMBER_DAYS = 30

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
const showPassword = ref(false)
const isTyping = ref(false)
const classOptions = ref<{ label: string; value: number }[]>([])
const classesLoaded = ref(false)
const isMobile = ref(window.innerWidth <= 1024)

const formData = ref({ username: '', password: '' })
const registerData = ref({
  username: '',
  password: '',
  name: '',
  student_id: '',
  email: '',
  class_id: null as number | null
})

/* ===== 角色动画（照搬源码行为） ===== */
const mouseX = ref(0)
const mouseY = ref(0)
const isPurpleBlinking = ref(false)
const isBlackBlinking = ref(false)
const lookEach = ref(false)
const peek = ref(false)
const purpleRef = ref<HTMLElement | null>(null)
const blackRef = ref<HTMLElement | null>(null)
const orangeRef = ref<HTMLElement | null>(null)
const yellowRef = ref<HTMLElement | null>(null)

const pwShown = computed(() => formData.value.password.length > 0 && showPassword.value)
const leaning = computed(() => isTyping.value || (formData.value.password.length > 0 && !showPassword.value))

const clamp = (v: number, lo: number, hi: number) => Math.max(lo, Math.min(hi, v))
function posOf(el: HTMLElement | null) {
  if (!el) return { faceX: 0, faceY: 0, bodySkew: 0 }
  const r = el.getBoundingClientRect()
  const cx = r.left + r.width / 2
  const cy = r.top + r.height / 3
  const dx = mouseX.value - cx
  const dy = mouseY.value - cy
  return { faceX: clamp(dx / 20, -15, 15), faceY: clamp(dy / 30, -10, 10), bodySkew: clamp(-dx / 120, -6, 6) }
}
const purplePos = computed(() => posOf(purpleRef.value))
const blackPos = computed(() => posOf(blackRef.value))
const orangePos = computed(() => posOf(orangeRef.value))
const yellowPos = computed(() => posOf(yellowRef.value))

const purpleBody = computed(() => ({
  left: '70px', width: '180px', height: leaning.value ? '440px' : '400px',
  backgroundColor: '#6C3FF5', borderRadius: '10px 10px 0 0', zIndex: 1,
  transform: pwShown.value ? 'skewX(0deg)' : leaning.value ? `skewX(${purplePos.value.bodySkew - 12}deg) translateX(40px)` : `skewX(${purplePos.value.bodySkew}deg)`,
}))
const purpleEyes = computed(() => ({
  left: pwShown.value ? '20px' : lookEach.value ? '55px' : `${45 + purplePos.value.faceX}px`,
  top: pwShown.value ? '35px' : lookEach.value ? '65px' : `${40 + purplePos.value.faceY}px`,
}))
const purpleForce = computed(() => pwShown.value ? (peek.value ? { x: 4, y: 5 } : { x: -4, y: -4 }) : lookEach.value ? { x: 3, y: 4 } : undefined)

const blackBody = computed(() => ({
  left: '240px', width: '120px', height: '310px',
  backgroundColor: '#2D2D2D', borderRadius: '8px 8px 0 0', zIndex: 2,
  transform: pwShown.value ? 'skewX(0deg)' : lookEach.value ? `skewX(${blackPos.value.bodySkew * 1.5 + 10}deg) translateX(20px)` : leaning.value ? `skewX(${blackPos.value.bodySkew * 1.5}deg)` : `skewX(${blackPos.value.bodySkew}deg)`,
}))
const blackEyes = computed(() => ({
  left: pwShown.value ? '10px' : lookEach.value ? '32px' : `${26 + blackPos.value.faceX}px`,
  top: pwShown.value ? '28px' : lookEach.value ? '12px' : `${32 + blackPos.value.faceY}px`,
}))
const blackForce = computed(() => pwShown.value ? { x: -4, y: -4 } : lookEach.value ? { x: 0, y: -4 } : undefined)

const orangeBody = computed(() => ({
  left: '0px', width: '240px', height: '200px', zIndex: 3,
  backgroundColor: '#FF9B6B', borderRadius: '120px 120px 0 0',
  transform: pwShown.value ? 'skewX(0deg)' : `skewX(${orangePos.value.bodySkew}deg)`,
}))
const orangeEyes = computed(() => ({
  left: pwShown.value ? '50px' : `${82 + orangePos.value.faceX}px`,
  top: pwShown.value ? '85px' : `${90 + orangePos.value.faceY}px`,
}))
const orangeForce = computed(() => pwShown.value ? { x: -5, y: -4 } : undefined)

const yellowBody = computed(() => ({
  left: '310px', width: '140px', height: '230px',
  backgroundColor: '#E8D754', borderRadius: '70px 70px 0 0', zIndex: 4,
  transform: pwShown.value ? 'skewX(0deg)' : `skewX(${yellowPos.value.bodySkew}deg)`,
}))
const yellowEyes = computed(() => ({
  left: pwShown.value ? '20px' : `${52 + yellowPos.value.faceX}px`,
  top: pwShown.value ? '35px' : `${40 + yellowPos.value.faceY}px`,
}))
const yellowForce = computed(() => pwShown.value ? { x: -5, y: -4 } : undefined)
const yellowMouth = computed(() => ({
  left: pwShown.value ? '10px' : `${40 + yellowPos.value.faceX}px`,
  top: pwShown.value ? '88px' : `${88 + yellowPos.value.faceY}px`,
}))

const timers: ReturnType<typeof setTimeout>[] = []
function scheduleBlink(set: (v: boolean) => void) {
  const t = setTimeout(() => {
    set(true)
    timers.push(setTimeout(() => { set(false); scheduleBlink(set) }, 150))
  }, 3000 + Math.random() * 4000)
  timers.push(t)
}
watch(isTyping, (v) => {
  if (v) {
    lookEach.value = true
    timers.push(setTimeout(() => { lookEach.value = false }, 800))
  } else {
    lookEach.value = false
  }
})
watch([() => formData.value.password, showPassword], () => {
  if (pwShown.value) {
    timers.push(setTimeout(() => {
      peek.value = true
      timers.push(setTimeout(() => { peek.value = false }, 800))
    }, 2000 + Math.random() * 3000))
  } else {
    peek.value = false
  }
})

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
  isMobile.value = window.innerWidth <= 1024
}
function handleMouseMove(e: MouseEvent) {
  mouseX.value = e.clientX
  mouseY.value = e.clientY
}

const inkBtn = computed(() => (
  themeStore.isDark
    ? { bg: '#fafafa', ink: '#18181b' }
    : { bg: '#18181b', ink: '#fafafa' }
))

function modalStyle(width: string) {
  return {
    width: isMobile.value ? '94vw' : width,
    maxWidth: '94vw',
    background: themeStore.isDark ? '#09090b' : '#ffffff',
    borderRadius: '8px',
    border: themeStore.isDark ? '1px solid #27272a' : '1px solid #e4e4e7',
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
      localStorage.setItem(REMEMBER_TS_KEY, String(Date.now() + REMEMBER_DAYS * 86400_000))
    } else {
      localStorage.removeItem(REMEMBER_KEY)
      localStorage.removeItem(REMEMBER_TS_KEY)
    }
    router.replace(userStore.isTeacher ? '/admin' : '/')
  } catch (error: any) {
    errorMsg.value = error?.detail || error?.message || '账号或密码错误，请重试'
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
  window.addEventListener('mousemove', handleMouseMove, { passive: true })
  scheduleBlink((v) => { isPurpleBlinking.value = v })
  scheduleBlink((v) => { isBlackBlinking.value = v })
  const saved = localStorage.getItem(REMEMBER_KEY)
  const expires = Number(localStorage.getItem(REMEMBER_TS_KEY) || 0)
  if (saved && expires > Date.now()) {
    formData.value.username = saved
    rememberMe.value = true
  } else {
    localStorage.removeItem(REMEMBER_KEY)
    localStorage.removeItem(REMEMBER_TS_KEY)
  }
  loadSettings()
})

onBeforeUnmount(() => {
  window.removeEventListener('resize', handleResize)
  window.removeEventListener('mousemove', handleMouseMove)
  timers.forEach(clearTimeout)
})
</script>

<style scoped>
/* ===== shadcn 中性色板：白天 primary=近黑 / 黑夜 primary=近白，仅灰白转换 ===== */
.cc-auth {
  --cc-bg: #ffffff;
  --cc-fg: #09090b;
  --cc-muted: #71717a;
  --cc-border: #e4e4e7;
  --cc-input: #e4e4e7;
  --cc-primary: #18181b;
  --cc-primary-fg: #fafafa;
  --cc-ring: #18181b;
  --cc-brandbox: rgba(250, 250, 250, 0.1);
  --cc-left-a: rgba(24, 24, 27, 0.9);
  --cc-left-b: #18181b;
  --cc-left-c: rgba(24, 24, 27, 0.8);
  --cc-left-fg: #fafafa;
  --cc-left-muted: rgba(250, 250, 250, 0.75);
  --cc-grid: rgba(255, 255, 255, 0.05);
  --cc-blob: rgba(250, 250, 250, 0.1);
  --cc-blob2: rgba(250, 250, 250, 0.05);
  --cc-error: #dc2626;
  --cc-error-bg: rgba(127, 29, 29, 0.08);
  --cc-error-border: rgba(127, 29, 29, 0.2);

  position: relative;
  display: grid;
  grid-template-columns: 1fr 1fr;
  min-height: 100vh;
  overflow: hidden;
  background: var(--cc-bg);
  color: var(--cc-fg);
  font-family: Inter, -apple-system, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif;
  transition: background-color 0.3s ease, color 0.3s ease;
}

.cc-auth.dark {
  --cc-bg: #09090b;
  --cc-fg: #fafafa;
  --cc-muted: #a1a1aa;
  --cc-border: #27272a;
  --cc-input: #27272a;
  --cc-primary: #fafafa;
  --cc-primary-fg: #18181b;
  --cc-ring: #fafafa;
  --cc-brandbox: rgba(24, 24, 27, 0.1);
  --cc-left-a: rgba(250, 250, 250, 0.9);
  --cc-left-b: #fafafa;
  --cc-left-c: rgba(250, 250, 250, 0.8);
  --cc-left-fg: #18181b;
  --cc-left-muted: rgba(24, 24, 27, 0.75);
  --cc-grid: rgba(255, 255, 255, 0.05);
  --cc-blob: rgba(24, 24, 27, 0.1);
  --cc-blob2: rgba(24, 24, 27, 0.05);
  --cc-error: #f87171;
  --cc-error-bg: rgba(127, 29, 29, 0.2);
  --cc-error-border: rgba(127, 29, 29, 0.3);
}

/* ===== 左面板 ===== */
.cc-left {
  position: relative;
  display: flex;
  flex-direction: column;
  justify-content: space-between;
  padding: 48px;
  background: linear-gradient(to bottom right, var(--cc-left-a), var(--cc-left-b), var(--cc-left-c));
  color: var(--cc-left-fg);
  overflow: hidden;
}
.cc-grid { position: absolute; inset: 0; background-image: linear-gradient(var(--cc-grid) 1px, transparent 1px), linear-gradient(90deg, var(--cc-grid) 1px, transparent 1px); background-size: 20px 20px; pointer-events: none; }
.cc-blob { position: absolute; border-radius: 50%; filter: blur(64px); pointer-events: none; }
.cc-blob-a { top: 25%; right: 25%; width: 256px; height: 256px; background: var(--cc-blob); }
.cc-blob-b { bottom: 25%; left: 25%; width: 384px; height: 384px; background: var(--cc-blob2); }

.cc-left-top { position: relative; z-index: 2; display: flex; align-items: center; gap: 8px; font-size: 18px; font-weight: 600; }
.cc-brand-box { width: 32px; height: 32px; border-radius: 8px; background: var(--cc-brandbox); backdrop-filter: blur(4px); display: flex; align-items: center; justify-content: center; }
.cc-brand-box svg { width: 16px; height: 16px; }
.cc-brand-box.mobile { background: color-mix(in srgb, var(--cc-primary) 10%, transparent); color: var(--cc-primary); }

.cc-left-mid { position: relative; z-index: 2; display: flex; align-items: flex-end; justify-content: center; height: 500px; }
.cc-left-foot { position: relative; z-index: 2; display: flex; align-items: center; gap: 32px; font-size: 14px; color: var(--cc-left-muted); }
.cc-left-foot span { transition: color 0.2s; cursor: default; }
.cc-left-foot span:hover { color: var(--cc-left-fg); }

/* ===== 四个角色 ===== */
.cc-chars { position: relative; width: 550px; height: 400px; }
.cc-char { position: absolute; bottom: 0; transition: all 0.7s ease-in-out; transform-origin: bottom center; }
.cc-eyes { position: absolute; display: flex; }
.cc-eyes-slow { gap: 32px; transition: all 0.7s ease-in-out; }
.cc-eyes-fast { gap: 32px; transition: all 0.2s ease-out; }
.cc-mouth { position: absolute; width: 80px; height: 4px; background: #2D2D2D; border-radius: 9999px; transition: all 0.2s ease-out; }

/* ===== 右面板 ===== */
.cc-right { position: relative; z-index: 1; display: flex; align-items: center; justify-content: center; padding: 32px; }
.cc-theme { position: absolute; top: 20px; right: 20px; z-index: 3; display: inline-flex; align-items: center; gap: 6px; padding: 6px 12px; font-size: 12px; color: var(--cc-muted); background: transparent; border: 1px solid var(--cc-border); border-radius: 8px; cursor: pointer; transition: color 0.2s, border-color 0.2s; }
.cc-theme:hover { color: var(--cc-fg); border-color: var(--cc-muted); }
.cc-theme-ico { display: inline-block; transition: transform 0.4s cubic-bezier(0.22, 1, 0.36, 1); }
.cc-theme:hover .cc-theme-ico { transform: rotate(40deg) scale(1.15); }

.cc-form-wrap { position: relative; z-index: 2; width: 100%; max-width: 420px; }
.cc-mobile-brand { display: none; }
.cc-head { text-align: center; margin-bottom: 40px; }
.cc-head h1 { margin: 0 0 8px; font-size: 30px; font-weight: 700; letter-spacing: -0.02em; }
.cc-head p { margin: 0; font-size: 14px; color: var(--cc-muted); }

.cc-form { display: flex; flex-direction: column; gap: 20px; }
.cc-field { display: flex; flex-direction: column; gap: 8px; }
.cc-field label { font-size: 14px; font-weight: 500; }
.cc-field input {
  height: 48px; width: 100%; padding: 0 12px; font-size: 14px;
  color: var(--cc-fg); background: var(--cc-bg);
  border: 1px solid var(--cc-input); border-radius: 6px; outline: none;
  transition: border-color 0.2s, box-shadow 0.2s;
}
.cc-field input::placeholder { color: var(--cc-muted); }
.cc-field input:focus { border-color: var(--cc-primary); box-shadow: 0 0 0 2px var(--cc-bg), 0 0 0 4px var(--cc-ring); }
.cc-pw-wrap { position: relative; }
.cc-pw-wrap input { padding-right: 40px; }
.cc-eye { position: absolute; right: 12px; top: 50%; transform: translateY(-50%); display: inline-flex; padding: 0; color: var(--cc-muted); background: none; border: none; cursor: pointer; transition: color 0.2s; }
.cc-eye:hover { color: var(--cc-fg); }
.cc-eye svg { width: 20px; height: 20px; }

.cc-row { display: flex; align-items: center; justify-content: space-between; }
.cc-remember { display: inline-flex; align-items: center; gap: 8px; font-size: 14px; cursor: pointer; position: relative; }
.cc-remember input { position: absolute; opacity: 0; width: 16px; height: 16px; margin: 0; cursor: pointer; }
.cc-box { width: 16px; height: 16px; border: 1px solid var(--cc-primary); border-radius: 4px; display: inline-flex; align-items: center; justify-content: center; color: var(--cc-primary-fg); background: transparent; transition: background 0.15s; flex: 0 0 auto; }
.cc-box svg { width: 12px; height: 12px; opacity: 0; }
.cc-remember input:checked + .cc-box { background: var(--cc-primary); }
.cc-remember input:checked + .cc-box svg { opacity: 1; }
.cc-remember input:focus-visible + .cc-box { box-shadow: 0 0 0 2px var(--cc-bg), 0 0 0 4px var(--cc-ring); }
.cc-remember-txt { font-weight: 400; }
.cc-link { padding: 0; font-size: 14px; font-weight: 500; color: var(--cc-primary); background: none; border: none; cursor: pointer; }
.cc-link:hover { text-decoration: underline; }

.cc-error { margin: 0; padding: 12px; font-size: 14px; color: var(--cc-error); background: var(--cc-error-bg); border: 1px solid var(--cc-error-border); border-radius: 8px; }

.cc-submit {
  height: 48px; width: 100%; font-size: 16px; font-weight: 500;
  color: var(--cc-primary-fg); background: var(--cc-primary);
  border: none; border-radius: 6px; cursor: pointer; transition: opacity 0.2s;
}
.cc-submit:hover:not(:disabled) { opacity: 0.9; }
.cc-submit:disabled { opacity: 0.5; cursor: default; }

.cc-alt { margin: 32px 0 0; text-align: center; font-size: 14px; color: var(--cc-muted); }
.cc-alt-link { padding: 0; font-size: 14px; font-weight: 500; color: var(--cc-fg); background: none; border: none; cursor: pointer; }
.cc-alt-link:hover { text-decoration: underline; }

/* ===== 右下角大表情头（保留） ===== */
.bg-bot {
  position: absolute; right: -90px; bottom: -150px; z-index: 0;
  width: 520px; height: 520px; display: grid; place-items: center;
  opacity: 0.5; pointer-events: none; line-height: 0;
  filter: saturate(0.3) brightness(1.05);
  -webkit-mask-image: radial-gradient(circle at 52% 48%, #000 42%, transparent 76%);
  mask-image: radial-gradient(circle at 52% 48%, #000 42%, transparent 76%);
  --aora-fg: #16171a; --aora-paper: #ffffff; --aora-bg-base: transparent;
}

.reg-form :deep(.n-input), .reg-form :deep(.n-base-selection), .mod-actions :deep(.n-button) { --n-border-radius: 6px !important; border-radius: 6px !important; }
.reg-form :deep(.n-input), .reg-form :deep(.n-base-selection) { --n-border-focus: var(--cc-primary) !important; --n-border-hover: var(--cc-primary) !important; --n-box-shadow-focus: none !important; }
.reg-form :deep(.n-form-item-label) { font-size: 12.5px; }
.help p { margin: 0 0 12px; font-size: 13.5px; line-height: 1.8; color: var(--cc-muted); }
.help p:last-child { margin-bottom: 0; }

@media (max-width: 1280px) { .cc-chars { transform: scale(0.75); transform-origin: bottom center; } }
@media (max-width: 1024px) {
  .cc-auth { grid-template-columns: 1fr; }
  .cc-left { display: none; }
  .cc-right { min-height: 100vh; padding: 72px 24px 24px; }
  .cc-mobile-brand { display: flex; align-items: center; justify-content: center; gap: 8px; margin-bottom: 48px; font-size: 18px; font-weight: 600; }
  .bg-bot { right: -170px; bottom: -180px; width: 320px; height: 320px; opacity: 0.35;
    -webkit-mask-image: radial-gradient(circle at 50% 50%, #000 40%, transparent 78%);
    mask-image: radial-gradient(circle at 50% 50%, #000 40%, transparent 78%); }
}
@media (prefers-reduced-motion: reduce) {
  .cc-auth, .cc-auth *, .cc-auth *::before, .cc-auth *::after { animation: none !important; transition: none !important; }
}
</style>