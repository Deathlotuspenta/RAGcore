import client from './client'

export function register(email, password) {
  return client.post('/api/auth/register', { email, password })
}

export function login(email, password) {
  return client.post('/api/auth/login', { email, password })
}

export function changePassword(currentPassword, newPassword) {
  return client.post('/api/auth/change-password', {
    current_password: currentPassword,
    new_password: newPassword,
  })
}
