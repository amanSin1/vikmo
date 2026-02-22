import { createContext, useContext, useState } from 'react'
import api from '../api/axios'

const AuthContext = createContext(null)

export function AuthProvider({ children }) {
  const [user, setUser] = useState(() => {
    const saved = localStorage.getItem('vikmo_user')
    return saved ? JSON.parse(saved) : null
  })

  const login = async (username, password) => {
    // Encode credentials for Basic Auth
    const credentials = btoa(`${username}:${password}`)
    localStorage.setItem('vikmo_credentials', credentials)

    try {
      // Test credentials by hitting products endpoint
      const res = await api.get('/products/')
      // If we get here, credentials are valid
      // Check if admin by trying admin-only endpoint
      let isAdmin = false
      try {
        await api.get('/inventory/')
        isAdmin = true
      } catch {
        isAdmin = false
      }

      const userData = { username, isAdmin }
      localStorage.setItem('vikmo_user', JSON.stringify(userData))
      setUser(userData)
      return { success: true, isAdmin }
    } catch (err) {
      localStorage.removeItem('vikmo_credentials')
      throw new Error('Invalid username or password')
    }
  }

  const logout = () => {
    localStorage.removeItem('vikmo_credentials')
    localStorage.removeItem('vikmo_user')
    setUser(null)
  }

  return (
    <AuthContext.Provider value={{ user, login, logout }}>
      {children}
    </AuthContext.Provider>
  )
}

export const useAuth = () => useContext(AuthContext)