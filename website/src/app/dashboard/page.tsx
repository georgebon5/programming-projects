// User Dashboard - Main hub after login
'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { RefreshCw } from 'lucide-react'

export default function DashboardPage() {
  const router = useRouter()
  const { user, isAuthenticated, loading, signOut } = useAuth()
  const [bookingsCount, setBookingsCount] = useState(0)
  const [myProjectsCount, setMyProjectsCount] = useState(0)
  const [activeProjectsCount, setActiveProjectsCount] = useState(0)
  const [dataLoading, setDataLoading] = useState(true)

  const fetchStats = async () => {
    if (!isAuthenticated || !user) return
    
    try {
      setDataLoading(true)
      
      // Fetch bookings for the user
      const bookingsRes = await fetch(`/api/bookings?citizenId=${user.id}`)
      if (bookingsRes.ok) {
        const bookingsData = await bookingsRes.json()
        setBookingsCount(bookingsData.bookings?.length || 0)
      }
      
      // Fetch all projects
      const projectsRes = await fetch('/api/projects')
      if (projectsRes.ok) {
        const projectsData = await projectsRes.json()
        
        // Count user's own projects
        const userProjects = projectsData.filter((p: any) => p.creatorId === user.id)
        setMyProjectsCount(userProjects.length)
        
        // Count all active/approved projects in the municipality
        const activeProjects = projectsData.filter((p: any) => 
          p.status === 'active' || p.status === 'approved' || p.status === 'in_progress'
        )
        setActiveProjectsCount(activeProjects.length)
      }
    } catch (error) {
      console.error('Error fetching stats:', error)
    } finally {
      setDataLoading(false)
    }
  }

  useEffect(() => {
    if (!loading && !isAuthenticated) {
      router.push('/auth')
    }
  }, [isAuthenticated, loading, router])

  useEffect(() => {
    if (isAuthenticated && user) {
      fetchStats()
    }
  }, [isAuthenticated, user])

  const handleSignOut = async () => {
    await signOut()
    router.push('/')
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600 text-lg">Φόρτωση Dashboard...</p>
        </div>
      </div>
    )
  }

  if (!user) {
    return null
  }

  return (
    <div className="min-h-screen bg-gray-50">
      {/* Navigation */}
      <nav className="bg-white shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <div className="flex items-center gap-8">
              <button 
                onClick={() => router.push('/')}
                className="text-2xl font-bold text-gray-900"
              >
                HelpMeAnytime
              </button>
              <div className="hidden md:flex items-center gap-6">
                <button onClick={() => router.push('/dashboard')} className="text-blue-600 font-medium">
                  Dashboard
                </button>
                <button onClick={() => router.push('/bookings')} className="text-gray-700 hover:text-blue-600 transition">
                  Ραντεβού
                </button>
                <button onClick={() => router.push('/help')} className="text-gray-700 hover:text-blue-600 transition">
                  Αιτήματα
                </button>
                <button onClick={() => router.push('/projects')} className="text-gray-700 hover:text-blue-600 transition">
                  Έργα
                </button>
              </div>
            </div>
            <div className="flex items-center gap-4">
              <span className="text-sm text-gray-700">
                <strong>{user.name || user.email}</strong>
              </span>
              <button
                onClick={handleSignOut}
                className="px-4 py-2 text-sm text-gray-700 hover:text-red-600 transition font-medium"
              >
                Αποσύνδεση
              </button>
            </div>
          </div>
        </div>
      </nav>

      {/* Main Content */}
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Welcome Section */}
        <div className="mb-12 text-center">
          <h1 className="text-5xl font-bold text-gray-900 mb-4">
            Καλώς ήρθες, {user.name || 'δημότη'}!
          </h1>
          <button
            onClick={fetchStats}
            disabled={dataLoading}
            className="inline-flex items-center gap-2 px-4 py-2 text-sm text-gray-600 hover:text-blue-900 transition disabled:opacity-50"
          >
            <RefreshCw className={`w-4 h-4 ${dataLoading ? 'animate-spin' : ''}`} />
            Ανανέωση
          </button>
        </div>

        {/* Quick Actions */}
        <div className="grid md:grid-cols-3 gap-8 mb-12">
          {/* Book Appointment */}
          <button
            onClick={() => router.push('/professionals')}
            className="bg-blue-500 rounded-2xl p-8 text-center hover:shadow-xl transition transform hover:-translate-y-1 border-2 border-transparent hover:border-blue-300"
          >
            <h3 className="text-3xl font-bold text-white mb-3">
              Κλείσε Ραντεβού με ειδικό
            </h3>
          </button>

          {/* Request Help */}
          <button
            onClick={() => router.push('/help')}
            className="bg-blue-500 rounded-2xl p-8 text-center hover:shadow-xl transition transform hover:-translate-y-1 border-2 border-transparent hover:border-blue-300"
          >
            <h3 className="text-3xl font-bold text-white mb-3">
              Ζήτα ή Πρόσφερε Βοήθεια
            </h3>
          </button>

          {/* Propose Project */}
          <button
            onClick={() => router.push('/projects')}
            className="bg-blue-500 rounded-2xl p-8 text-center hover:shadow-xl transition transform hover:-translate-y-1 border-2 border-transparent hover:border-indigo-300"
          >
            <h3 className="text-3xl font-bold text-white mb-3">
              Πρότεινε Έργο
            </h3>
            <p className="text-white text-lg mb-4">
              Βοήθησε την κοινότητα
            </p>
          </button>
        </div>

        {/* Stats Cards */}
        <div className="grid md:grid-cols-2 gap-6 mb-12">
          <div 
            className="bg-white rounded-xl p-6 shadow-md text-center cursor-pointer hover:shadow-xl transition"
            onClick={() => router.push('/bookings')}
          >
            <div className="text-5xl mb-3">📅</div>
            <div className="text-4xl font-bold text-blue-900 mb-2">
              {dataLoading ? '...' : bookingsCount}
            </div>
            <div className="text-lg text-gray-600 font-medium">Τα Ραντεβού μου</div>
          </div>
          
          <div 
            className="bg-white rounded-xl p-6 shadow-md text-center cursor-pointer hover:shadow-xl transition"
            onClick={() => router.push('/projects')}
          >
            <div className="text-5xl mb-3">🏗️</div>
            <div className="text-4xl font-bold text-green-700 mb-2">
              {dataLoading ? '...' : activeProjectsCount}
            </div>
            <div className="text-lg text-gray-600 font-medium">Ενεργά Έργα Δήμου</div>
          </div>

    
        </div>
      </div>
    </div>
  )
}
