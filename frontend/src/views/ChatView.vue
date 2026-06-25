<script setup>
import DOMPurify from 'dompurify'
import { marked } from 'marked'
import { computed, onUnmounted, ref } from 'vue'
import { useRouter } from 'vue-router'
import * as chatApi from '../api/chat'

marked.setOptions({ breaks: true, gfm: true })

const router = useRouter()

const question = ref('')
const answer = ref('')
const sources = ref([])
const loading = ref(false)
const streaming = ref(false)
const error = ref('')
const previewSource = ref(null)

let abortController = null

const answerHtml = computed(() => {
  if (!answer.value) return ''
  const raw = marked.parse(answer.value)
  return DOMPurify.sanitize(raw)
})

const previewHtml = computed(() => {
  const text = previewSource.value?.content || previewSource.value?.excerpt || ''
  if (!text) return ''
  const raw = marked.parse(text)
  return DOMPurify.sanitize(raw)
})

function openPreview(source) {
  previewSource.value = source
}

function closePreview() {
  previewSource.value = null
}

function openNote(noteId) {
  closePreview()
  router.push(`/notes/${noteId}`)
}

async function submit() {
  if (!question.value.trim() || loading.value) return

  abortController?.abort()
  abortController = new AbortController()

  loading.value = true
  streaming.value = false
  error.value = ''
  answer.value = ''
  sources.value = []
  previewSource.value = null

  try {
    await chatApi.askStream(question.value.trim(), {
      signal: abortController.signal,
      onToken: (chunk) => {
        streaming.value = true
        answer.value += chunk
      },
      onSources: (items) => {
        sources.value = items || []
      },
      onError: (msg) => {
        error.value = msg || '生成失败'
      },
    })
  } catch (e) {
    if (e.name !== 'AbortError') {
      error.value = e.message || '问答失败，请确认后端已启动'
    }
  } finally {
    loading.value = false
    streaming.value = false
  }
}

onUnmounted(() => {
  abortController?.abort()
})
</script>

<template>
  <div>
    <h1>RAG 问答</h1>
    <p class="muted">根据你的笔记检索并生成回答（仅搜索当前账号下的内容）</p>

    <div class="card chat-form">
      <div class="field">
        <label>问题</label>
        <textarea
          v-model="question"
          rows="3"
          placeholder="例如：什么是 RAG？"
          :disabled="loading"
          @keydown.ctrl.enter="submit"
        />
      </div>
      <button type="button" class="btn" :disabled="loading || !question.trim()" @click="submit">
        <span v-if="loading && !answer" class="spinner sm" />
        {{ loading && !answer ? '检索中…' : loading ? '生成中…' : '提问' }}
      </button>
      <p class="muted hint">Ctrl + Enter 提交</p>
    </div>

    <p v-if="error" class="error">{{ error }}</p>

    <div v-if="answer || (loading && streaming)" class="card answer">
      <h2>
        回答
        <span v-if="streaming" class="streaming-dot" />
      </h2>
      <div class="answer-body markdown-body" v-html="answerHtml" />
    </div>

    <div v-if="sources.length" class="card sources">
      <h2>引用来源</h2>
      <ul>
        <li v-for="(s, i) in sources" :key="i">
          <div class="source-head">
            <button class="source-title" type="button" @click="openPreview(s)">
              {{ s.note_title }}
            </button>
            <span class="muted meta">
              块 {{ s.chunk_index + 1 }}
              <span v-if="s.score != null"> · 相关度 {{ s.score }}</span>
            </span>
          </div>
          <p class="excerpt">{{ s.excerpt }}…</p>
          <button class="link-btn" type="button" @click="openPreview(s)">查看原文</button>
        </li>
      </ul>
    </div>

    <Teleport to="body">
      <div v-if="previewSource" class="source-overlay" @click.self="closePreview">
        <div class="source-modal card">
          <div class="modal-head">
            <div>
              <h3>{{ previewSource.note_title }}</h3>
              <p class="muted">
                引用块 {{ previewSource.chunk_index + 1 }}
                <span v-if="previewSource.score != null">
                  · 相关度 {{ previewSource.score }}
                </span>
              </p>
            </div>
            <button class="close-btn" type="button" aria-label="关闭" @click="closePreview">
              ×
            </button>
          </div>
          <div class="modal-body markdown-body" v-html="previewHtml" />
          <div class="modal-foot">
            <button class="btn btn-outline" type="button" @click="closePreview">关闭</button>
            <button
              class="btn"
              type="button"
              @click="openNote(previewSource.note_id)"
            >
              打开完整笔记
            </button>
          </div>
        </div>
      </div>
    </Teleport>
  </div>
</template>

<style scoped>
h1 {
  margin: 0 0 0.25rem;
}
.chat-form {
  margin: 1.25rem 0;
}
.chat-form textarea {
  min-height: 80px;
  font-family: inherit;
}
.hint {
  margin: 0.5rem 0 0;
}
.btn .spinner {
  margin-right: 0.35rem;
}
.answer,
.sources {
  margin-top: 1rem;
}
h2 {
  margin: 0 0 0.75rem;
  font-size: 1.1rem;
  display: flex;
  align-items: center;
  gap: 0.5rem;
}
.streaming-dot {
  display: inline-block;
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: var(--primary);
  animation: pulse 1s ease-in-out infinite;
}
@keyframes pulse {
  0%,
  100% {
    opacity: 0.3;
  }
  50% {
    opacity: 1;
  }
}
.answer-body {
  line-height: 1.7;
}
.sources ul {
  margin: 0;
  padding: 0;
  list-style: none;
}
.sources li {
  padding: 0.75rem 0;
  border-bottom: 1px solid var(--border);
}
.sources li:last-child {
  border-bottom: none;
}
.source-head {
  display: flex;
  align-items: baseline;
  flex-wrap: wrap;
  gap: 0.35rem 0.75rem;
}
.source-title {
  padding: 0;
  border: none;
  background: none;
  font-weight: 600;
  font-size: 1rem;
  color: var(--primary);
  cursor: pointer;
  text-align: left;
}
.source-title:hover {
  text-decoration: underline;
}
.meta {
  font-size: 0.8rem;
}
.excerpt {
  margin: 0.35rem 0 0;
  color: var(--muted);
  font-size: 0.875rem;
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
.link-btn:hover {
  text-decoration: underline;
}

.source-overlay {
  position: fixed;
  inset: 0;
  z-index: 300;
  background: rgba(15, 23, 42, 0.45);
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 1rem;
}
.source-modal {
  width: min(720px, 100%);
  max-height: min(85vh, 900px);
  display: flex;
  flex-direction: column;
  padding: 0;
  overflow: hidden;
}
.modal-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 1rem;
  padding: 1rem 1.25rem;
  border-bottom: 1px solid var(--border);
}
.modal-head h3 {
  margin: 0;
  font-size: 1.05rem;
}
.modal-head p {
  margin: 0.25rem 0 0;
  font-size: 0.8rem;
}
.close-btn {
  width: 2rem;
  height: 2rem;
  border: none;
  border-radius: 8px;
  background: #f1f5f9;
  color: #64748b;
  font-size: 1.25rem;
  line-height: 1;
  cursor: pointer;
  flex-shrink: 0;
}
.close-btn:hover {
  background: #e2e8f0;
  color: #334155;
}
.modal-body {
  flex: 1;
  overflow-y: auto;
  padding: 1rem 1.25rem;
  line-height: 1.7;
}
.modal-foot {
  display: flex;
  justify-content: flex-end;
  gap: 0.5rem;
  padding: 0.85rem 1.25rem;
  border-top: 1px solid var(--border);
}
</style>
