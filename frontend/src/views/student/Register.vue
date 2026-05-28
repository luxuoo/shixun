<template>
  <div class="register-container">
    <div class="register-card">
      <div class="register-header">
        <n-icon size="48" color="#2080f0">
          <svg viewBox="0 0 24 24">
            <path fill="currentColor" d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
          </svg>
        </n-icon>
        <h1>学生注册</h1>
        <p>创建账号开始编程学习之旅</p>
      </div>

      <n-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-placement="left"
        label-width="80"
      >
        <n-form-item label="用户名" path="username">
          <n-input v-model:value="formData.username" placeholder="请输入用户名" size="large">
            <template #prefix>
              <n-icon><svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 12c2.21 0 4-1.79 4-4s-1.79-4-4-4-4 1.79-4 4 1.79 4 4 4zm0 2c-2.67 0-8 1.34-8 4v2h16v-2c0-2.66-5.33-4-8-4z"/></svg></n-icon>
            </template>
          </n-input>
        </n-form-item>

        <n-form-item label="密码" path="password">
          <n-input v-model:value="formData.password" type="password" placeholder="请输入密码" size="large" show-password-on="click">
            <template #prefix>
              <n-icon><svg viewBox="0 0 24 24"><path fill="currentColor" d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z"/></svg></n-icon>
            </template>
          </n-input>
        </n-form-item>

        <n-form-item label="确认密码" path="confirmPassword">
          <n-input v-model:value="formData.confirmPassword" type="password" placeholder="请再次输入密码" size="large" show-password-on="click">
            <template #prefix>
              <n-icon><svg viewBox="0 0 24 24"><path fill="currentColor" d="M18 8h-1V6c0-2.76-2.24-5-5-5S7 3.24 7 6v2H6c-1.1 0-2 .9-2 2v10c0 1.1.9 2 2 2h12c1.1 0 2-.9 2-2V10c0-1.1-.9-2-2-2zm-6 9c-1.1 0-2-.9-2-2s.9-2 2-2 2 .9 2 2-.9 2-2 2zm3.1-9H8.9V6c0-1.71 1.39-3.1 3.1-3.1 1.71 0 3.1 1.39 3.1 3.1v2z"/></svg></n-icon>
            </template>
          </n-input>
        </n-form-item>

        <n-form-item label="姓名" path="name">
          <n-input v-model:value="formData.name" placeholder="请输入真实姓名" size="large">
            <template #prefix>
              <n-icon><svg viewBox="0 0 24 24"><path fill="currentColor" d="M12 2C6.48 2 2 6.48 2 12s4.48 10 10 10 10-4.48 10-10S17.52 2 12 2zm0 3c1.66 0 3 1.34 3 3s-1.34 3-3 3-3-1.34-3-3 1.34-3 3-3zm0 14.2c-2.5 0-4.71-1.28-6-3.22.03-1.99 4-3.08 6-3.08 1.99 0 5.97 1.09 6 3.08-1.29 1.94-3.5 3.22-6 3.22z"/></svg></n-icon>
            </template>
          </n-input>
        </n-form-item>

        <n-form-item label="学号" path="student_id">
          <n-input v-model:value="formData.student_id" placeholder="请输入学号" size="large">
            <template #prefix>
              <n-icon><svg viewBox="0 0 24 24"><path fill="currentColor" d="M20 4H4c-1.11 0-1.99.89-1.99 2L2 18c0 1.11.89 2 2 2h16c1.11 0 2-.89 2-2V6c0-1.11-.89-2-2-2zm0 14H4v-6h16v6zm0-10H4V6h16v2z"/></svg></n-icon>
            </template>
          </n-input>
        </n-form-item>

        <n-form-item label="邮箱" path="email">
          <n-input v-model:value="formData.email" placeholder="请输入邮箱" size="large">
            <template #prefix>
              <n-icon><svg viewBox="0 0 24 24"><path fill="currentColor" d="M20 4H4c-1.1 0-1.99.9-1.99 2L2 18c0 1.1.9 2 2 2h16c1.1 0 2-.9 2-2V6c0-1.1-.9-2-2-2zm0 4l-8 5-8-5V6l8 5 8-5v2z"/></svg></n-icon>
            </template>
          </n-input>
        </n-form-item>

        <n-form-item label="班级" path="class_id">
          <n-select
            v-model:value="formData.class_id"
            :options="classOptions"
            placeholder="请选择班级"
            size="large"
          />
        </n-form-item>

        <n-form-item>
          <n-button type="primary" size="large" block :loading="loading" @click="handleRegister">
            注册
          </n-button>
        </n-form-item>
      </n-form>

      <div class="register-footer">
        <n-space justify="center">
          <n-button text type="primary" @click="router.push('/login')">
            已有账号？立即登录
          </n-button>
        </n-space>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import type { FormInst, FormRules } from 'naive-ui'
import { authApi } from '@/api'

const router = useRouter()
const message = useMessage()
const formRef = ref<FormInst | null>(null)
const loading = ref(false)
const classOptions = ref<{ label: string; value: number }[]>([])

const formData = ref({
  username: '',
  password: '',
  confirmPassword: '',
  name: '',
  student_id: '',
  email: '',
  class_id: null as number | null
})

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 20, message: '用户名长度为3-20个字符', trigger: 'blur' }
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码长度不少于6个字符', trigger: 'blur' }
  ],
  confirmPassword: [
    { required: true, message: '请再次输入密码', trigger: 'blur' },
    {
      validator: (rule: any, value: string) => {
        return value === formData.value.password ? true : new Error('两次密码不一致')
      },
      trigger: 'blur'
    }
  ],
  name: [
    { required: true, message: '请输入姓名', trigger: 'blur' }
  ]
}

async function handleRegister() {
  try {
    await formRef.value?.validate()
    loading.value = true
    await authApi.register({
      username: formData.value.username,
      password: formData.value.password,
      name: formData.value.name,
      student_id: formData.value.student_id,
      email: formData.value.email,
      class_id: formData.value.class_id
    })
    message.success('注册成功，请登录')
    router.push('/login')
  } catch (error: any) {
    message.error(error.detail || '注册失败')
  } finally {
    loading.value = false
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

onMounted(() => {
  loadClasses()
})
</script>

<style scoped>
.register-container {
  width: 100vw;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  background: #000;
  padding: 20px;
}

.register-card {
  width: 100%;
  max-width: 500px;
  background: #fff;
  border-radius: 16px;
  padding: 40px;
  box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
}

.register-header {
  text-align: center;
  margin-bottom: 32px;
}

.register-header h1 {
  margin-top: 16px;
  font-size: 24px;
  color: #333;
}

.register-header p {
  margin-top: 8px;
  color: #666;
  font-size: 14px;
}

.register-footer {
  margin-top: 24px;
}
</style>
