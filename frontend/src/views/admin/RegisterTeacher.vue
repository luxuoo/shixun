<template>
  <div class="register-container">
    <div class="register-card">
      <div class="register-header">
        <n-icon size="48" color="#f0a020">
          <svg viewBox="0 0 24 24">
            <path fill="currentColor" d="M12 2L2 7l10 5 10-5-10-5zM2 17l10 5 10-5M2 12l10 5 10-5"/>
          </svg>
        </n-icon>
        <h1>教师注册</h1>
        <p>创建教师账号管理教学课程</p>
      </div>

      <n-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-placement="left"
        label-width="80"
      >
        <n-form-item label="用户名" path="username">
          <n-input v-model:value="formData.username" placeholder="请输入用户名" size="large" />
        </n-form-item>

        <n-form-item label="密码" path="password">
          <n-input v-model:value="formData.password" type="password" placeholder="请输入密码" size="large" show-password-on="click" />
        </n-form-item>

        <n-form-item label="确认密码" path="confirmPassword">
          <n-input v-model:value="formData.confirmPassword" type="password" placeholder="请再次输入密码" size="large" show-password-on="click" />
        </n-form-item>

        <n-form-item label="姓名" path="name">
          <n-input v-model:value="formData.name" placeholder="请输入真实姓名" size="large" />
        </n-form-item>

        <n-form-item label="邮箱" path="email">
          <n-input v-model:value="formData.email" placeholder="请输入邮箱" size="large" />
        </n-form-item>

        <n-form-item label="班级名称" path="class_name">
          <n-input v-model:value="formData.class_name" placeholder="请输入班级名称（如：2024级计算机1班）" size="large" />
        </n-form-item>

        <n-form-item>
          <n-button type="warning" size="large" block :loading="loading" @click="handleRegister">
            注册教师账号
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
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useMessage } from 'naive-ui'
import type { FormInst, FormRules } from 'naive-ui'
import { authApi } from '@/api'

const router = useRouter()
const message = useMessage()
const formRef = ref<FormInst | null>(null)
const loading = ref(false)

const formData = ref({
  username: '',
  password: '',
  confirmPassword: '',
  name: '',
  email: '',
  class_name: ''
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

    // 注册教师账号
    await authApi.register({
      username: formData.value.username,
      password: formData.value.password,
      name: formData.value.name,
      email: formData.value.email,
      role: 'teacher'
    })

    message.success('教师账号注册成功，请登录后在管理后台创建班级')
    router.push('/login')
  } catch (error: any) {
    message.error(error.detail || '注册失败')
  } finally {
    loading.value = false
  }
}
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
