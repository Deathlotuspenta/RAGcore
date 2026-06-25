<script setup>
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import TaskPanel from '../components/TaskPanel.vue'

const router = useRouter()
const auth = useAuthStore()

function logout() {
  auth.logout()
  router.push('/login')
}
</script>

<template>
  <div class="layout">
    <header class="header">
      <div class="container header-inner">
        <router-link to="/notes" class="brand">Notes RAG</router-link>
        <nav>
          <router-link to="/notes">笔记</router-link>
          <router-link to="/chat">问答</router-link>
          <router-link to="/settings">设置</router-link>
        </nav>
        <div class="user">
          <span class="muted">{{ auth.email }}</span>
          <button class="btn btn-outline btn-sm" @click="logout">退出</button>
        </div>
      </div>
    </header>
    <main class="container main">
      <router-view />
    </main>
    <TaskPanel />
  </div>
</template>

<style scoped>
.layout {
  min-height: 100vh;
}
.header {
  background: #fff;
  border-bottom: 1px solid var(--border);
  position: sticky;
  top: 0;
  z-index: 10;
}
.header-inner {
  display: flex;
  align-items: center;
  gap: 1.5rem;
  height: 56px;
}
.brand {
  font-weight: 700;
  color: #1e293b;
  margin-right: auto;
}
nav {
  display: flex;
  gap: 1rem;
}
nav a {
  color: #475569;
  font-weight: 500;
}
nav a.router-link-active {
  color: var(--primary);
}
.user {
  display: flex;
  align-items: center;
  gap: 0.75rem;
}
.btn-sm {
  padding: 0.35rem 0.75rem;
  font-size: 0.875rem;
}
.main {
  padding: 1.5rem 1rem 3rem;
}
</style>
