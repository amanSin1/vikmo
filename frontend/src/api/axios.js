import axios from 'axios'

const api = axios.create({
  baseURL: 'http://localhost:8000/api',
  withCredentials: true,
})

// Attach Basic Auth header from localStorage on every request
api.interceptors.request.use((config) => {
  const credentials = localStorage.getItem('vikmo_credentials')
  if (credentials) {
    config.headers['Authorization'] = `Basic ${credentials}`
  }
  return config
})

// If 401, clear credentials and redirect to login
api.interceptors.response.use(
  (res) => res,
  (err) => {
    if (err.response?.status === 401) {
      localStorage.removeItem('vikmo_credentials')
      localStorage.removeItem('vikmo_user')
      window.location.href = '/login'
    }
    return Promise.reject(err)
  }
)

export default api