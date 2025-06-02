import { createRouter, createWebHistory } from 'vue-router'
import HomeView from '../views/HomeView.vue'
import AssistantsView from '../views/AssistantsView.vue'
import LoginView from '../views/LoginView.vue'
import PhoneNumbersView from '../views/PhoneNumbersView.vue'
import CallsView from '../views/CallsView.vue'
import { useAuthStore } from '@/stores/auth'
import CallDetailsView from '../views/CallDetailsView.vue'
import KnowledgeBaseView from '../views/KnowledgeBaseView.vue'
import KnowledgeBaseDetailView from '../views/KnowledgeBaseDetailView.vue'
import NewKnowledgeBaseView from '../views/NewKnowledgeBaseView.vue'

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/',
      name: 'home',
      component: HomeView,
      meta: { requiresAuth: true }
    },
    {
      path: '/assistant/:id',
      name: 'assistant',
      component: AssistantsView,
      meta: { requiresAuth: true }
    },
    {
      path: '/phone-numbers',
      name: 'phone-numbers',
      component: PhoneNumbersView,
      meta: { requiresAuth: true }
    },
    {
      path: '/login',
      name: 'login',
      component: LoginView,
      meta: { public: true }
    },
    {
      path: '/calls',
      name: 'calls',
      component: CallsView,
      meta: { requiresAuth: true }
    },
    {
      path: '/calls/:id',
      name: 'call-details',
      component: () => import('@/views/CallDetailsView.vue')
    },
    {
      path: '/logout',
      name: 'logout',
      component: () => import('../views/LogoutView.vue'),
      meta: { public: true }
    },
    {
      path: '/calls/new',
      name: 'NewCall',
      component: () => import('../views/NewCallView.vue')
    },
    {
      path: '/knowledge-base',
      name: 'knowledge-base',
      component: KnowledgeBaseView,
      meta: { requiresAuth: true }
    },
    {
      path: '/knowledge-base/:id',
      name: 'knowledge-base-detail',
      component: KnowledgeBaseDetailView,
      meta: { requiresAuth: true }
    },
    {
      path: '/knowledge-base/new',
      name: 'new-knowledge-base',
      component: NewKnowledgeBaseView,
      meta: { requiresAuth: true }
    },
    {
      path: '/signup',
      name: 'signup',
      component: () => import('@/views/SignupView.vue'),
      meta: { public: true }
    }
  ]
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  
  if (to.meta.requiresAuth && !authStore.isAuthenticated) {
    next('/login')
  } else if (to.path === '/login' && authStore.isAuthenticated) {
    next('/')
  } else {
    next()
  }
})

export default router
