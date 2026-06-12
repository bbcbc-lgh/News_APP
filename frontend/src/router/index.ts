import { createRouter, createWebHistory } from 'vue-router'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    { path: '/login',      name: 'login',      component: () => import('@/views/LoginView.vue'),      meta: { public: true } },
    { path: '/register',   name: 'register',   component: () => import('@/views/RegisterView.vue'),   meta: { public: true } },
    { path: '/',           redirect: '/news' },
    { path: '/news',       name: 'news',       component: () => import('@/views/NewsView.vue') },
    { path: '/news/detail/:id', name: 'newsDetail', component: () => import('@/views/NewsDetailView.vue') },
    { path: '/profile',    name: 'profile',    component: () => import('@/views/ProfileView.vue') }
  ]
})

router.beforeEach((to) => {
  const token = localStorage.getItem('token')
  if (!to.meta.public && !token) return '/login'
})

export default router
