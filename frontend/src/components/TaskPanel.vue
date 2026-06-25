<script setup>
import { onMounted, onUnmounted } from 'vue'
import { useRouter } from 'vue-router'
import { useTasksStore } from '../stores/tasks'

const router = useRouter()
const tasksStore = useTasksStore()

onMounted(async () => {
  await tasksStore.refresh()
  if (tasksStore.hasActive) {
    tasksStore.panelOpen = true
    tasksStore.startPolling()
  }
})

onUnmounted(() => {
  tasksStore.stopPolling()
})

function statusLabel(status) {
  const map = {
    pending: '排队中',
    running: '处理中',
    success: '完成',
    failed: '失败',
  }
  return map[status] || status
}

function openNote(task) {
  if (task.note_id) router.push(`/notes/${task.note_id}`)
}
</script>

<template>
  <div v-if="tasksStore.tasks.length" class="task-panel">
    <button
      class="task-toggle"
      type="button"
      :aria-expanded="tasksStore.panelOpen"
      @click="tasksStore.togglePanel()"
    >
      <span v-if="tasksStore.hasActive" class="spinner sm" />
      <span>后台任务</span>
      <span v-if="tasksStore.hasActive" class="count">({{ tasksStore.activeTasks.length }} 进行中)</span>
      <span class="chevron" :class="{ open: tasksStore.panelOpen }">›</span>
    </button>

    <Transition name="task-slide">
      <div v-show="tasksStore.panelOpen" class="task-list card">
        <div class="task-header">
          <h3>任务列表</h3>
          <button class="collapse-btn" type="button" @click="tasksStore.togglePanel()">收起</button>
        </div>
        <ul>
          <li v-for="task in tasksStore.tasks" :key="task.id" :class="task.status">
            <div class="row">
              <span v-if="task.status === 'pending' || task.status === 'running'" class="spinner sm" />
              <strong>{{ task.type_label }}</strong>
              <span class="badge">{{ statusLabel(task.status) }}</span>
            </div>
            <p class="title">{{ task.title }}</p>
            <p class="muted msg">{{ task.message }}</p>
            <p v-if="task.error" class="error">{{ task.error }}</p>
            <button
              v-if="task.status === 'success' && task.note_id"
              class="link-btn"
              type="button"
              @click="openNote(task)"
            >
              打开笔记
            </button>
          </li>
        </ul>
      </div>
    </Transition>
  </div>
</template>

<style scoped>
.task-panel {
  position: fixed;
  right: 1rem;
  bottom: 1rem;
  z-index: 100;
  max-width: 360px;
  width: calc(100% - 2rem);
  display: flex;
  flex-direction: column;
  align-items: flex-end;
}
.task-toggle {
  display: inline-flex;
  align-items: center;
  gap: 0.4rem;
  padding: 0.5rem 0.85rem;
  border-radius: 999px;
  border: 1px solid var(--border);
  background: #fff;
  box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  font-size: 0.875rem;
  cursor: pointer;
  transition: box-shadow 0.2s;
}
.task-toggle:hover {
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.12);
}
.count {
  color: var(--primary);
  font-size: 0.8rem;
}
.chevron {
  display: inline-block;
  font-size: 1.1rem;
  line-height: 1;
  transform: rotate(90deg);
  transition: transform 0.2s;
  color: var(--muted);
}
.chevron.open {
  transform: rotate(-90deg);
}
.task-list {
  margin-top: 0.5rem;
  width: 100%;
  max-height: 320px;
  overflow-y: auto;
  padding: 0.85rem;
}
.task-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.75rem;
}
.task-header h3 {
  margin: 0;
  font-size: 0.95rem;
}
.collapse-btn {
  padding: 0.2rem 0.55rem;
  border: 1px solid var(--border);
  border-radius: 6px;
  background: #f8fafc;
  color: #64748b;
  font-size: 0.75rem;
  cursor: pointer;
}
.collapse-btn:hover {
  background: #f1f5f9;
  color: #334155;
}
.task-list ul {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.task-list li {
  border-bottom: 1px solid var(--border);
  padding-bottom: 0.75rem;
}
.task-list li:last-child {
  border-bottom: none;
  padding-bottom: 0;
}
.row {
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.badge {
  margin-left: auto;
  font-size: 0.75rem;
  padding: 0.1rem 0.45rem;
  border-radius: 999px;
  background: #f1f5f9;
  color: #475569;
}
li.running .badge,
li.pending .badge {
  background: #eef2ff;
  color: var(--primary);
}
li.success .badge {
  background: #ecfdf5;
  color: #059669;
}
li.failed .badge {
  background: #fef2f2;
  color: var(--danger);
}
.title {
  margin: 0.25rem 0 0;
  font-size: 0.875rem;
}
.msg {
  margin: 0.15rem 0 0;
  font-size: 0.8rem;
}
.link-btn {
  margin-top: 0.35rem;
  padding: 0;
  border: none;
  background: none;
  color: var(--primary);
  font-size: 0.875rem;
  cursor: pointer;
}

.task-slide-enter-active,
.task-slide-leave-active {
  transition: opacity 0.2s, transform 0.2s;
  transform-origin: bottom right;
}
.task-slide-enter-from,
.task-slide-leave-to {
  opacity: 0;
  transform: translateY(8px) scale(0.98);
}
</style>
