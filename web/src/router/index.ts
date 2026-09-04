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
        component: () => import('../views/dashboard/HomeView.vue'),
      meta: { requiresAuth: true, layout: 'default' },
    },
      {
        path: '/users',
        name: 'users',
        component: () => import('../views/administration/users/UsersView.vue'),
        meta: { requiresAuth: true, requiredRoles: ['admin'], layout: 'default' },
      },
      {
        path: '/users/:id',
        name: 'user-detail',
        component: () => import('../views/administration/users/UserDetailView.vue'),
        meta: { requiresAuth: true, requiredRoles: ['admin'], layout: 'default' },
      },
      {
        path: '/users/new',
        name: 'user-create',
        component: () => import('../views/administration/users/UserFormView.vue'),
        meta: { requiresAuth: true, requiredRoles: ['admin'], layout: 'default' },
      },
      {
        path: '/users/:id/edit',
        name: 'user-edit',
        component: () => import('../views/administration/users/UserFormView.vue'),
        meta: { requiresAuth: true, requiredRoles: ['admin'], layout: 'default' },
      },
    {
      path: '/gares',
      name: 'gares',
      component: () => import('../views/management/ManagementView.vue'),
      meta: { requiresAuth: true, requiredRoles: ['admin', 'responsable_gare', 'agent_gare'], layout: 'default' },
    },
    {
      path: '/gares/:id',
      name: 'gare-detail',
      component: () => import('../views/management/GareDetailView.vue'),
      meta: { requiresAuth: true, requiredRoles: ['admin', 'responsable_gare', 'agent_gare'], layout: 'default' },
    },
    {
      path: '/gares/new',
      name: 'gare-create',
      component: () => import('../views/management/GareFormView.vue'),
      meta: { requiresAuth: true, requiredRoles: ['admin', 'responsable_gare'], layout: 'default' },
    },
    {
      path: '/gares/:id/edit',
      name: 'gare-edit',
      component: () => import('../views/management/GareFormView.vue'),
      meta: { requiresAuth: true, requiredRoles: ['admin', 'responsable_gare'], layout: 'default' },
    },
    {
      path: '/cooperatives',
      name: 'cooperatives',
      component: () => import('../views/management/ManagementView.vue'),
      meta: { requiresAuth: true, requiredRoles: ['admin', 'responsable_gare', 'responsable_cooperative'], layout: 'default' },
    },
    {
      path: '/cooperatives/:id',
      name: 'cooperative-detail',
      component: () => import('../views/management/CooperativeDetailView.vue'),
      meta: { requiresAuth: true, requiredRoles: ['admin', 'responsable_gare', 'responsable_cooperative'], layout: 'default' },
    },
    {
      path: '/cooperatives/new',
      name: 'cooperative-create',
      component: () => import('../views/management/CooperativeFormView.vue'),
      meta: { requiresAuth: true, requiredRoles: ['admin'], layout: 'default' },
    },
    {
      path: '/cooperatives/:id/edit',
      name: 'cooperative-edit',
      component: () => import('../views/management/CooperativeFormView.vue'),
      meta: { requiresAuth: true, requiredRoles: ['admin', 'responsable_cooperative'], layout: 'default' },
    },
      {
        path: '/roles',
        name: 'roles',
        component: () => import('../views/administration/roles/RolesPermissionsView.vue'),
      meta: { requiresAuth: true, requiredRoles: ['admin'], layout: 'default' },
    },
    {
      path: '/vehicules',
      name: 'vehicules',
      component: () => import('../views/management/FleetListView.vue'),
      meta: { requiresAuth: true, requiredRoles: ['admin', 'responsable_cooperative', 'chauffeur'], layout: 'default' },
    },
    {
      path: '/vehicules/new',
      name: 'vehicule-create',
      component: () => import('../views/management/FleetFormView.vue'),
      meta: { requiresAuth: true, requiredRoles: ['admin', 'responsable_cooperative'], layout: 'default' },
    },
    {
      path: '/vehicules/:id',
      name: 'vehicule-detail',
      component: () => import('../views/management/FleetDetailView.vue'),
      meta: { requiresAuth: true, requiredRoles: ['admin', 'responsable_cooperative', 'chauffeur'], layout: 'default' },
    },
    {
      path: '/vehicules/:id/edit',
      name: 'vehicule-edit',
      component: () => import('../views/management/FleetFormView.vue'),
      meta: { requiresAuth: true, requiredRoles: ['admin', 'responsable_cooperative'], layout: 'default' },
    },
    {
      path: '/chauffeurs',
      name: 'chauffeurs',
      component: () => import('../views/management/FleetListView.vue'),
      meta: { requiresAuth: true, requiredRoles: ['admin', 'responsable_cooperative'], layout: 'default' },
    },
    {
      path: '/chauffeurs/new',
      name: 'chauffeur-create',
      component: () => import('../views/management/FleetFormView.vue'),
      meta: { requiresAuth: true, requiredRoles: ['admin', 'responsable_cooperative'], layout: 'default' },
    },
    {
      path: '/chauffeurs/:id',
      name: 'chauffeur-detail',
      component: () => import('../views/management/FleetDetailView.vue'),
      meta: { requiresAuth: true, requiredRoles: ['admin', 'responsable_cooperative'], layout: 'default' },
    },
    {
      path: '/chauffeurs/:id/edit',
      name: 'chauffeur-edit',
      component: () => import('../views/management/FleetFormView.vue'),
      meta: { requiresAuth: true, requiredRoles: ['admin', 'responsable_cooperative'], layout: 'default' },
    },
    {
      path: '/marques',
      name: 'marques',
      component: () => import('../views/management/FleetListView.vue'),
      meta: { requiresAuth: true, requiredRoles: ['admin', 'responsable_cooperative'], layout: 'default' },
    },
    {
      path: '/marques/new',
      name: 'marque-create',
      component: () => import('../views/management/FleetFormView.vue'),
      meta: { requiresAuth: true, requiredRoles: ['admin'], layout: 'default' },
    },
    {
      path: '/marques/:id',
      name: 'marque-detail',
      component: () => import('../views/management/FleetDetailView.vue'),
      meta: { requiresAuth: true, requiredRoles: ['admin', 'responsable_cooperative'], layout: 'default' },
    },
    {
      path: '/marques/:id/edit',
      name: 'marque-edit',
      component: () => import('../views/management/FleetFormView.vue'),
      meta: { requiresAuth: true, requiredRoles: ['admin'], layout: 'default' },
    },
    {
      path: '/modeles',
      name: 'modeles',
      component: () => import('../views/management/FleetListView.vue'),
      meta: { requiresAuth: true, requiredRoles: ['admin', 'responsable_cooperative'], layout: 'default' },
    },
    {
      path: '/modeles/new',
      name: 'modele-create',
      component: () => import('../views/management/FleetFormView.vue'),
      meta: { requiresAuth: true, requiredRoles: ['admin'], layout: 'default' },
    },
    {
      path: '/modeles/:id',
      name: 'modele-detail',
      component: () => import('../views/management/FleetDetailView.vue'),
      meta: { requiresAuth: true, requiredRoles: ['admin', 'responsable_cooperative'], layout: 'default' },
    },
    {
      path: '/modeles/:id/edit',
      name: 'modele-edit',
      component: () => import('../views/management/FleetFormView.vue'),
      meta: { requiresAuth: true, requiredRoles: ['admin'], layout: 'default' },
    },
  ],
})

