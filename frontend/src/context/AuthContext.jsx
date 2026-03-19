import { createContext, useContext, useState, useEffect } from 'react'
import api from '../services/api'

const AuthContext = createContext(null)

export const useAuth = () => {
  const context = useContext(AuthContext)
  if (!context) {
    throw new Error('useAuth must be used within an AuthProvider')
  }
  return context
}

export const AuthProvider = ({ children }) => {
  const [user, setUser] = useState(null)
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // Try to restore session by fetching current user
    // Tokens are stored in httpOnly cookies, browser sends them automatically
    const restoreSession = async () => {
      try {
        const response = await api.get('/users/me', {
          withCredentials: true
        })
        setUser(response.data)
        localStorage.setItem('user', JSON.stringify(response.data))
      } catch (error) {
        // No valid session - user is not logged in
        localStorage.removeItem('user')
      }
      setLoading(false)
    }

    restoreSession()
  }, [])

  const login = async (email, password) => {
    const response = await api.post('/auth/login', { email, password }, {
      withCredentials: true
    })

    // Tokens are now in httpOnly cookies, no need to store them here
    const userResponse = await api.get('/users/me', {
      withCredentials: true
    })
    setUser(userResponse.data)
    localStorage.setItem('user', JSON.stringify(userResponse.data))

    return userResponse.data
  }

  const register = async (email, password, fullName, phone) => {
    const response = await api.post('/auth/register', {
      email,
      password,
      full_name: fullName,
      phone
    }, {
      withCredentials: true
    })

    // Tokens are now in httpOnly cookies
    const userResponse = await api.get('/users/me', {
      withCredentials: true
    })
    setUser(userResponse.data)
    localStorage.setItem('user', JSON.stringify(userResponse.data))

    return userResponse.data
  }

  const logout = async () => {
    try {
      await api.post('/auth/logout', {}, {
        withCredentials: true
      })
    } catch (error) {
      console.error('Logout error:', error)
    }

    // Clear local storage
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    localStorage.removeItem('user')
    delete api.defaults.headers.common['Authorization']
    setUser(null)
  }

  const refreshUser = async () => {
    try {
      const response = await api.get('/users/me', {
        withCredentials: true
      })
      setUser(response.data)
      localStorage.setItem('user', JSON.stringify(response.data))
      return response.data
    } catch (error) {
      console.error('Failed to refresh user:', error)
      // If refresh fails, user might be logged out
      if (error.response?.status === 401) {
        setUser(null)
        localStorage.removeItem('user')
      }
    }
  }

  return (
    <AuthContext.Provider value={{ user, loading, login, register, logout, refreshUser }}>
      {children}
    </AuthContext.Provider>
  )
}