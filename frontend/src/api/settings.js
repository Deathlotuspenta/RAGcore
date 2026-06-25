import client from './client'

export function getLlmSettings() {
  return client.get('/api/settings/llm')
}

export function updateLlmSettings(data) {
  return client.put('/api/settings/llm', data)
}
