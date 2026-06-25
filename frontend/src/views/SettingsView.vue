<script setup>
import { onMounted, ref } from 'vue'
import * as authApi from '../api/auth'
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

const currentPassword = ref('')
const newPassword = ref('')
const confirmPassword = ref('')
const savingPassword = ref(false)
const passwordError = ref('')
const passwordStatus = ref('')

const presets = [
  {
    label: 'DeepSeek Chat',
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

async function savePassword() {
  passwordError.value = ''
  passwordStatus.value = ''

  if (newPassword.value.length < 6) {
    passwordError.value = '新密码至少 6 位'
    return
  }
  if (newPassword.value !== confirmPassword.value) {
    passwordError.value = '两次输入的新密码不一致'
    return
  }

  savingPassword.value = true
  try {
    const { data } = await authApi.changePassword(
      currentPassword.value,
      newPassword.value
    )
    currentPassword.value = ''
    newPassword.value = ''
    confirmPassword.value = ''
    passwordStatus.value = data.message || '密码已更新'
  } catch (e) {
    passwordError.value = e.response?.data?.detail || '修改失败'
  } finally {
    savingPassword.value = false
  }
}

onMounted(load)
</script>

<template>
  <div>
    <h1>设置</h1>
    <p class="muted">账号与模型配置</p>

    <div class="card form">
      <h2>修改密码</h2>
      <div class="field">
        <label>当前密码</label>
        <input
          v-model="currentPassword"
          type="password"
          autocomplete="current-password"
        />
      </div>
      <div class="field">
        <label>新密码</label>
        <input
          v-model="newPassword"
          type="password"
          autocomplete="new-password"
          placeholder="至少 6 位"
        />
      </div>
      <div class="field">
        <label>确认新密码</label>
        <input
          v-model="confirmPassword"
          type="password"
          autocomplete="new-password"
        />
      </div>
      <p v-if="passwordStatus" class="status">{{ passwordStatus }}</p>
      <p v-if="passwordError" class="error">{{ passwordError }}</p>
      <button
        class="btn"
        :disabled="savingPassword || !currentPassword || !newPassword || !confirmPassword"
        @click="savePassword"
      >
        {{ savingPassword ? '保存中…' : '更新密码' }}
      </button>
    </div>

    <div v-if="loading" class="muted section">加载中…</div>
    <div v-else class="card form section">
      <h2>LLM 问答</h2>
      <p class="muted hint">DeepSeek 模型与 API Key（保存在本机数据目录 .env）</p>
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
.section {
  margin-top: 1.25rem;
}
h2 {
  margin: 0 0 0.75rem;
  font-size: 1.1rem;
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
.field {
  margin-bottom: 1rem;
}
.field label {
  display: block;
  margin-bottom: 0.35rem;
  font-size: 0.875rem;
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
