import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'Login',
      component: () => import('@/views/student/Login.vue'),
      meta: { guest: true }
    },
    {
      path: '/register',
      name: 'Register',
      component: () => import('@/views/student/Register.vue'),
      meta: { guest: true }
    },
    {
      path: '/',
      component: () => import('@/layouts/StudentLayout.vue'),
      meta: { requiresAuth: true },
      children: [
        {
          path: '',
          name: 'Home',
          component: () => import('@/views/student/Home.vue')
        },
        {
          path: 'tasks',
          name: 'TaskList',
          component: () => import('@/views/student/TaskList.vue')
        },
        {
          path: 'tasks/:id',
          name: 'TaskDetail',
          component: () => import('@/views/student/TaskDetail.vue')
        },
        {
          path: 'submissions',
          name: 'Submissions',
          component: () => import('@/views/student/Submissions.vue')
        },
        {
          path: 'scores',
          name: 'Scores',
          component: () => import('@/views/student/Scores.vue')
        },
        {
          path: 'ai-history',
          name: 'AiHistory',
          component: () => import('@/views/student/AiHistory.vue')
        }
      ]
    },
    {
      path: '/admin',
      component: () => import('@/layouts/AdminLayout.vue'),
      meta: { requiresAuth: true, requiresTeacher: true },
      children: [
        {
          path: '',
          name: 'AdminDashboard',
          component: () => import('@/views/admin/Dashboard.vue')
        },
        {
          path: 'students',
          name: 'AdminStudents',
          component: () => import('@/views/admin/Students.vue')
        },
        {
          path: 'tasks',
          name: 'AdminTasks',
          component: () => import('@/views/admin/TaskManage.vue')
        },
        {
          path: 'submissions',
          name: 'AdminSubmissions',
          component: () => import('@/views/admin/Submissions.vue')
        },
        {
          path: 'ai-stats',
          name: 'AdminAiStats',
          component: () => import('@/views/admin/AiStats.vue')
        },
        {
          path: 'classes',
          name: 'AdminClasses',
          component: () => import('@/views/admin/ClassManage.vue')
        },
        {
          path: 'users',
          name: 'AdminUsers',
          component: () => import('@/views/admin/UserManage.vue'),
          meta: { requiresAdmin: true }
        },
        {
          path: 'ai-logs',
          name: 'AdminAiLogs',
          component: () => import('@/views/admin/AiLogs.vue')
        },
        {
          path: 'system-stats',
          name: 'AdminSystemStats',
          component: () => import('@/views/admin/SystemStats.vue'),
          meta: { requiresAdmin: true }
        },
        {
          path: 'roll-call',
          name: 'AdminRollCall',
          component: () => import('@/views/admin/RollCall.vue')
        },
        {
          path: 'process-eval',
          name: 'AdminProcessEval',
          component: () => import('@/views/admin/ProcessEvalDashboard.vue')
        },
        {
          path: 'process-eval-config',
          name: 'AdminProcessEvalConfig',
          component: () => import('@/views/admin/ProcessEvalConfig.vue')
        }
      ]
    }
  ]
})

// 路由守卫 - 使用懒加载避免循环依赖
router.beforeEach(async (to, from, next) => {
  // 如果是登录页，直接放行
  if (to.path === '/login') {
    next()
    return
  }

  // 动态导入 user store 避免循环
  const { useUserStore } = await import('@/stores/user')
  const userStore = useUserStore()

  // 如果有 token 但没有用户信息，尝试获取
  if (userStore.token && !userStore.user && !userStore.loading) {
    await userStore.fetchUser()
  }

  // 需要认证的页面
  if (to.meta.requiresAuth && !userStore.isLoggedIn) {
    next('/login')
    return
  }

  // 需要教师权限的页面
  if (to.meta.requiresTeacher && !userStore.isTeacher) {
    next('/')
    return
  }

  // 需要管理员权限的页面
  if (to.meta.requiresAdmin && !userStore.isAdmin) {
    next('/admin')
    return
  }

  next()
})

export default router
