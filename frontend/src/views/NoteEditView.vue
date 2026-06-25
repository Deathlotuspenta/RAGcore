<script setup>
import { computed, nextTick, onBeforeUnmount, onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import Vditor from 'vditor'
import 'vditor/dist/index.css'
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
const textareaRef = ref(null)
const editorHost = ref(null)
const editorFullscreen = ref(false)

const NORMAL_EDITOR_HEIGHT = 460

let vditor = null
const editorReady = ref(false)

function destroyEditor() {
  if (vditor) {
    vditor.destroy()
    vditor = null
    editorReady.value = false
  }
}

async function initEditor() {
  if (fileType.value !== 'md' || !editorHost.value) return
  destroyEditor()
  await nextTick()

  vditor = new Vditor(editorHost.value, {
    mode: 'ir',
    lang: 'zh_CN',
    cdn: '/vditor',
    placeholder: '# 标题\n\n输入 ## 你好 等 Markdown，此处即时显示效果',
    cache: { enable: false },
    height: NORMAL_EDITOR_HEIGHT,
    toolbar: [
      'headings',
      'bold',
      'italic',
      'strike',
      '|',
      'list',
      'ordered-list',
      'check',
      '|',
      'quote',
      'code',
      'inline-code',
      '|',
      'link',
      'table',
      '|',
      'undo',
      'redo',
    ],
    value: content.value,
    input: (val) => {
      content.value = val
    },
    after: () => {
      editorReady.value = true
      if (submitting.value) vditor.disabled()
      applyEditorLayout()
    },
  })
}

function syncContentFromEditor() {
  if (vditor && editorReady.value && fileType.value === 'md') {
    content.value = vditor.getValue()
  }
}

function resizeTextarea() {
  // 正文使用固定高度 + 滚动条，不再随内容增长
}

function applyEditorLayout() {
  if (!vditor || !editorReady.value || !editorHost.value) return
  const root = editorHost.value.querySelector('.vditor')
  if (!root) return
  if (editorFullscreen.value) {
    root.style.height = '100%'
  } else {
    root.style.height = `${NORMAL_EDITOR_HEIGHT}px`
  }
}

function setEditorFullscreen(on) {
  editorFullscreen.value = on
  document.body.style.overflow = on ? 'hidden' : ''
  nextTick(applyEditorLayout)
}

function toggleEditorFullscreen() {
  setEditorFullscreen(!editorFullscreen.value)
}

function onFullscreenKey(e) {
  if (e.key === 'Escape' && editorFullscreen.value) {
    setEditorFullscreen(false)
  }
}

async function load() {
  if (isNew.value) {
    title.value = ''
    content.value = ''
    fileType.value = 'md'
    return
  }
  loading.value = true
  error.value = ''
  try {
    const { data } = await notesApi.getNote(noteId.value)
    title.value = data.title
    content.value = data.content
    fileType.value = data.file_type
    await nextTick()
    if (fileType.value === 'md' && vditor && editorReady.value) {
      vditor.setValue(content.value || '')
    } else if (fileType.value === 'txt') {
      resizeTextarea()
    }
  } catch (e) {
    error.value = e.response?.data?.detail || '加载失败'
  } finally {
    loading.value = false
  }
}

async function save() {
  syncContentFromEditor()
  if (!title.value.trim() || !content.value.trim()) {
    error.value = '请填写标题和正文'
    return
  }

  submitting.value = true
  error.value = ''
  status.value = ''
  try {
    const payload = {
      title: title.value.trim(),
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

watch(content, () => {
  if (fileType.value === 'txt') nextTick(resizeTextarea)
})

watch(fileType, async (type) => {
  if (type === 'md') {
    await initEditor()
  } else {
    syncContentFromEditor()
    destroyEditor()
    await nextTick()
    resizeTextarea()
  }
})

watch(submitting, (disabled) => {
  if (vditor && editorReady.value) {
    disabled ? vditor.disabled() : vditor.enable()
  }
})

watch(() => route.params.id, async () => {
  await load()
  if (fileType.value === 'md') {
    if (vditor && editorReady.value) {
      vditor.setValue(content.value || '')
    } else {
      await initEditor()
    }
  }
})

onMounted(async () => {
  window.addEventListener('keydown', onFullscreenKey)
  await load()
  if (fileType.value === 'md') await initEditor()
})

onBeforeUnmount(() => {
  window.removeEventListener('keydown', onFullscreenKey)
  document.body.style.overflow = ''
  destroyEditor()
})
</script>

<template>
  <div class="page">
    <div v-if="submitting" class="overlay-loading">
      <span class="spinner lg" />
      <p class="muted">正在提交…</p>
    </div>

    <div class="toolbar">
      <button type="button" class="btn btn-outline" @click="router.push('/notes')">
        ← 返回
      </button>
      <h1>{{ isNew ? '新建笔记' : '编辑笔记' }}</h1>
      <button
        type="button"
        class="btn"
        :disabled="submitting || !title.trim() || !content.trim()"
        @click="save"
      >
        <span v-if="submitting" class="spinner sm" />
        {{ submitting ? '提交中…' : '保存' }}
      </button>
    </div>

    <p v-if="loading" class="muted">加载中…</p>
    <div v-else class="card editor-card">
      <div class="meta-row">
        <div class="field title-field">
          <label for="note-title">标题</label>
          <input
            id="note-title"
            v-model="title"
            type="text"
            placeholder="笔记标题"
            :disabled="submitting"
          />
        </div>
        <div class="field type-field">
          <label for="note-type">类型</label>
          <select id="note-type" v-model="fileType" :disabled="submitting">
            <option value="md">Markdown</option>
            <option value="txt">纯文本</option>
          </select>
        </div>
      </div>

      <section
        class="editor-section"
        :class="{ 'is-fullscreen': editorFullscreen }"
        aria-label="正文"
      >
        <div class="section-header">
          <div>
            <label class="section-label">正文</label>
            <p v-if="fileType === 'md' && !editorFullscreen" class="section-hint muted">
              同一编辑框内即时渲染，输入 <code>## 你好</code> 会直接显示为标题
            </p>
            <p v-else-if="!editorFullscreen" class="section-hint muted">纯文本模式，不做 Markdown 渲染</p>
          </div>
          <button
            type="button"
            class="btn btn-outline btn-sm fullscreen-btn"
            :title="editorFullscreen ? '退出全屏 (Esc)' : '全屏编辑'"
            @click="toggleEditorFullscreen"
          >
            {{ editorFullscreen ? '缩小' : '全屏' }}
          </button>
        </div>

        <div
          v-if="editorFullscreen"
          class="fullscreen-topbar"
        >
          <span class="fullscreen-title">{{ title.trim() || '未命名笔记' }}</span>
          <span class="muted fullscreen-hint">Esc 或点「缩小」退出全屏</span>
        </div>

        <div
          class="editor-unified"
          :class="{ 'is-txt': fileType === 'txt', 'is-md': fileType === 'md', 'is-fullscreen': editorFullscreen }"
        >
          <div v-if="fileType === 'md' && !editorReady" class="editor-loading">
            <span class="spinner" />
            <span class="muted">编辑器加载中…</span>
          </div>
          <div v-show="fileType === 'md'" ref="editorHost" class="vditor-host" />
          <textarea
            v-show="fileType === 'txt'"
            id="note-content"
            ref="textareaRef"
            v-model="content"
            class="editor-input"
            placeholder="在这里写纯文本…"
            :disabled="submitting"
            spellcheck="false"
            @input="resizeTextarea"
          />
        </div>
      </section>

      <p v-if="status" class="status">{{ status }}</p>
      <p v-if="error" class="error">{{ error }}</p>
      <p v-if="status" class="muted hint">向量化在后台进行，可在右下角「后台任务」查看进度。</p>
    </div>
  </div>
</template>

<style scoped>
.page {
  max-width: 820px;
  margin: 0 auto;
}

.toolbar {
  display: flex;
  align-items: center;
  gap: 1rem;
  margin-bottom: 1.25rem;
  flex-wrap: wrap;
}

h1 {
  margin: 0;
  flex: 1;
  font-size: 1.35rem;
  font-weight: 600;
  color: #0f172a;
}

.editor-card {
  padding: 1.25rem 1.35rem 1.5rem;
}

.meta-row {
  display: grid;
  grid-template-columns: 1fr 160px;
  gap: 1rem;
  margin-bottom: 1.25rem;
}

.meta-row .field {
  margin-bottom: 0;
}

.section-label {
  display: block;
  font-size: 0.875rem;
  font-weight: 600;
  color: #334155;
  margin-bottom: 0.25rem;
}

.section-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 0.75rem;
  margin-bottom: 0.65rem;
}

.fullscreen-btn {
  flex-shrink: 0;
  margin-top: 0.1rem;
}

.section-hint {
  margin: 0;
  font-size: 0.8rem;
}

.section-hint code {
  font-size: 0.85em;
  padding: 0.1em 0.35em;
  border-radius: 4px;
  background: #f1f5f9;
  color: #475569;
}

.editor-unified {
  position: relative;
  border: 1px solid var(--border);
  border-radius: 10px;
  overflow: hidden;
  background: #fff;
  box-shadow: inset 0 1px 2px rgba(15, 23, 42, 0.03);
  transition: border-color 0.2s var(--ease), box-shadow 0.2s var(--ease);
}

.editor-section.is-fullscreen {
  position: fixed;
  inset: 0;
  z-index: 300;
  margin: 0;
  padding: 1rem 1.25rem 1.25rem;
  background: #f8fafc;
  display: flex;
  flex-direction: column;
  box-sizing: border-box;
}

.editor-section.is-fullscreen .section-header {
  flex-shrink: 0;
  margin-bottom: 0.5rem;
}

.fullscreen-topbar {
  flex-shrink: 0;
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 1rem;
  margin-bottom: 0.65rem;
  padding: 0.5rem 0.75rem;
  border-radius: 8px;
  background: #fff;
  border: 1px solid var(--border);
}

.fullscreen-title {
  font-weight: 600;
  color: #0f172a;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.fullscreen-hint {
  font-size: 0.8rem;
  flex-shrink: 0;
}

.editor-unified.is-fullscreen {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.editor-unified.is-fullscreen .vditor-host {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
}

.editor-unified.is-fullscreen .editor-input {
  height: 100%;
  flex: 1;
  min-height: 0;
}

.editor-loading {
  position: absolute;
  inset: 0;
  z-index: 2;
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 0.6rem;
  background: #fff;
}

.editor-unified:focus-within {
  border-color: var(--primary);
  box-shadow: 0 0 0 3px rgba(79, 70, 229, 0.1);
}

.vditor-host :deep(.vditor) {
  border: none;
  border-radius: 0;
}

.editor-unified.is-fullscreen .vditor-host :deep(.vditor) {
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  height: 100% !important;
}

.editor-unified.is-fullscreen .vditor-host :deep(.vditor-content) {
  flex: 1;
  min-height: 0;
}

.vditor-host :deep(.vditor-toolbar) {
  border-bottom: 1px solid var(--border);
  background: #f8fafc;
  padding-left: 0.35rem;
  padding-right: 0.35rem;
}

.vditor-host :deep(.vditor-content) {
  overflow-y: auto;
}

.vditor-host :deep(.vditor-ir) {
  padding: 0.85rem 1rem 1.1rem;
  font-size: 0.95rem;
  line-height: 1.7;
}

.vditor-host :deep(.vditor-ir pre.vditor-reset) {
  background: transparent;
}

.editor-input {
  display: block;
  width: 100%;
  height: 460px;
  padding: 1rem 1.1rem;
  border: none;
  resize: none;
  overflow-y: auto;
  background: #fff;
  font-family: ui-sans-serif, system-ui, sans-serif;
  font-size: 0.95rem;
  line-height: 1.7;
  color: #334155;
}

.editor-input:focus {
  outline: none;
}

.editor-input:disabled {
  background: var(--surface-muted);
  color: var(--muted);
}

.hint {
  margin-top: 0.35rem;
  font-size: 0.8rem;
}

.btn .spinner {
  margin-right: 0.35rem;
}

.btn-sm {
  padding: 0.35rem 0.75rem;
  font-size: 0.875rem;
}

@media (max-width: 640px) {
  .meta-row {
    grid-template-columns: 1fr;
  }
}
</style>
