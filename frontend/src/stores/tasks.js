import { defineStore } from 'pinia'
import { computed, ref } from 'vue'
import * as tasksApi from '../api/tasks'

export const useTasksStore = defineStore('tasks', () => {
  const tasks = ref([])
  const panelOpen = ref(false)
  let pollTimer = null

  const activeTasks = computed(() =>
    tasks.value.filter((t) => t.status === 'pending' || t.status === 'running')
  )

  const hasActive = computed(() => activeTasks.value.length > 0)

  async function refresh() {
    const { data } = await tasksApi.listTasks()
    tasks.value = data
  }

  function trackTask() {
    panelOpen.value = true
    refresh()
    startPolling()
  }

  function startPolling() {
    if (pollTimer) return
    pollTimer = setInterval(async () => {
      await refresh()
      if (!hasActive.value) stopPolling()
    }, 2000)
  }

  function stopPolling() {
    if (pollTimer) {
      clearInterval(pollTimer)
      pollTimer = null
    }
  }

  function togglePanel() {
    panelOpen.value = !panelOpen.value
  }

  return {
    tasks,
    panelOpen,
    activeTasks,
    hasActive,
    refresh,
    trackTask,
    startPolling,
    stopPolling,
    togglePanel,
  }
})
