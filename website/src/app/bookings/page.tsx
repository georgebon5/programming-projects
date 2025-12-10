// My Bookings Page - Τα Ραντεβού Μου (Working Demo Version)
'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { Calendar, Clock, MapPin, Euro, Check, X, AlertCircle, Plus, ArrowLeft, RotateCcw } from 'lucide-react'

// Simple booking interface for demo
interface SimpleBooking {
  id: string
  citizenId: string
  professionalId: string
  professionalName?: string
  profession?: string
  serviceType: string
  scheduledDate: string
  scheduledTime: string
  durationHours: number
  address: string
  description: string
  status: string
  basePrice: number
  municipalitySubsidy: number
  citizenPays: number
  createdAt: string
}

const professionLabels: Record<string, string> = {
  electrician: 'Ηλεκτρολόγος',
  plumber: 'Υδραυλικός',
  carpenter: 'Μαραγκός',
  painter: 'Βαφέας',
  mason: 'Οικοδόμος',
  hvac: 'Τεχνικός Κλιματισμού',
  gardener: 'Κηπουρός',
  cleaner: 'Καθαριστής/Καθαρίστρια',
  locksmith: 'Κλειδαράς',
  appliance_repair: 'Επισκευή Συσκευών',
  electrical: 'Ηλεκτρολογικά',
  plumbing: 'Υδραυλικά',
  general: 'Γενικά',
}

const statusLabels: Record<string, string> = {
  pending: 'Εκκρεμεί',
  approved: 'Εγκρίθηκε', 
  confirmed: 'Επιβεβαιώθηκε',
  rejected: 'Απορρίφθηκε',
  completed: 'Ολοκληρώθηκε',
  cancelled: 'Ακυρώθηκε',
}

const statusColors: Record<string, string> = {
  pending: 'bg-warning-50 text-warning-700 border-warning-200',
  approved: 'bg-success-50 text-success-700 border-success-200', 
  confirmed: 'bg-accent-50 text-accent-700 border-accent-200',
  rejected: 'bg-danger-50 text-danger-700 border-danger-200',
  completed: 'bg-success-50 text-success-600 border-success-200',
  cancelled: 'bg-neutral-100 text-neutral-600 border-neutral-200',
}

const statusIcons: Record<string, React.ReactNode> = {
  pending: <AlertCircle className="w-4 h-4" />,
  approved: <Check className="w-4 h-4" />,
  confirmed: <Check className="w-4 h-4" />,
  rejected: <X className="w-4 h-4" />,
  completed: <Check className="w-4 h-4" />,
  cancelled: <X className="w-4 h-4" />,
}

