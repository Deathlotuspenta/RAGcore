import { createRouter, createWebHistory } from 'vue-router'
import { useAuthStore } from '../stores/auth'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: () => import('../views/LoginView.vue'),
    meta: { guest: true },
  },
  {
    path: '/register',
    name: 'register',
    component: () => import('../views/RegisterView.vue'),
    meta: { guest: true },
  },
  {
    path: '/',
    component: () => import('../views/AppLayout.vue'),
    meta: { requiresAuth: true },
    children: [
      { path: '', redirect: '/notes' },
      {
        path: 'notes',
        name: 'notes',
        component: () => import('../views/NotesListView.vue'),
      },
      {
        path: 'notes/new',
        name: 'note-new',
        component: () => import('../views/NoteEditView.vue'),
      },
      {
        path: 'notes/:id',
        name: 'note-edit',
        component: () => import('../views/NoteEditView.vue'),
      },
      {
        path: 'chat',
        name: 'chat',
        component: () => import('../views/ChatView.vue'),
      },
      {
        path: 'settings',
        name: 'settings',
        component: () => import('../views/SettingsView.vue'),
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach((to) => {
  const auth = useAuthStore()
  if (to.meta.requiresAuth && !auth.isLoggedIn) {
    return { name: 'login' }
  }
  if (to.meta.guest && auth.isLoggedIn) {
    return { name: 'notes' }
  }
})

export default router
