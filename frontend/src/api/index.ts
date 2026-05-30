import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 120000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    return response.data
  },
  (error) => {
    if (error.response) {
      const { status, data } = error.response
      if (status === 401) {
        localStorage.removeItem('token')
        // 使用 router 跳转而不是 window.location
        if (window.location.pathname !== '/login') {
          window.location.replace('/login')
        }
      }
      return Promise.reject(data || error.message)
    }
    return Promise.reject(error)
  }
)

export default api

// 认证接口
export const authApi = {
  login: (data: { username: string; password: string }) =>
    api.post('/auth/login', data),
  register: (data: any) =>
    api.post('/auth/register', data),
  registerByAdmin: (data: any) =>
    api.post('/auth/register/admin', data),
  getMe: () =>
    api.get('/auth/me'),
  getClasses: () =>
    api.get('/auth/classes'),
  createClass: (data: any) =>
    api.post('/auth/classes', data),
  getUsers: (role?: string) =>
    api.get('/auth/users', { params: { role } }),
  updateUser: (id: number, data: any) =>
    api.put(`/auth/users/${id}`, data),
  deleteUser: (id: number) =>
    api.delete(`/auth/users/${id}`),
  toggleUser: (id: number) =>
    api.put(`/auth/users/${id}/toggle`),
  batchRegister: (data: { students: { student_id: string; name: string }[]; class_id: number }) =>
    api.post('/auth/batch-register', data),
  getSettings: () =>
    api.get('/auth/settings'),
  updateSettings: (data: { student_register_enabled?: boolean; ai_chat_enabled?: boolean; ai_hints_limit?: number; ai_auto_score?: boolean; submission_limit?: number; grade_weights?: { ai: number; teacher: number; attendance: number }; rollcall_score?: number; rollcall_auto_score?: boolean }) =>
    api.put('/auth/settings', data)
}

// 任务接口
export const taskApi = {
  getList: (category?: string) =>
    api.get('/tasks', { params: { category } }),
  getDetail: (id: number) =>
    api.get(`/tasks/${id}`),
  getSteps: (taskId: number) =>
    api.get(`/tasks/${taskId}/steps`),
  getStep: (taskId: number, stepId: number) =>
    api.get(`/tasks/${taskId}/steps/${stepId}`),
  create: (data: any) =>
    api.post('/tasks', data),
  update: (id: number, data: any) =>
    api.put(`/tasks/${id}`, data),
  delete: (id: number) =>
    api.delete(`/tasks/${id}`),
  createStep: (taskId: number, data: any) =>
    api.post(`/tasks/${taskId}/steps`, data),
  updateStep: (taskId: number, stepId: number, data: any) =>
    api.put(`/tasks/${taskId}/steps/${stepId}`, data),
  deleteStep: (taskId: number, stepId: number) =>
    api.delete(`/tasks/${taskId}/steps/${stepId}`),
  aiDecompose: (data: { title: string; description: string; category?: string; difficulty?: number; auto_publish?: boolean; detail_level?: string; steps_count?: number }) =>
    api.post('/tasks/ai-decompose', data)
}

// 提交接口
export const submissionApi = {
  create: (data: any) =>
    api.post('/submissions', data),
  getList: (params?: { task_id?: number; step_id?: number }) =>
    api.get('/submissions', { params }),
  getDetail: (id: number) =>
    api.get(`/submissions/${id}`),
  getMyScores: () =>
    api.get('/submissions/scores/my')
}

// AI 接口
export const aiApi = {
  getHint: (data: { task_id: number; step_id: number; student_code?: string; question?: string }) =>
    api.post('/ai/hint', data),
  analyzeCode: (data: { task_id: number; step_id: number; code: string }) =>
    api.post('/ai/analyze', data),
  scoreSubmission: (data: { task_id: number; step_id: number; code: string }) =>
    api.post('/ai/score', data),
  getHistory: (task_id?: number) =>
    api.get('/ai/history', { params: { task_id } })
}

// 管理接口
export const adminApi = {
  getDashboard: () =>
    api.get('/admin/dashboard'),
  getStudents: (class_id?: number) =>
    api.get('/admin/students', { params: { class_id } }),
  getStudentDetail: (id: number) =>
    api.get(`/admin/students/${id}`),
  getSubmissions: (params?: any) =>
    api.get('/admin/submissions', { params }),
  reviewSubmission: (id: number, data: { teacher_score: number; teacher_comment?: string }) =>
    api.put(`/admin/submissions/${id}/score`, data),
  batchScore: (data: { submission_ids: number[]; teacher_score: number; teacher_comment?: string }) =>
    api.post('/admin/submissions/batch-score', data),
  getAiStats: () =>
    api.get('/admin/ai-stats'),
  // 班级管理
  getClasses: () =>
    api.get('/admin/classes'),
  updateClass: (id: number, data: any) =>
    api.put(`/admin/classes/${id}`, data),
  deleteClass: (id: number) =>
    api.delete(`/admin/classes/${id}`),
  assignStudents: (classId: number, studentIds: number[]) =>
    api.post(`/admin/classes/${classId}/students`, { student_ids: studentIds }),
  getClassStats: (classId: number) =>
    api.get(`/admin/classes/${classId}/stats`),
  // AI 日志
  getAiLogs: (params?: { user_id?: number; request_type?: string; page?: number; page_size?: number }) =>
    api.get('/admin/ai-logs', { params }),
  // 系统统计
  getSystemStats: () =>
    api.get('/admin/system-stats'),
  // 加减分
  adjustScore: (studentId: number, data: { task_id?: number; adjustment: number; reason: string }) =>
    api.post(`/admin/students/${studentId}/adjust-score`, data),
  // 成绩汇总
  getGrades: (classId?: number) =>
    api.get('/admin/grades', { params: classId ? { class_id: classId } : {} }),
  // 点名记录
  recordRollcall: (data: { student_id: number; class_id?: number }) =>
    api.post('/admin/rollcall', data),
  getTodayRollcall: (classId?: number) =>
    api.get('/admin/rollcall/today', { params: classId ? { class_id: classId } : {} }),
  // 出勤分
  setAttendanceScore: (data: { student_id: number; task_id?: number; score: number }) =>
    api.post('/admin/attendance', data)
}
