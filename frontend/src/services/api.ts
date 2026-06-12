import axios from 'axios'

const API_BASE = '/api/v1'

const api = axios.create({
  baseURL: API_BASE,
  timeout: 30000,
  headers: { 'Content-Type': 'application/json' },
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

api.interceptors.response.use(
  (res) => res,
  async (error) => {
    const original = error.config
    if (error.response?.status === 401 && !original._retry) {
      original._retry = true
      const refresh = localStorage.getItem('refresh_token')
      if (refresh) {
        try {
          const res = await axios.post(`${API_BASE}/auth/refresh`, { refresh_token: refresh })
          if (res.data.success) {
            localStorage.setItem('access_token', res.data.data.access_token)
            localStorage.setItem('refresh_token', res.data.data.refresh_token)
            original.headers.Authorization = `Bearer ${res.data.data.access_token}`
            return axios(original)
          }
        } catch {
          localStorage.removeItem('access_token')
          localStorage.removeItem('refresh_token')
        }
      }
    }
    return Promise.reject(error)
  }
)

export const authAPI = {
  login: (email: string, password: string) => api.post('/auth/login', { email, password }),
  signup: (email: string, password: string, name: string) => api.post('/auth/signup', { email, password, name }),
  me: () => api.get('/auth/me'),
}

export const agentAPI = {
  chatURL: `${API_BASE}/agent/chat`,
  conversations: () => api.get('/agent/conversations'),
  conversation: (id: number) => api.get(`/agent/conversations/${id}`),
  deleteConversation: (id: number) => api.delete(`/agent/conversations/${id}`),
}

export const alertsAPI = {
  list: (limit?: number) => api.get('/ai/alerts', { params: { limit } }),
  markRead: (id: number) => api.post(`/ai/alerts/${id}/read`),
  scan: () => api.post('/ai/alerts/scan'),
}

export const builderAPI = {
  screener: {
    generate: (description: string) => api.post('/builder/screener/generate', { description }),
    execute: (config: any) => api.post('/builder/screener/execute', config),
    saved: () => api.get('/builder/screener/saved'),
    save: (title: string, config: any) => api.post('/builder/screener/save', { title, config }),
    delete: (id: number) => api.delete(`/builder/screener/saved/${id}`),
  },
}

export default api
