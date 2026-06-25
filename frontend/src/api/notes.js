import client from './client'

export function listNotes() {
  return client.get('/api/notes')
}

export function getNote(id) {
  return client.get(`/api/notes/${id}`)
}

export function createNote(data) {
  return client.post('/api/notes', data)
}

export function updateNote(id, data) {
  return client.put(`/api/notes/${id}`, data)
}

export function deleteNote(id) {
  return client.delete(`/api/notes/${id}`)
}

export function getImportFormats() {
  return client.get('/api/notes/import/formats')
}

export function uploadNote(file, title = '') {
  const form = new FormData()
  form.append('file', file)
  if (title) form.append('title', title)
  return client.post('/api/notes/upload', form, {
    headers: { 'Content-Type': 'multipart/form-data' },
  })
}
