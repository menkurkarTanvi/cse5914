export const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export function authHeaders(): HeadersInit {
  const token = localStorage.getItem('token')

  return {
    'Content-Type': 'application/json',
    ...(token
      ? { Authorization: `Bearer ${token}` }
      : {}),
  }
}
