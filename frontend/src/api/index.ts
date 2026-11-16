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
      // 只有明确 401 才代表登录失效；502/503 是服务重启中，不能把用户踢出去
      if (status === 401) {
        localStorage.removeItem('token')
        if (window.location.pathname !== '/login') {
          window.location.replace('/login')
        }
      }
      const detail =
        data && typeof data === 'object' && data.detail
          ? data.detail
          : status === 502 || status === 503 || status === 504
            ? '服务正在重启或暂时不可用，请稍后重试'
            : typeof data === 'string' && data
              ? data
              : error.message
      // 统一成对象，调用方既可以用 e.detail，也可以用 e.message
      return Promise.reject({ status, detail, message: detail, data })
    }
    // 网络层错误（断网、连接被拒）：同样不当作登录失效
    const detail = '无法连接服务器，服务可能正在重启'
    return Promise.reject({ status: 0, detail, message: detail, original: error })
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
  changePassword: (data: { old_password: string; new_password: string }) =>
    api.post('/auth/change-password', data),
  updateSettings: (data: { student_register_enabled?: boolean; ai_chat_enabled?: boolean; ai_hints_limit?: number; ai_auto_score?: boolean; submission_limit?: number; grade_weights?: { ai: number; teacher: number; attendance: number }; rollcall_score?: number; rollcall_auto_score?: boolean; student_view_grades?: boolean }) =>
    api.put('/auth/settings', data)
}

