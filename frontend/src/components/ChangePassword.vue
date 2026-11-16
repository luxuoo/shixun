<!--
  修改密码弹窗（学生/教师/管理员通用）
  <ChangePassword v-model:show="showPwd" />
-->
<template>
  <n-modal
    v-model:show="visible"
    preset="card"
    title="修改密码"
    :style="{ width: '420px', maxWidth: '92vw' }"
    :bordered="false"
  >
    <n-form ref="formRef" :model="form" :rules="rules" label-placement="left" label-width="76">
      <n-form-item label="原密码" path="old_password">
        <n-input v-model:value="form.old_password" type="password" show-password-on="click" placeholder="当前登录密码" />
      </n-form-item>
      <n-form-item label="新密码" path="new_password">
        <n-input v-model:value="form.new_password" type="password" show-password-on="click" placeholder="至少 6 位" />
      </n-form-item>
      <n-form-item label="确认密码" path="confirm">
        <n-input v-model:value="form.confirm" type="password" show-password-on="click" placeholder="再输入一次" />
      </n-form-item>
    </n-form>
    <template #footer>
      <n-space justify="end">
        <n-button @click="visible = false">取消</n-button>
        <n-button type="primary" :loading="saving" @click="submit">保存</n-button>
      </n-space>
    </template>
  </n-modal>
</template>

<script setup lang="ts">
import { ref, computed } from 'vue'
import { useMessage } from 'naive-ui'
import type { FormInst, FormRules } from 'naive-ui'
import { authApi } from '@/api'

const props = defineProps<{ show: boolean }>()
const emit = defineEmits<{
  (e: 'update:show', value: boolean): void
}>()

const visible = computed({
  get: () => props.show,
  set: (v) => emit('update:show', v)
})

const message = useMessage()
const formRef = ref<FormInst | null>(null)
const saving = ref(false)
const form = ref({ old_password: '', new_password: '', confirm: '' })

const rules: FormRules = {
  old_password: { required: true, message: '请输入原密码', trigger: 'blur' },
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '新密码至少 6 位', trigger: 'blur' }
  ],
  confirm: {
    required: true,
    trigger: 'blur',
    validator: (_rule, value) => {
      if (!value) return new Error('请再输入一次新密码')
      if (value !== form.value.new_password) return new Error('两次输入的新密码不一致')
      return true
    }
  }
}

async function submit() {
  try {
    await formRef.value?.validate()
  } catch {
    return
  }
  saving.value = true
  try {
    await authApi.changePassword({
      old_password: form.value.old_password,
      new_password: form.value.new_password
    })
    message.success('密码已修改，下次登录请使用新密码')
    visible.value = false
    form.value = { old_password: '', new_password: '', confirm: '' }
  } catch (e: any) {
    message.error(e?.detail || '修改失败')
  } finally {
    saving.value = false
  }
}
</script>
