<script setup>
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../stores/auth'
import TaskPanel from '../components/TaskPanel.vue'
import OnboardingTour from '../components/OnboardingTour.vue'

const router = useRouter()
const auth = useAuthStore()

const TOUR_KEY = 'ragcore_onboarding_done'
const showTour = ref(false)

const tourSteps = [
  {
    target: null,
    title: '欢迎使用 RAGcore',
    text: '这是你的个人笔记知识库。只需 3 步即可开始：配置 AI、导入笔记、开始问答。点「下一步」跟着引导走。',
  },
  {
    target: '[data-tour="settings"]',
    title: '1. 先到「设置」填 API Key',
    text: '问答需要 DeepSeek 大模型。进入设置，粘贴你的 API Key（默认模型 deepseek-v4-flash），保存即可。',
  },
  {
    target: '[data-tour="notes"]',
    title: '2. 在「笔记」导入内容',
    text: '新建笔记，或批量导入 .md / .txt / .pdf 文件。导入后会自动切块并向量化，首次约需 30 秒。',
  },
  {
    target: '[data-tour="chat"]',
    title: '3. 到「问答」开始提问',
    text: 'AI 会检索你的笔记并给出带来源的回答。试着问：「总结一下我的笔记要点」。',
  },
  {
    target: '[data-tour="help"]',
    title: '随时可重看引导',
    text: '需要再看一遍时，点这里的「新手引导」即可重新开始。祝使用愉快！',
  },
]

function startTour() {
  showTour.value = true
}
function finishTour() {
  localStorage.setItem(TOUR_KEY, '1')
}

function logout() {
  auth.logout()
  router.push('/login')
}

onMounted(() => {
  if (!localStorage.getItem(TOUR_KEY)) {
    setTimeout(() => {
      showTour.value = true
    }, 400)
  }
})
</script>

<template>
  <div class="layout">
    <header class="header">
      <div class="container header-inner">
        <router-link to="/notes" class="brand">Notes RAG</router-link>
        <nav>
          <router-link to="/notes" data-tour="notes">笔记</router-link>
          <router-link to="/chat" data-tour="chat">问答</router-link>
          <router-link to="/settings" data-tour="settings">设置</router-link>
        </nav>
        <div class="user">
          <button
            type="button"
            class="btn btn-outline btn-sm"
            data-tour="help"
            @click="startTour"
          >
            新手引导
          </button>
          <span class="muted">{{ auth.email }}</span>
          <button type="button" class="btn btn-outline btn-sm" @click="logout">退出</button>
        </div>
      </div>
    </header>
    <main class="container main">
      <router-view />
    </main>
    <TaskPanel />

    <OnboardingTour
      v-model="showTour"
      :steps="tourSteps"
      @finish="finishTour"
      @skip="finishTour"
    />
  </div>
</template>

<style scoped>
.layout {
  min-height: 100vh;
}
.header {
  background: rgba(255, 255, 255, 0.92);
  backdrop-filter: blur(8px);
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