export default function MyBookingsPage() {
  const router = useRouter()
  const { user, isAuthenticated, loading: authLoading } = useAuth()
  const [bookings, setBookings] = useState<SimpleBooking[]>([])
  const [loading, setLoading] = useState(true)
  const [filter, setFilter] = useState<'all' | 'pending' | 'confirmed' | 'completed'>('all')

  // Redirect if not authenticated
  useEffect(() => {
    if (!authLoading && !isAuthenticated) {
      router.push('/auth?mode=signin&redirect=/bookings')
    }
  }, [authLoading, isAuthenticated, router])

  // Fetch bookings for the current user
  const fetchBookings = async () => {
    if (!user?.id) {
      console.log('❌ No user ID available')
      setLoading(false)
      return
    }
    
    try {
      setLoading(true)
      console.log('🔍 Fetching bookings for user:', user.id)
      const response = await fetch(`/api/bookings?citizenId=${user.id}`)
      
      if (!response.ok) {
        throw new Error('Failed to fetch bookings')
      }

      const data = await response.json()
      console.log('📋 Fetched bookings:', data)
      setBookings(data.bookings || [])
    } catch (error) {
      console.error('❌ Error fetching bookings:', error)
      setBookings([])
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (!isAuthenticated || !user?.id) {
      console.log('⏳ Waiting for user authentication...')
      return
    }
    
    fetchBookings()
    
    // Auto refresh when window gains focus (user returns to the page)
    const handleFocus = () => {
      console.log('🔄 Window focused - refreshing bookings')
      fetchBookings()
    }
    
    // Auto refresh when page becomes visible (tab switching)
    const handleVisibilityChange = () => {
      if (!document.hidden) {
        console.log('🔄 Page became visible - refreshing bookings')
        fetchBookings()
      }
    }
    
    window.addEventListener('focus', handleFocus)
    document.addEventListener('visibilitychange', handleVisibilityChange)
    
    return () => {
      window.removeEventListener('focus', handleFocus)
      document.removeEventListener('visibilitychange', handleVisibilityChange)
    }
  }, [isAuthenticated, user?.id])

  const filteredBookings = filter === 'all' 
    ? bookings 
    : bookings.filter(b => b.status === filter)

  if (loading) {
    return (
      <div className="min-h-screen bg-neutral-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-primary-600">Φόρτωση ραντεβού...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-neutral-50 p-4 sm:p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-10">
          <div className="flex items-center gap-4 mb-6">
            <button
              onClick={() => router.push('/dashboard')}
              className="flex items-center gap-2 text-primary-600 hover:text-primary-900 transition font-medium"
            >
              <ArrowLeft className="w-5 h-5" />
              <span>Πίσω στο Dashboard</span>
            </button>
            <span className="text-neutral-300">|</span>
            <button
              onClick={() => router.push('/')}
              className="flex items-center gap-2 text-primary-600 hover:text-primary-900 transition font-medium"
            >
              <ArrowLeft className="w-5 h-5" />
              <span>Αρχική Σελίδα</span>
            </button>
          </div>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-6">
            <div>
              <div className="flex items-center gap-4 mb-3">
                <h1 className="text-4xl font-bold text-primary-900">
                  Τα Ραντεβού Μου
                </h1>
                <span className="bg-primary-900 text-white px-4 py-2 rounded-full text-lg font-bold shadow-soft">
                  {bookings.length}
                </span>
              </div>
              <p className="text-primary-600 text-lg leading-relaxed">
                Διαχειριστείτε τα ραντεβού σας με επαγγελματίες
              </p>
            </div>
            <div className="flex gap-4">
              <button
                onClick={fetchBookings}
                disabled={loading}
                className="flex items-center gap-2 bg-white border border-neutral-200 text-primary-700 px-6 py-3 rounded-xl font-medium hover:bg-neutral-50 transition disabled:opacity-50 shadow-card"
              >
                <RotateCcw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                Ανανέωση
              </button>
              <button
                onClick={() => router.push('/bookings/new')}
                className="flex items-center gap-2 bg-primary-900 text-white px-8 py-3 rounded-xl font-semibold hover:bg-primary-800 transition shadow-soft hover:shadow-card"
              >
                <Plus className="w-5 h-5" />
                Νέο Ραντεβού
              </button>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-4 mb-10">
          <button
            onClick={() => setFilter('all')}
            className={`px-6 py-3 rounded-xl font-medium transition ${
              filter === 'all'
                ? 'bg-primary-900 text-white shadow-soft'
                : 'bg-white text-primary-700 hover:bg-neutral-50 border border-neutral-200'
            }`}
          >
            Όλα ({bookings.length})
          </button>
          <button
            onClick={() => setFilter('pending')}
            className={`px-6 py-3 rounded-xl font-medium transition ${
              filter === 'pending'
                ? 'bg-warning-600 text-white shadow-soft'
                : 'bg-white text-primary-700 hover:bg-neutral-50 border border-neutral-200'
            }`}
          >
            Εκκρεμεί ({bookings.filter(b => b.status === 'pending').length})
          </button>
          <button
            onClick={() => setFilter('confirmed')}
            className={`px-6 py-3 rounded-xl font-medium transition ${
              filter === 'confirmed'
                ? 'bg-success-600 text-white shadow-soft'
                : 'bg-white text-primary-700 hover:bg-neutral-50 border border-neutral-200'
            }`}
          >
            Επιβεβαιώθηκε ({bookings.filter(b => b.status === 'confirmed').length})
          </button>
          <button
            onClick={() => setFilter('completed')}
            className={`px-4 py-2 rounded-lg font-medium transition ${
              filter === 'completed'
                ? 'bg-blue-600 text-white shadow-lg'
                : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
          >
            Ολοκληρώθηκε ({bookings.filter(b => b.status === 'completed').length})
          </button>
        </div>

        {/* Bookings List */}
        {filteredBookings.length === 0 ? (
          <div className="bg-white rounded-2xl shadow-lg p-12 text-center">
            <Calendar className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-800 mb-2">
              {filter === 'all' ? 'Δεν έχετε ραντεβού' : `Δεν έχετε ${statusLabels[filter]?.toLowerCase()} ραντεβού`}
            </h3>
            <p className="text-gray-600 mb-6">
              Κλείστε το πρώτο σας ραντεβού με έναν επαγγελματία
            </p>
            <button
              onClick={() => router.push('/bookings/new')}
              className="bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-6 py-3 rounded-lg font-semibold hover:from-blue-700 hover:to-indigo-700 transition shadow-lg inline-flex items-center gap-2"
            >
              <Plus className="w-5 h-5" />
              Νέο Ραντεβού
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 gap-6">
            {filteredBookings.map((booking) => {
              const formattedDate = new Date(booking.scheduledDate).toLocaleDateString('el-GR', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric',
              })

              return (
                <div
                  key={booking.id}
                  className="bg-white rounded-2xl shadow-lg hover:shadow-xl transition overflow-hidden"
                >
                  <div className="flex flex-col sm:flex-row">
                    {/* Left Section - Main Info */}
                    <div className="flex-1 p-6">
                      <div className="flex items-start justify-between mb-4">
                        <div>
                          <h3 className="text-xl font-bold text-gray-800 mb-1">
                            {booking.professionalName || `Επαγγελματίας #${booking.professionalId}`}
                          </h3>
                          <p className="text-sm text-gray-600">
                            {professionLabels[booking.profession || booking.serviceType] || booking.serviceType}
                          </p>
                        </div>
                        <div className={`flex items-center gap-1 px-3 py-1.5 rounded-lg border text-sm font-medium ${statusColors[booking.status]}`}>
                          {statusIcons[booking.status]}
                          {statusLabels[booking.status]}
                        </div>
                      </div>

                      <div className="space-y-3">
                        <div className="flex items-start gap-3 text-sm text-gray-700">
                          <Calendar className="w-5 h-5 text-gray-400 flex-shrink-0 mt-0.5" />
                          <div>
                            <p className="font-medium">{formattedDate}</p>
                            <p className="text-gray-500 flex items-center gap-1">
                              <Clock className="w-4 h-4" />
                              {booking.scheduledTime}
                            </p>
                          </div>
                        </div>

                        <div className="flex items-start gap-3 text-sm text-gray-700">
                          <MapPin className="w-5 h-5 text-gray-400 flex-shrink-0" />
                          <p>{booking.address}</p>
                        </div>

                        {booking.description && (
                          <div className="bg-gray-50 rounded-lg p-3 text-sm text-gray-700">
                            <p className="font-medium mb-1">Περιγραφή:</p>
                            <p className="text-gray-600">{booking.description}</p>
                          </div>
                        )}
                      </div>
                    </div>

                    {/* Right Section - Cost */}
                    <div className="bg-gradient-to-br from-blue-50 to-indigo-50 p-6 sm:w-64 border-t sm:border-t-0 sm:border-l border-gray-200">
                      <h4 className="text-sm font-semibold text-gray-700 mb-4">
                        Κόστος
                      </h4>
                      <div className="space-y-3">
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">Ώρες:</span>
                          <span className="font-medium">{booking.durationHours}h</span>
                        </div>
                        <div className="flex justify-between text-sm">
                          <span className="text-gray-600">Σύνολο:</span>
                          <span className="font-medium">€{booking.basePrice.toFixed(2)}</span>
                        </div>
                        <div className="flex justify-between text-sm text-green-600">
                          <span>Επιδότηση:</span>
                          <span className="font-medium">-€{booking.municipalitySubsidy.toFixed(2)}</span>
                        </div>
                        <div className="border-t border-gray-300 pt-3">
                          <div className="flex justify-between items-center">
                            <span className="text-sm text-gray-700 font-medium">Πληρώνετε:</span>
                            <div className="text-right">
                              <div className="text-2xl font-bold text-blue-600">
                                €{booking.citizenPays.toFixed(2)}
                              </div>
                              <div className="text-xs text-green-600 font-medium">
                                -70% 🎉
                              </div>
                            </div>
                          </div>
                        </div>
                      </div>
                    </div>
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {/* Info Section */}
        <div className="mt-8 bg-white rounded-2xl shadow-lg p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4">
            💡 Πληροφορίες Κρατήσεων
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm text-gray-700">
            <div>
              <h4 className="font-semibold mb-2">Κατάσταση "Εκκρεμεί"</h4>
              <p className="text-gray-600">
                Το ραντεβού σας περιμένει έγκριση από τον Δήμο. Θα ενημερωθείτε εντός 24-48 ωρών.
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-2">Κατάσταση "Επιβεβαιώθηκε"</h4>
              <p className="text-gray-600">
                Η επιδότηση εγκρίθηκε! Ο επαγγελματίας θα έρθει στην ημερομηνία που ορίσατε.
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-2">Πληρωμή</h4>
              <p className="text-gray-600">
                Πληρώνετε μόνο το 30% του κόστους στον επαγγελματία μετά την ολοκλήρωση της εργασίας.
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-2">Ακύρωση</h4>
              <p className="text-gray-600">
                Για ακύρωση ραντεβού, επικοινωνήστε με τον Δήμο τουλάχιστον 24 ώρες πριν.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
