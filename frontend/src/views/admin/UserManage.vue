<template>
  <div class="user-manage-container">
    <n-space justify="space-between" align="center" style="margin-bottom: 24px;">
      <h2>用户管理</h2>
      <n-space>
        <n-select
          v-model:value="filterRole"
          :options="roleOptions"
          placeholder="筛选角色"
          clearable
          style="width: 150px;"
          @update:value="loadUsers"
        />
        <n-button type="primary" @click="openCreateUser">
          创建用户
        </n-button>
      </n-space>
    </n-space>

    <n-card>
      <n-data-table
        :columns="columns"
        :data="users"
        :loading="loading"
        :bordered="false"
        :pagination="pagination"
      />
    </n-card>

    <!-- 创建/编辑用户弹窗 -->
    <n-modal v-model:show="showUserModal" preset="card" :title="editingUser ? '编辑用户' : '创建用户'" style="width: 500px">
      <n-form
        ref="formRef"
        :model="formData"
        :rules="rules"
        label-placement="left"
        label-width="80"
      >
        <n-form-item label="用户名" path="username">
          <n-input v-model:value="formData.username" placeholder="请输入用户名" :disabled="!!editingUser" />
        </n-form-item>
        <n-form-item :label="editingUser ? '新密码' : '密码'" path="password">
          <n-input v-model:value="formData.password" type="password" :placeholder="editingUser ? '留空则不修改' : '请输入密码'" />
        </n-form-item>
        <n-form-item label="姓名" path="name">
          <n-input v-model:value="formData.name" placeholder="请输入姓名" />
        </n-form-item>
        <n-form-item label="角色" path="role">
          <n-select
            v-model:value="formData.role"
            :options="roleOptions"
            placeholder="选择角色"
          />
        </n-form-item>
        <n-form-item label="邮箱" path="email">
          <n-input v-model:value="formData.email" placeholder="请输入邮箱" />
        </n-form-item>
        <n-form-item label="学号" path="student_id">
          <n-input v-model:value="formData.student_id" placeholder="请输入学号" />
        </n-form-item>
        <n-form-item label="班级" path="class_id">
          <n-select
            v-model:value="formData.class_id"
            :options="classOptions"
            placeholder="选择班级"
            clearable
          />
        </n-form-item>
      </n-form>
      <template #footer>
        <n-space justify="end">
          <n-button @click="showUserModal = false">取消</n-button>
          <n-button type="primary" :loading="saveLoading" @click="handleSaveUser">
            {{ editingUser ? '保存' : '创建' }}
          </n-button>
        </n-space>
      </template>
    </n-modal>
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, onMounted, h } from 'vue'
import { useMessage, useDialog } from 'naive-ui'
import type { FormInst, FormRules } from 'naive-ui'
import { NButton, NTag, NSpace } from 'naive-ui'
import { authApi } from '@/api'

const message = useMessage()
const dialog = useDialog()
const loading = ref(false)
const saveLoading = ref(false)
const showUserModal = ref(false)
const formRef = ref<FormInst | null>(null)

const users = ref<any[]>([])
const editingUser = ref<any>(null)
const filterRole = ref<string | null>(null)
const classOptions = ref<{ label: string; value: number }[]>([])

const formData = ref({
  username: '',
  password: '',
  name: '',
  role: 'student',
  email: '',
  student_id: '',
  class_id: null as number | null
})

const rules: FormRules = {
  username: { required: true, message: '请输入用户名', trigger: 'blur' },
  name: { required: true, message: '请输入姓名', trigger: 'blur' },
  role: { required: true, message: '请选择角色', trigger: 'change' }
}

const roleOptions = [
  { label: '学生', value: 'student' },
  { label: '教师', value: 'teacher' },
  { label: '管理员', value: 'admin' }
]

const pagination = reactive({
  page: 1,
  pageSize: 20,
  showSizePicker: true,
  pageSizes: [10, 20, 50],
  onChange: (page: number) => { pagination.page = page },
  onUpdatePageSize: (pageSize: number) => { pagination.pageSize = pageSize; pagination.page = 1 }
})