// 任务接口
export const taskApi = {
  getList: (category?: string, showAll?: boolean) =>
    api.get('/tasks', { params: { category, show_all: showAll || undefined } }),
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
    api.get('/submissions/scores/my'),
  rescore: (id: number) =>
    api.post(`/submissions/${id}/rescore`)
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
// 部署运维（仅管理员，需服务端开启 OPS_ENABLED）
export const opsApi = {
  getStatus: (lines = 60) =>
    api.get('/admin/ops/status', { params: { lines } }),
  check: () =>
    api.get('/admin/ops/check', { timeout: 45000 }),
  deploy: (payload: { ref?: string; force?: boolean } = {}) =>
    api.post('/admin/ops/deploy', payload, { timeout: 30000 }),
  rollback: (release?: string) =>
    api.post('/admin/ops/rollback', release ? { release } : {}, { timeout: 30000 }),
  getLog: (lines = 300) =>
    api.get('/admin/ops/log', { params: { lines } })
}

export const adminApi = {
  getDashboard: () =>
    api.get('/admin/dashboard'),
  // AI 服务配置（数据库优先于 .env，保存后即时生效）
  getAiConfig: () =>
    api.get('/admin/ai-config'),
  updateAiConfig: (data: {
    provider?: string
    providers?: Record<string, { api_key?: string; api_url?: string; model?: string }>
    clear?: string[]
  }) =>
    api.put('/admin/ai-config', data),
  testAi: (provider?: string) =>
    api.get('/admin/ai-test', { params: { provider }, timeout: 180000 }),
  getStudents: (class_id?: number) =>
    api.get('/admin/students', { params: { class_id } }),
  getStudentDetail: (id: number) =>
    api.get(`/admin/students/${id}`),
  deleteStudent: (id: number) =>
    api.delete(`/admin/students/${id}`),
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
  // 成绩汇总
  getGrades: (classId?: number) =>
    api.get('/admin/grades', { params: classId ? { class_id: classId } : {} }),
  // 导出成绩单（返回 Blob，前端触发下载）
  exportGrades: (classId?: number) =>
    api.get('/admin/export/grades', {
      params: classId ? { class_id: classId } : {},
      responseType: 'blob'
    }),
  // 点名记录
  recordRollcall: (data: { student_id: number; class_id?: number }) =>
    api.post('/admin/rollcall', data),
  getTodayRollcall: (classId?: number) =>
    api.get('/admin/rollcall/today', { params: classId ? { class_id: classId } : {} }),
}

// 过程性评价接口
export const evalApi = {
  // 模板管理
  getTemplates: (classId?: number) =>
    api.get('/evaluation/templates', { params: classId ? { class_id: classId } : {} }),
  getTemplate: (id: number) =>
    api.get(`/evaluation/templates/${id}`),
  createTemplate: (data: { name: string; description?: string; class_id?: number }) =>
    api.post('/evaluation/templates', data),
  updateTemplate: (id: number, data: any) =>
    api.put(`/evaluation/templates/${id}`, data),
  deleteTemplate: (id: number) =>
    api.delete(`/evaluation/templates/${id}`),
  activateTemplate: (id: number) =>
    api.post(`/evaluation/templates/${id}/activate`),
  initDefaultTemplate: (classId?: number) =>
    api.post('/evaluation/templates/init-default', null, { params: classId ? { class_id: classId } : {} }),
  checkTemplateWeights: (templateId: number) =>
    api.get(`/evaluation/templates/${templateId}/weight-validation`),

  // 阶段管理
  createPhase: (templateId: number, data: { name: string; weight: number; sort_order?: number }) =>
    api.post(`/evaluation/templates/${templateId}/phases`, data),
  updatePhase: (phaseId: number, data: any) =>
    api.put(`/evaluation/phases/${phaseId}`, data),
  deletePhase: (phaseId: number) =>
    api.delete(`/evaluation/phases/${phaseId}`),

  // 指标管理
  createIndicator: (phaseId: number, data: any) =>
    api.post(`/evaluation/phases/${phaseId}/indicators`, data),
  updateIndicator: (indicatorId: number, data: any) =>
    api.put(`/evaluation/indicators/${indicatorId}`, data),
  deleteIndicator: (indicatorId: number) =>
    api.delete(`/evaluation/indicators/${indicatorId}`),
  checkIndicatorWeights: (phaseId: number) =>
    api.post(`/evaluation/phases/${phaseId}/indicators/weight-validation`),

  // 评分主体
  addScorer: (indicatorId: number, data: { scorer_role: string; weight: number }) =>
    api.post(`/evaluation/indicators/${indicatorId}/scorers`, data),
  deleteScorer: (scorerId: number) =>
    api.delete(`/evaluation/scorers/${scorerId}`),

  // 评价记录
  createRecord: (data: any) =>
    api.post('/evaluation/records', data),
  batchCreateRecords: (data: any) =>
    api.post('/evaluation/records/batch', data),
  getRecords: (params?: { template_id?: number; student_id?: number; indicator_id?: number }) =>
    api.get('/evaluation/records', { params }),
  autoCollect: (templateId: number, classId?: number) =>
    api.post(`/evaluation/records/auto-collect/${templateId}`, null, { params: classId ? { class_id: classId } : {} }),

  // 学生看板
  getStudentDashboard: (studentId: number, templateId?: number) =>
    api.get(`/evaluation/dashboard/student/${studentId}`, { params: templateId ? { template_id: templateId } : {} }),
  getStudentRadar: (studentId: number, templateId?: number) =>
    api.get(`/evaluation/dashboard/student/${studentId}/radar`, { params: templateId ? { template_id: templateId } : {} }),
  getStudentTrend: (studentId: number, templateId?: number) =>
    api.get(`/evaluation/dashboard/student/${studentId}/trend`, { params: templateId ? { template_id: templateId } : {} }),

  // 班级看板
  getClassDashboard: (classId: number, templateId?: number) =>
    api.get(`/evaluation/dashboard/class/${classId}`, { params: templateId ? { template_id: templateId } : {} }),
  getClassRanking: (classId: number, templateId?: number) =>
    api.get(`/evaluation/dashboard/class/${classId}/ranking`, { params: templateId ? { template_id: templateId } : {} }),

  // 学生自评/互评
  studentSelfEval: (data: { indicator_id: number; template_id: number; score: number; remark?: string }) =>
    api.post('/evaluation/records/self-eval', data),
  studentPeerEval: (data: { indicator_id: number; template_id: number; student_id: number; score: number; remark?: string }) =>
    api.post('/evaluation/records/peer-eval', data),
  getIndicatorStudents: (indicatorId: number) =>
    api.get(`/evaluation/indicators/${indicatorId}/students`),

  // AI 辅助配置
  aiGenerateTemplate: (data: { course_name: string; course_description: string; category?: string; student_count?: number; task_count?: number; class_id?: number }) =>
    api.post('/evaluation/ai/generate-template', data),
  aiSuggestIndicators: (data: { phase_id: number }) =>
    api.post('/evaluation/ai/suggest-indicators', data),
  aiDiagnoseStudent: (studentId: number, templateId?: number) =>
    api.post(`/evaluation/ai/diagnose/${studentId}`, null, { params: templateId ? { template_id: templateId } : {} }),
  aiClassInsight: (classId: number, templateId?: number) =>
    api.post(`/evaluation/ai/class-insight/${classId}`, null, { params: templateId ? { template_id: templateId } : {} })
}
