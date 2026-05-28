<template>
  <div class="login-container">
    <div class="login-background">
      <div class="login-card">
        <div class="login-header">
          <n-icon size="48" color="#2080f0">
            <svg viewBox="0 0 24 24">
              <path fill="currentColor" d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
            </svg>
          </n-icon>
          <h1>AI 编程实训辅助教学系统</h1>
          <p>通过 AI 引导，掌握编程技能</p>
        </div>

        <n-form
          ref="formRef"
          :model="formData"
          :rules="rules"
          label-placement="left"
          label-width="80"
        >
          <n-form-item label="用户名" path="username">
            <n-input
              v-model:value="formData.username"
              placeholder="请输入用户名"
              size="large"
            >
              <template #prefix>
                <n-icon><svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg></n-icon>
              </template>
            </n-input>
          </n-form-item>

          <n-form-item label="密码" path="password">
            <n-input
              v-model:value="formData.password"
              type="password"
              placeholder="请输入密码"
              size="large"
              show-password-on="click"
              @keyup.enter="handleLogin"
            >
              <template #prefix>
                <n-icon><svg viewBox="0 0 24 24"><path fill="currentColor" d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z"/></svg></n-icon>
              </template>
            </n-input>
          </n-form-item>

          <n-form-item>
            <n-button
              type="primary"
              size="large"
              block
              :loading="loading"
              @click="handleLogin"
            >
              登录
            </n-button>
          </n-form-item>
        </n-form>

        <div class="login-footer" v-if="registerEnabled">
          <n-space justify="center" align="center">
            <n-button text type="primary" @click="showRegister = true">
              学生注册
            </n-button>
          </n-space>
        </div>
      </div>
    </div>

    <!-- 注册弹窗 -->
    <n-modal v-model:show="showRegister" preset="card" title="学生注册" style="width: 500px">
      <n-form
        ref="registerFormRef"
        :model="registerData"
        :rules="registerRules"
        label-placement="left"
        label-width="80"
      >
        <n-form-item label="用户名" path="username">
          <n-input v-model:value="registerData.username" placeholder="请输入用户名" />
        </n-form-item>
        <n-form-item label="密码" path="password">
          <n-input v-model:value="registerData.password" type="password" placeholder="请输入密码" />
        </n-form-item>
        <n-form-item label="姓名" path="name">
          <n-input v-model:value="registerData.name" placeholder="请输入真实姓名" />
        </n-form-item>
        <n-form-item label="学号" path="student_id">
          <n-input v-model:value="registerData.student_id" placeholder="请输入学号" />
        </n-form-item>
        <n-form-item label="邮箱" path="email">
          <n-input v-model:value="registerData.email" placeholder="请输入邮箱" />
        </n-form-item>
        <n-form-item label="班级" path="class_id">
          <n-select
            v-model:value="registerData.class_id"
            :options="classOptions"
            placeholder="请选择班级"
          />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showRegister = false">取消</n-button>
          <n-button type="primary" :loading="registerLoading" @click="handleRegister">
            注册
          </n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import type { FormInst, FormRules } from 'naive-ui'
import { useUserStore } from '@/stores/user'
import { authApi } from '@/api'

const router = useRouter()
const message = useMessage()
const userStore = useUserStore()

const formRef = ref<FormInst | null>(null)
const registerFormRef = ref<FormInst | null>(null)
const loading = ref(false)
const registerLoading = ref(false)
const showRegister = ref(false)
const registerEnabled = ref(true)
const classOptions = ref<{ label: string; value: number }[]>([])

const formData = ref({
  username: '',
  password: ''
})

const registerData = ref({
  username: '',
  password: '',
  name: '',
  student_id: '',
  email: '',
  class_id: null as number | null
})

const rules: FormRules = {
  username: { required: true, message: '请输入用户名', trigger: 'blur' },
  password: { required: true, message: '请输入密码', trigger: 'blur' }
}

const registerRules: FormRules = {
  username: { required: true, message: '请输入用户名', trigger: 'blur' },
  password: { required: true, message: '请输入密码', trigger: 'blur' },
  name: { required: true, message: '请输入姓名', trigger: 'blur' }
}

async function handleLogin() {
  try {
    await formRef.value?.validate()
    loading.value = true
    await userStore.login(formData.value.username, formData.value.password)
    message.success('登录成功')
    router.replace('/')
  } catch (error: any) {
    message.error(error.detail || '登录失败')
  } finally {
    loading.value = false
  }
}

async function handleRegister() {
  try {
    await registerFormRef.value?.validate()
    registerLoading.value = true
    await authApi.register(registerData.value)
    message.success('注册成功，请登录')
    showRegister.value = false
  } catch (error: any) {
    message.error(error.detail || '注册失败')
  } finally {
    registerLoading.value = false
  }
}

async function loadClasses() {
  try {
    const data = await authApi.getClasses() as any
    classOptions.value = data.map((c: any) => ({
      label: c.name,
      value: c.id
    }))
  } catch (error) {
    console.error('加载班级列表失败', error)
  }
}

async function loadSettings() {
  try {
    const data = await authApi.getSettings() as any
    registerEnabled.value = data.student_register_enabled !== false
  } catch (error) {
    // 默认允许注册
    registerEnabled.value = true
  }
}

onMounted(() => {
  loadClasses()
  loadSettings()
})
</script>

<style scoped>
.login-container {
  width: 100vw;
  height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: url('@/assets/login-bg.png') center center / cover no-repeat;
  position: relative;
}

.login-container::before {
  content: '';
  position: absolute;
  inset: 0;
  background: rgba(0, 0, 0, 0.35);
  backdrop-filter: blur(2px);
}

.login-background {
  width: 100%;
  max-width: 480px;
  padding: 20px;
  position: relative;
  z-index: 1;
}

.login-card {
  background: rgba(255, 255, 255, 0.92);
  border-radius: 16px;
  padding: 40px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-header h1 {
  margin-top: 16px;
  font-size: 24px;
  color: #333;
}

.login-header p {
  margin-top: 8px;
  color: #666;
  font-size: 14px;
}

.login-footer {
  margin-top: 24px;
}
</style>
