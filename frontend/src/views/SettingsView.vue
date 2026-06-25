<script setup>
import { onMounted, ref } from 'vue'
import * as settingsApi from '../api/settings'

const modelName = ref('deepseek-chat')
const modelUrl = ref('https://api.deepseek.com/v1/chat/completions')
const apiKey = ref('')
const apiKeyMasked = ref('')
const apiKeySet = ref(false)
const loading = ref(false)
const saving = ref(false)
const error = ref('')
const status = ref('')

const presets = [
  {
    label: 'DeepSeek Chat',
    model_name: 'deepseek-chat',
    model_url: 'https://api.deepseek.com/v1/chat/completions',
  },
  {
    label: 'DeepSeek V3',
    model_name: 'deepseek-chat',
    model_url: 'https://api.deepseek.com/v1/chat/completions',
  },
]

async function load() {
  loading.value = true
  error.value = ''
  try {
    const { data } = await settingsApi.getLlmSettings()
    modelName.value = data.model_name
    modelUrl.value = data.model_url
    apiKeySet.value = data.api_key_set
    apiKeyMasked.value = data.api_key_masked
  } catch (e) {
    error.value = e.response?.data?.detail || '加载失败'
  } finally {
    loading.value = false
  }
}

function applyPreset(preset) {
  modelName.value = preset.model_name
  modelUrl.value = preset.model_url
}

async function save() {
  saving.value = true
  error.value = ''
  status.value = ''
  try {
    const payload = {
      model_name: modelName.value.trim(),
      model_url: modelUrl.value.trim(),
    }
    if (apiKey.value.trim()) {
      payload.api_key = apiKey.value.trim()
    }
    const { data } = await settingsApi.updateLlmSettings(payload)
    apiKeySet.value = data.api_key_set
    apiKeyMasked.value = data.api_key_masked
    apiKey.value = ''
    status.value = '已保存，下次问答将使用新配置'
  } catch (e) {
    error.value = e.response?.data?.detail || '保存失败'
  } finally {
    saving.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <h1>模型设置</h1>
    <p class="muted">切换 DeepSeek 模型名称或 API Key（保存在本机 backend/.env）</p>

    <div v-if="loading" class="muted">加载中…</div>
    <div v-else class="card form">
      <div class="presets">
        <span class="muted">快捷预设：</span>
        <button
          v-for="p in presets"
          :key="p.label"
          type="button"
          class="btn btn-outline btn-sm"
          @click="applyPreset(p)"
        >
          {{ p.label }}
        </button>
      </div>

      <div class="field">
        <label>模型名称</label>
        <input v-model="modelName" type="text" placeholder="deepseek-chat" />
      </div>
      <div class="field">
        <label>API 地址</label>
        <input v-model="modelUrl" type="url" />
      </div>
      <div class="field">
        <label>API Key</label>
        <input
          v-model="apiKey"
          type="password"
          :placeholder="apiKeySet ? `已配置 ${apiKeyMasked}` : 'sk-...'"
          autocomplete="off"
        />
        <p class="muted hint">留空则保持现有 Key 不变</p>
      </div>

      <p v-if="status" class="status">{{ status }}</p>
      <p v-if="error" class="error">{{ error }}</p>
      <button class="btn" :disabled="saving" @click="save">
        {{ saving ? '保存中…' : '保存' }}
      </button>
    </div>
  </div>
</template>

<style scoped>
h1 {
  margin: 0 0 0.25rem;
}
.form {
  margin-top: 1.25rem;
  max-width: 520px;
}
.presets {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 0.5rem;
  margin-bottom: 1rem;
}
.btn-sm {
  padding: 0.35rem 0.65rem;
  font-size: 0.8rem;
}
.hint {
  margin: 0.35rem 0 0;
  font-size: 0.8rem;
}
.status {
  color: #059669;
  font-size: 0.875rem;
}
</style>