const columns = [
  { title: 'ID', key: 'id', width: 60 },
  { title: '姓名', key: 'name', render: (row: any) => row.name || '-' },
  { title: '用户名', key: 'username' },
  {
    title: '角色',
    key: 'role',
    width: 80,
    render: (row: any) => {
      const map: Record<string, { label: string; type: string }> = {
        student: { label: '学生', type: 'info' },
        teacher: { label: '教师', type: 'warning' },
        admin: { label: '管理员', type: 'error' }
      }
      const info = map[row.role] || { label: row.role, type: 'default' }
      return h(NTag, { type: info.type as any, size: 'small' }, { default: () => info.label })
    }
  },
  { title: '学号', key: 'student_id', render: (row: any) => row.student_id || '-' },
  { title: '邮箱', key: 'email', render: (row: any) => row.email || '-' },
  {
    title: '状态',
    key: 'is_active',
    width: 80,
    render: (row: any) => h(NTag, { type: row.is_active ? 'success' : 'error', size: 'small' }, { default: () => row.is_active ? '正常' : '禁用' })
  },
  {
    title: '最后登录',
    key: 'last_login',
    width: 160,
    render: (row: any) => row.last_login ? new Date(row.last_login).toLocaleString() : '-'
  },
  {
    title: '操作',
    key: 'actions',
    width: 240,
    render: (row: any) => h(NSpace, { size: 'small' }, {
      default: () => [
        h(NButton, { type: 'info', size: 'small', onClick: () => openEditUser(row) }, { default: () => '编辑' }),
        h(NButton, {
          type: row.is_active ? 'warning' : 'success',
          size: 'small',
          onClick: () => toggleUser(row)
        }, { default: () => row.is_active ? '禁用' : '启用' }),
        h(NButton, { type: 'error', size: 'small', onClick: () => confirmDeleteUser(row) }, { default: () => '删除' })
      ]
    })
  }
]

function openCreateUser() {
  editingUser.value = null
  formData.value = { username: '', password: '', name: '', role: 'student', email: '', student_id: '', class_id: null }
  showUserModal.value = true
}

function openEditUser(user: any) {
  editingUser.value = user
  formData.value = {
    username: user.username,
    password: '',
    name: user.name || '',
    role: user.role,
    email: user.email || '',
    student_id: user.student_id || '',
    class_id: user.class_id || null
  }
  showUserModal.value = true
}

async function loadUsers() {
  loading.value = true
  try {
    const data = await authApi.getUsers(filterRole.value || undefined) as any
    users.value = data
  } catch (error) {
    console.error('加载用户列表失败', error)
  } finally {
    loading.value = false
  }
}

async function loadClasses() {
  try {
    const data = await authApi.getClasses() as any
    classOptions.value = data.map((c: any) => ({ label: c.name, value: c.id }))
  } catch (error) {
    console.error('加载班级列表失败', error)
  }
}

async function handleSaveUser() {
  try {
    await formRef.value?.validate()
    saveLoading.value = true

    if (editingUser.value) {
      const updateData: any = { ...formData.value }
      if (!updateData.password) delete updateData.password
      delete updateData.username // 用户名不可改
      await authApi.updateUser(editingUser.value.id, updateData)
      message.success('用户更新成功')
    } else {
      if (!formData.value.password) {
        message.error('请输入密码')
        return
      }
      await authApi.registerByAdmin(formData.value)
      message.success('用户创建成功')
    }
    showUserModal.value = false
    loadUsers()
  } catch (error: any) {
    message.error(error.detail || '操作失败')
  } finally {
    saveLoading.value = false
  }
}

async function toggleUser(user: any) {
  try {
    const result = await authApi.toggleUser(user.id) as any
    message.success(result.message)
    loadUsers()
  } catch (error: any) {
    message.error(error.detail || '操作失败')
  }
}

function confirmDeleteUser(user: any) {
  dialog.warning({
    title: '确认删除',
    content: `确定要删除用户"${user.name || user.username}"吗？此操作不可恢复。`,
    positiveText: '删除',
    negativeText: '取消',
    onPositiveClick: async () => {
      try {
        await authApi.deleteUser(user.id)
        message.success('用户已删除')
        loadUsers()
      } catch (error: any) {
        message.error(error.detail || '删除失败')
      }
    }
  })
}

onMounted(() => {
  loadUsers()
  loadClasses()
})
</script>

<style scoped>
.user-manage-container {
  max-width: 1400px;
  margin: 0 auto;
}
</style>
