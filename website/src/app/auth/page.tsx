'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import Link from 'next/link'
import { useAuth } from '@/hooks/useAuth'

export default function AuthPage() {
  const [isLogin, setIsLogin] = useState(true)
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [name, setName] = useState('')
  const [error, setError] = useState('')
  const [loading, setLoading] = useState(false)
  
  const router = useRouter()
  const { signIn, signUp } = useAuth()

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setError('')
    setLoading(true)

    try {
      if (isLogin) {
        const result = await signIn(email, password)
        if (result.error) {
          setError(result.error)
          setLoading(false)
          return
        }
        router.push('/dashboard')
      } else {
        if (!name.trim()) {
          setError('Το όνομα είναι υποχρεωτικό')
          setLoading(false)
          return
        }
        const result = await signUp(email, password, { name })
        if (result.error) {
          setError(result.error)
          setLoading(false)
          return
        }
        // After successful signup, log them in
        const loginResult = await signIn(email, password)
        if (loginResult.error) {
          setError('Εγγραφή επιτυχής! Παρακαλώ συνδεθείτε.')
          setIsLogin(true)
          setLoading(false)
          return
        }
        router.push('/dashboard')
      }
    } catch (err: any) {
      setError(err.message || 'Κάτι πήγε στραβά. Παρακαλώ δοκιμάστε ξανά.')
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-white flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
      <div className="max-w-md w-full space-y-8">
        {/* Logo */}
        <div className="text-center">
          <Link href="/" className="inline-flex items-center justify-center space-x-3 mb-6">
            <div className="w-16 h-16 bg-blue-900 rounded-full flex items-center justify-center shadow-lg">
              <span className="text-white text-2xl font-bold">HA</span>
            </div>
          </Link>
          <h2 className="text-3xl font-bold text-gray-900 text-center">
            {isLogin ? 'Σύνδεση' : 'Εγγραφή'}
          </h2>
          <p className="mt-3 text-base text-gray-600 text-center">
            {isLogin 
              ? 'Συνδεθείτε για να έχετε πρόσβαση στον λογαριασμό σας' 
              : 'Δημιουργήστε έναν νέο λογαριασμό'}
          </p>
        </div>

        {/* Auth Form */}
        <div className="bg-white rounded-2xl shadow-xl p-8">
          <form onSubmit={handleSubmit} className="space-y-6">
            {!isLogin && (
              <div>
                <label htmlFor="name" className="block text-base font-medium text-gray-900 mb-2 text-center">
                  Ονοματεπώνυμο
                </label>
                <input
                  id="name"
                  name="name"
                  type="text"
                  required={!isLogin}
                  value={name}
                  onChange={(e) => setName(e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-xl text-gray-900 bg-white placeholder:text-gray-500 text-base focus:outline-none focus:ring-2 focus:ring-blue-900 focus:border-transparent"
                  placeholder="Εισάγετε το όνομά σας"
                />
              </div>
            )}

            <div>
              <label htmlFor="email" className="block text-base font-medium text-gray-900 mb-2 text-center">
                Email
              </label>
              <input
                id="email"
                name="email"
                type="email"
                required
                value={email}
                onChange={(e) => setEmail(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl text-gray-900 bg-white placeholder:text-gray-500 text-base focus:outline-none focus:ring-2 focus:ring-blue-900 focus:border-transparent"
                placeholder="email@example.com"
              />
            </div>

            <div>
              <label htmlFor="password" className="block text-base font-medium text-gray-900 mb-2 text-center">
                Κωδικός
              </label>
              <input
                id="password"
                name="password"
                type="password"
                required
                value={password}
                onChange={(e) => setPassword(e.target.value)}
                className="w-full px-4 py-3 border border-gray-300 rounded-xl text-gray-900 bg-white placeholder:text-gray-500 text-base focus:outline-none focus:ring-2 focus:ring-blue-900 focus:border-transparent"
                placeholder="Εισάγετε τον κωδικό σας"
              />
            </div>

            {error && (
              <div className="bg-red-50 border border-red-200 text-red-800 px-4 py-3 rounded-xl text-center text-base">
                {error}
              </div>
            )}

            <button
              type="submit"
              disabled={loading}
              className="w-full bg-blue-900 text-white py-3 px-4 rounded-xl text-base font-semibold hover:bg-blue-800 focus:outline-none focus:ring-2 focus:ring-blue-900 focus:ring-offset-2 transition-colors disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Παρακαλώ περιμένετε...' : (isLogin ? 'Σύνδεση' : 'Εγγραφή')}
            </button>
          </form>

          {/* Toggle between Login/Signup */}
          <div className="mt-6 text-center">
            <button
              type="button"
              onClick={() => {
                setIsLogin(!isLogin)
                setError('')
                setName('')
                setEmail('')
                setPassword('')
              }}
              className="text-blue-900 hover:text-blue-700 font-medium text-base"
            >
              {isLogin 
                ? 'Δεν έχετε λογαριασμό; Εγγραφείτε εδώ' 
                : 'Έχετε ήδη λογαριασμό; Συνδεθείτε εδώ'}
            </button>
          </div>

          {/* Demo Credentials */}
          <div className="mt-6 bg-blue-50 border border-blue-200 rounded-xl p-4">
            <p className="text-sm font-semibold text-gray-900 mb-2 text-center">Demo Credentials:</p>
            <div className="space-y-1 text-sm text-gray-700 text-center">
              <p><strong>Πολίτης:</strong> citizen@helpmeanytime.gr / Demo123!</p>
              <p><strong>Επαγγελματίας:</strong> professional@helpmeanytime.gr / Demo123!</p>
              <p><strong>Δήμος:</strong> municipality@helpmeanytime.gr / Demo123!</p>
            </div>
          </div>
        </div>

        {/* Back to Home */}
        <div className="text-center">
          <Link href="/" className="text-base text-gray-600 hover:text-gray-900 font-medium">
            ← Επιστροφή στην αρχική
          </Link>
        </div>
      </div>
    </div>
  )
}
