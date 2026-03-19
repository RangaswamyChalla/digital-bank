import axios from 'axios'

const api = axios.create({
  baseURL: '',
  headers: {
    'Content-Type': 'application/json'
  },
  withCredentials: true  // Send cookies with requests
})

// Request interceptor - no longer adds Authorization header since we use httpOnly cookies
api.interceptors.request.use(
  (config) => {
    // Tokens are now in httpOnly cookies, browser sends them automatically
    // No need to read them from localStorage
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// Response interceptor for token refresh and error handling
api.interceptors.response.use(
  (response) => response,
  async (error) => {
    const originalRequest = error.config

    // Handle 401 by attempting token refresh
    if (error.response?.status === 401 && !originalRequest._retry) {
      originalRequest._retry = true

      try {
        // Refresh endpoint reads from httpOnly cookie automatically
        const response = await axios.post(
          '/api/auth/refresh',
          {},
          { withCredentials: true }
        )

        const { access_token, refresh_token: newRefreshToken } = response.data

        // Store new tokens in cookies (handled by backend via httpOnly)
        // Keep user data in localStorage for UI state
        if (newRefreshToken) {
          localStorage.setItem('refresh_token', newRefreshToken)
        }

        // Retry the original request
        return api(originalRequest)
      } catch (refreshError) {
        // Refresh failed - clear user data and redirect to login
        localStorage.removeItem('user')
        localStorage.removeItem('refresh_token')
        window.location.href = '/login'
        return Promise.reject(refreshError)
      }
    }

    return Promise.reject(error)
  }
)

export default api