router.beforeEach((to) => {
  const auth = useAuthenticationStore()
  const publicAuthRoutes = ['login', 'register', 'forgot-password']
  const routePermissions: Record<string, string> = {
    users: 'USER_READ', 'user-detail': 'USER_READ', 'user-create': 'USER_CREATE', 'user-edit': 'USER_UPDATE',
    gares: 'GARE_READ', 'gare-create': 'GARE_CREATE', 'gare-edit': 'GARE_UPDATE',
    'gare-detail': 'GARE_READ',
    cooperatives: 'COOPERATIVE_READ', 'cooperative-detail': 'COOPERATIVE_READ', 'cooperative-create': 'COOPERATIVE_CREATE', 'cooperative-edit': 'COOPERATIVE_UPDATE',
    roles: 'ROLE_MANAGE',
    vehicules: 'VEHICULE_READ', 'vehicule-detail': 'VEHICULE_READ', 'vehicule-create': 'VEHICULE_CREATE', 'vehicule-edit': 'VEHICULE_UPDATE',
    chauffeurs: 'CHAUFFEUR_READ', 'chauffeur-detail': 'CHAUFFEUR_READ', 'chauffeur-create': 'CHAUFFEUR_CREATE', 'chauffeur-edit': 'CHAUFFEUR_UPDATE',
    marques: 'VEHICULE_READ', 'marque-detail': 'VEHICULE_READ', 'marque-create': 'VEHICULE_CREATE', 'marque-edit': 'VEHICULE_UPDATE',
    modeles: 'VEHICULE_READ', 'modele-detail': 'VEHICULE_READ', 'modele-create': 'VEHICULE_CREATE', 'modele-edit': 'VEHICULE_UPDATE',
  }

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

  const requiredPermission = routePermissions[String(to.name || '')]
  if (requiredPermission && !auth.hasPermission(requiredPermission)) {
    return { name: 'home' }
  }
})

export default router
