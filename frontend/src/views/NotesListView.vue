<script setup>
import { onMounted, onUnmounted, ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import * as notesApi from '../api/notes'
import { useTasksStore } from '../stores/tasks'

const router = useRouter()
const tasksStore = useTasksStore()
const notes = ref([])
const loading = ref(true)
const error = ref('')
const importHint = ref('')
const submitting = ref(false)
const fileInput = ref(null)
let notesPoll = null

async function load(silent = false) {
  if (!silent) loading.value = true
  error.value = ''
  try {
    const [listRes, fmtRes] = await Promise.all([
      notesApi.listNotes(),
      notesApi.getImportFormats(),
    ])
    notes.value = listRes.data
    importHint.value = fmtRes.data.message
  } catch (e) {
    if (!silent) error.value = e.response?.data?.detail || '加载失败'
  } finally {
    if (!silent) loading.value = false
  }
}

async function remove(id) {
  if (!confirm('确定删除这篇笔记？')) return
  await notesApi.deleteNote(id)
  await load()
}

function pickFile() {
  fileInput.value?.click()
}

async function onFileChange(event) {
  const file = event.target.files?.[0]
  event.target.value = ''
  if (!file) return

  submitting.value = true
  error.value = ''
  try {
    const { data } = await notesApi.uploadNote(file)
    tasksStore.trackTask(data.task_id)
  } catch (e) {
    error.value = e.response?.data?.detail || '导入失败'
  } finally {
    submitting.value = false
  }
}

watch(
  () => tasksStore.hasActive,
  (active) => {
    if (active) {
      if (!notesPoll) notesPoll = setInterval(() => load(true), 3000)
    } else if (notesPoll) {
      clearInterval(notesPoll)
      notesPoll = null
      load()
    }
  },
  { immediate: true }
)

onMounted(load)
onUnmounted(() => {
  if (notesPoll) clearInterval(notesPoll)
})
</script>

<template>
  <div>
    <div v-if="submitting" class="overlay-loading">
      <span class="spinner lg" />
      <p class="muted">正在上传并提交任务…</p>
    </div>

    <div class="toolbar">
      <h1>我的笔记</h1>
      <div class="actions">
        <input
          ref="fileInput"
          type="file"
          class="hidden-input"
          accept=".md,.markdown,.txt,.pdf"
          @change="onFileChange"
        />
        <button class="btn btn-outline" :disabled="submitting" @click="pickFile">
          <span v-if="submitting" class="spinner sm" />
          {{ submitting ? '提交中…' : '导入文件' }}
        </button>
        <button class="btn" @click="router.push('/notes/new')">新建笔记</button>
      </div>
    </div>

    <p v-if="importHint" class="muted hint">{{ importHint }}</p>

    <p v-if="loading" class="muted">加载中…</p>
    <p v-else-if="error" class="error">{{ error }}</p>

    <div v-else-if="notes.length === 0" class="card empty">
      <p>还没有笔记，可「新建笔记」或「导入文件」（.md / .txt / .pdf）。</p>
    </div>

    <ul v-else class="note-list">
      <li v-for="note in notes" :key="note.id" class="card note-item">
        <div class="info" @click="router.push(`/notes/${note.id}`)">
          <h3>{{ note.title }}</h3>
          <p class="muted">
            {{ note.chunk_count }} 块 · {{ note.file_type }} ·
            {{ new Date(note.updated_at).toLocaleString() }}
          </p>
        </div>
        <button class="btn btn-outline btn-sm" @click="remove(note.id)">删除</button>
      </li>
    </ul>
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 0.5rem;
  gap: 1rem;
  flex-wrap: wrap;
}
.actions {
  display: flex;
  gap: 0.5rem;
}
.hidden-input {
  display: none;
}
.hint {
  margin: 0 0 1rem;
}
h1 {
  margin: 0;
  font-size: 1.5rem;
}
.empty {
  text-align: center;
  color: var(--muted);
}
.note-list {
  list-style: none;
  padding: 0;
  margin: 0;
  display: flex;
  flex-direction: column;
  gap: 0.75rem;
}
.note-item {
  display: flex;
  align-items: center;
  gap: 1rem;
}
.info {
  flex: 1;
  cursor: pointer;
}
.info h3 {
  margin: 0 0 0.25rem;
  font-size: 1.05rem;
}
.btn-sm {
  padding: 0.35rem 0.75rem;
  font-size: 0.875rem;
}
.btn .spinner {
  margin-right: 0.25rem;
}
</style>
