'use client'

import { useState, useEffect } from 'react'

// Simple mock user type
interface MockUser {
  id: string
  email: string
  name?: string
  phone?: string
}

// Demo credentials που δουλεύουν
const DEMO_CREDENTIALS = [
  {
    email: 'citizen@helpmeanytime.gr',
    password: 'Demo123!',
    user: { id: 'user-citizen-1', email: 'citizen@helpmeanytime.gr', name: 'Γιώργος Παπαδόπουλος', phone: '210 123 4567' }
  },
  {
    email: 'professional@helpmeanytime.gr', 
    password: 'Demo123!',
    user: { id: 'user-professional-1', email: 'professional@helpmeanytime.gr', name: 'Νίκος Ηλεκτρολόγος', phone: '210 234 5678' }
  },
  {
    email: 'admin@athens.gov.gr',
    password: 'Admin123!', 
    user: { id: 'user-admin-1', email: 'admin@athens.gov.gr', name: 'Μαρία Δημητρίου', phone: '210 345 6789' }
  }
]

export function useAuth() {
  const [user, setUser] = useState<MockUser | null>(null)
  const [loading, setLoading] = useState(true) // Start as true to load from localStorage
  const [error, setError] = useState<string | null>(null)

  // Load user from localStorage on mount
  useEffect(() => {
    try {
      const savedUser = localStorage.getItem('helpmeanyTime_user')
      if (savedUser) {
        setUser(JSON.parse(savedUser))
      }
    } catch (err) {
      console.error('Error loading user from localStorage:', err)
    } finally {
      setLoading(false)
    }
  }, [])

  const signIn = async (email: string, password: string) => {
    setLoading(true)
    setError(null)
    
    try {
      // Check demo credentials
      const credential = DEMO_CREDENTIALS.find(cred => cred.email === email && cred.password === password)
      
      if (credential) {
        console.log('✅ Demo login successful for:', email)
        setUser(credential.user)
        localStorage.setItem('helpmeanyTime_user', JSON.stringify(credential.user))
        setLoading(false)
        return { user: credential.user, error: null }
      } else {
        throw new Error('Μη έγκυρα διαπιστευτήρια. Χρησιμοποιήστε: citizen@helpmeanytime.gr / Demo123!')
      }
    } catch (err: any) {
      const errorMessage = err.message || 'Αποτυχία σύνδεσης'
      console.error('❌ Login failed:', errorMessage)
      setError(errorMessage)
      setLoading(false)
      return { user: null, error: errorMessage }
    }
  }

  const signUp = async (email: string, password: string, metadata?: { name?: string, phone?: string }) => {
    setLoading(true)
    setError(null)
    
    try {
      // For demo purposes, allow any signup
      if (email && password && password.length >= 6) {
        const mockUser = {
          id: `user-${Date.now()}`,
          email,
          name: metadata?.name || 'Νέος Χρήστης',
          phone: metadata?.phone
        }
        console.log('✅ Demo signup successful for:', email)
        // Don't auto-sign in on signup, just return success
        setLoading(false)
        return { user: mockUser, error: null }
      } else {
        throw new Error('Παρακαλώ συμπληρώστε όλα τα απαιτούμενα πεδία (κωδικός τουλάχιστον 6 χαρακτήρες)')
      }
    } catch (err: any) {
      const errorMessage = err.message || 'Αποτυχία εγγραφής'
      console.error('❌ Signup failed:', errorMessage)
      setError(errorMessage)
      setLoading(false)
      return { user: null, error: errorMessage }
    }
  }

  const signOut = async () => {
    console.log('🚪 Signing out user')
    setUser(null)
    setError(null)
    localStorage.removeItem('helpmeanyTime_user')
  }

  return {
    user,
    loading,
    error,
    signIn,
    signUp,
    signOut,
    isAuthenticated: !!user
  }
}
