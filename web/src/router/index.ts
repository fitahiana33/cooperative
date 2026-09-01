import { createRouter, createWebHistory } from 'vue-router'
import { useAuthenticationStore } from '../stores/authentication/store'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: () => import('../views/authentication/LoginView.vue'),
      meta: { layout: 'auth' },
    },
    {
      path: '/register',
      name: 'register',
      component: () => import('../views/authentication/RegisterView.vue'),
      meta: { layout: 'auth' },
    },
    {
      path: '/forgot-password',
      name: 'forgot-password',
      component: () => import('../views/authentication/ForgotPasswordView.vue'),
      meta: { layout: 'auth' },
    },
    {
      path: '/',
      name: 'home',
      component: () => import('../views/HomeView.vue'),
      meta: { requiresAuth: true, layout: 'default' },
    },
    {
      path: '/users',
      name: 'users',
      component: () => import('../views/UsersView.vue'),
      meta: { requiresAuth: true, requiredRoles: ['admin', 'responsable_gare', 'responsable_cooperative'], layout: 'default' },
    },
    {
      path: '/gares',
      name: 'gares',
      component: () => import('../views/ManagementView.vue'),
      meta: { requiresAuth: true, requiredRoles: ['admin', 'responsable_gare', 'agent_gare'], layout: 'default' },
    },
    {
      path: '/gares/new', name: 'gare-create', component: () => import('../views/management/GareFormView.vue'),
      meta: { requiresAuth: true, requiredRoles: ['admin', 'responsable_gare'], layout: 'default' },
    },
    {
      path: '/gares/:id/edit', name: 'gare-edit', component: () => import('../views/management/GareFormView.vue'),
      meta: { requiresAuth: true, requiredRoles: ['admin', 'responsable_gare'], layout: 'default' },
    },
    {
      path: '/cooperatives',
      name: 'cooperatives',
      component: () => import('../views/ManagementView.vue'),
      meta: { requiresAuth: true, requiredRoles: ['admin', 'responsable_cooperative'], layout: 'default' },
    },
    {
      path: '/cooperatives/new', name: 'cooperative-create', component: () => import('../views/management/CooperativeFormView.vue'),
      meta: { requiresAuth: true, requiredRoles: ['admin', 'responsable_cooperative'], layout: 'default' },
    },
    {
      path: '/cooperatives/:id/edit', name: 'cooperative-edit', component: () => import('../views/management/CooperativeFormView.vue'),
      meta: { requiresAuth: true, requiredRoles: ['admin', 'responsable_cooperative'], layout: 'default' },
    },
    {
      path: '/roles',
      name: 'roles',
      component: () => import('../views/ManagementView.vue'),
      meta: { requiresAuth: true, requiredRoles: ['admin'], layout: 'default' },
    },
  ],
})

router.beforeEach((to) => {
  const auth = useAuthenticationStore()
  const publicAuthRoutes = ['login', 'register', 'forgot-password']

  if (to.meta.requiresAuth && !auth.isAuthenticated) {
    return { name: 'login' }
  }

  if (publicAuthRoutes.includes(to.name as string) && auth.isAuthenticated) {
    return { name: 'home' }
  }

  if (to.meta.requiredRoles && Array.isArray(to.meta.requiredRoles)) {
    const userRole = (auth.userRole || '').toLowerCase()
    const allowedRoles = (to.meta.requiredRoles as string[]).map((r) => r.toLowerCase())
    if (userRole !== 'admin' && !allowedRoles.includes(userRole)) {
      return { name: 'home' }
    }
  }
})

export default router
