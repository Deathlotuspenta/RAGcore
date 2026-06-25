import client from './client'

export function ask(question) {
  return client.post('/api/chat', { question })
}

function getAuthHeaders() {
  const token = localStorage.getItem('token')
  return token ? { Authorization: `Bearer ${token}` } : {}
}

/**
 * Stream RAG answer via SSE. Callbacks: onToken, onSources, onDone, onError.
 */
export async function askStream(question, { onToken, onSources, onDone, onError, signal }) {
  const res = await fetch('/api/chat/stream', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      ...getAuthHeaders(),
    },
    body: JSON.stringify({ question }),
    signal,
  })

  if (res.status === 401) {
    localStorage.removeItem('token')
    window.location.href = '/login'
    throw new Error('未登录')
  }

  if (!res.ok) {
    let detail = '问答失败'
    try {
      const body = await res.json()
      detail = body.detail || detail
    } catch {
      /* ignore */
    }
    throw new Error(detail)
  }

  const reader = res.body.getReader()
  const decoder = new TextDecoder()
  let buffer = ''

  while (true) {
    const { done, value } = await reader.read()
    if (done) break

    buffer += decoder.decode(value, { stream: true })
    const parts = buffer.split('\n\n')
    buffer = parts.pop() || ''

    for (const part of parts) {
      const line = part.trim()
      if (!line.startsWith('data: ')) continue
      let event
      try {
        event = JSON.parse(line.slice(6))
      } catch {
        continue
      }

      if (event.type === 'token') onToken?.(event.content)
      else if (event.type === 'sources') onSources?.(event.sources)
      else if (event.type === 'done') onDone?.()
      else if (event.type === 'error') onError?.(event.message)
    }
  }

  onDone?.()
}
