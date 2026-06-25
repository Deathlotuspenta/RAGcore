<script setup>
import { computed, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import * as notesApi from '../api/notes'
import { useTasksStore } from '../stores/tasks'

const route = useRoute()
const router = useRouter()
const tasksStore = useTasksStore()

const isNew = computed(() => route.name === 'note-new')
const noteId = computed(() => route.params.id)

const title = ref('')
const content = ref('')
const fileType = ref('md')
const loading = ref(false)
const submitting = ref(false)
const error = ref('')
const status = ref('')

async function load() {
  if (isNew.value) return
  loading.value = true
  error.value = ''
  try {
    const { data } = await notesApi.getNote(noteId.value)
    title.value = data.title
    content.value = data.content
    fileType.value = data.file_type
  } catch (e) {
    error.value = e.response?.data?.detail || '加载失败'
  } finally {
    loading.value = false
  }
}

async function save() {
  submitting.value = true
  error.value = ''
  status.value = ''
  try {
    const payload = {
      title: title.value,
      content: content.value,
      file_type: fileType.value,
    }
    if (isNew.value) {
      const { data } = await notesApi.createNote(payload)
      tasksStore.trackTask(data.task_id)
      router.push('/notes')
    } else {
      const { data } = await notesApi.updateNote(noteId.value, payload)
      tasksStore.trackTask(data.task_id)
      status.value = data.message
    }
  } catch (e) {
    error.value = e.response?.data?.detail || '保存失败'
  } finally {
    submitting.value = false
  }
}

onMounted(load)
watch(() => route.params.id, load)
</script>

<template>
  <div>
    <div v-if="submitting" class="overlay-loading">
      <span class="spinner lg" />
      <p class="muted">正在提交…</p>
    </div>

    <div class="toolbar">
      <button class="btn btn-outline" @click="router.push('/notes')">← 返回</button>
      <h1>{{ isNew ? '新建笔记' : '编辑笔记' }}</h1>
      <button class="btn" :disabled="submitting || !title || !content" @click="save">
        <span v-if="submitting" class="spinner sm" />
        {{ submitting ? '提交中…' : '保存' }}
      </button>
    </div>

    <p v-if="loading" class="muted">加载中…</p>
    <div v-else class="card editor">
      <div class="field">
        <label>标题</label>
        <input v-model="title" type="text" required :disabled="submitting" />
      </div>
      <div class="field">
        <label>类型</label>
        <select v-model="fileType" :disabled="submitting">
          <option value="md">Markdown</option>
          <option value="txt">纯文本</option>
        </select>
      </div>
      <div class="field">
        <label>正文（Markdown）</label>
        <textarea
          v-model="content"
          placeholder="# 标题&#10;&#10;在这里写笔记内容…"
          :disabled="submitting"
        />
      </div>
      <p v-if="status" class="status">{{ status }}</p>
      <p v-if="error" class="error">{{ error }}</p>
      <p v-if="status" class="muted hint">向量化在后台进行，可在右下角「后台任务」查看进度。</p>
    </div>
  </div>
</template>

<style scoped>
.toolbar {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.25rem;
}
h1 {
  margin: 0;
  flex: 1;
  font-size: 1.35rem;
}
select {
  padding: 0.55rem 0.75rem;
  border: 1px solid var(--border);
  border-radius: 8px;
}
.status {
  color: #059669;
  font-size: 0.875rem;
}
.hint {
  margin-top: 0.35rem;
  font-size: 0.8rem;
}
.btn .spinner {
  margin-right: 0.35rem;
}
</style>
