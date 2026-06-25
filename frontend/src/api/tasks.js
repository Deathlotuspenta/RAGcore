import client from './client'

export function listTasks() {
  return client.get('/api/tasks')
}

export function getTask(id) {
  return client.get(`/api/tasks/${id}`)
}
