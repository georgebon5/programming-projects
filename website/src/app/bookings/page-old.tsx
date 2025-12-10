// My Bookings Page - Τα Ραντεβού Μου
'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { useBookings } from '@/hooks/useBookings'
import { useProfessionals } from '@/hooks/useProfessionals'
import { Calendar, Clock, MapPin, Euro, Check, X, AlertCircle, Plus, ArrowLeft } from 'lucide-react'

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
}

const statusLabels: Record<string, string> = {
  pending: 'Εκκρεμεί',
  approved: 'Εγκρίθηκε',
  rejected: 'Απορρίφθηκε',
  completed: 'Ολοκληρώθηκε',
  cancelled: 'Ακυρώθηκε',
}

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  approved: 'bg-green-100 text-green-800 border-green-200',
  rejected: 'bg-red-100 text-red-800 border-red-200',
  completed: 'bg-blue-100 text-blue-800 border-blue-200',
  cancelled: 'bg-gray-100 text-gray-800 border-gray-200',
}

const statusIcons: Record<string, React.ReactNode> = {
  pending: <AlertCircle className="w-4 h-4" />,
  approved: <Check className="w-4 h-4" />,
  rejected: <X className="w-4 h-4" />,
  completed: <Check className="w-4 h-4" />,
  cancelled: <X className="w-4 h-4" />,
}

export default function MyBookingsPage() {
  const router = useRouter()
  const { user, isAuthenticated } = useAuth()
  // const { bookings, loading, fetchMyBookings } = useBookings() // Commented out for demo
  const { professionals, fetchProfessionals } = useProfessionals()
  const [filter, setFilter] = useState<'all' | 'pending' | 'approved' | 'completed'>('all')
  
  // Demo state
  const [bookings, setBookings] = useState<any[]>([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    // For demo purposes, we'll skip auth check and load mock data
    // if (!isAuthenticated) {
    //   router.push('/auth?mode=signin')
    //   return
    // }
    
    // Load mock data for demo
    const mockBookingsData = [
      {
        id: '1',
        citizenId: 'citizen-1',
        professionalId: 'prof-1',
        serviceType: 'electrician',
        scheduledDate: new Date('2024-12-20'),
        scheduledTime: '10:00',
        durationHours: 2,
        address: 'Πλατεία Εξαρχείων 15, Αθήνα',
        description: 'Επισκευή ηλεκτρολογικής εγκατάστασης',
        status: 'pending' as const,
        basePrice: 80,
        municipalitySubsidy: 56,
        citizenPays: 24,
        createdAt: new Date('2024-11-15'),
        updatedAt: new Date('2024-11-15')
      },
      {
        id: '2',
        citizenId: 'citizen-1',
        professionalId: 'prof-2', 
        serviceType: 'plumber',
        scheduledDate: new Date('2024-12-22'),
        scheduledTime: '14:00',
        durationHours: 3,
        address: 'Ακαδημίας 50, Αθήνα',
        description: 'Επισκευή βρύσης κουζίνας',
        status: 'approved' as const,
        basePrice: 120,
        municipalitySubsidy: 84,
        citizenPays: 36,
        createdAt: new Date('2024-11-10'),
        updatedAt: new Date('2024-11-12')
      }
    ]
    
    // Simulate loading
    setTimeout(() => {
      setBookings(mockBookingsData)
      setLoading(false)
    }, 1000)
    
    fetchProfessionals({ approved: true })
  }, [])

  const getProfessional = (professionalId: string) => {
    return professionals.find(p => p.id === professionalId)
  }

  const filteredBookings = filter === 'all' 
    ? bookings 
    : bookings.filter(b => b.status === filter)

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Φόρτωση ραντεβού...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 p-4 sm:p-8">
      <div className="max-w-6xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-4 mb-4">
            <button
              onClick={() => router.push('/dashboard')}
              className="flex items-center gap-2 text-gray-600 hover:text-gray-800 transition"
            >
              <ArrowLeft className="w-5 h-5" />
              <span>Πίσω στο Dashboard</span>
            </button>
            <span className="text-gray-400">|</span>
            <button
              onClick={() => router.push('/')}
              className="flex items-center gap-2 text-gray-600 hover:text-gray-800 transition"
            >
              <ArrowLeft className="w-5 h-5" />
              <span>Αρχική Σελίδα</span>
            </button>
          </div>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-4xl font-bold text-gray-800 mb-2">
                Τα Ραντεβού Μου
              </h1>
              <p className="text-gray-600">
                Διαχειριστείτε τα ραντεβού σας με επαγγελματίες
              </p>
            </div>
            <button
              onClick={() => router.push('/bookings/new')}
              className="flex items-center gap-2 bg-gradient-to-r from-blue-600 to-indigo-600 text-white px-6 py-3 rounded-lg font-semibold hover:from-blue-700 hover:to-indigo-700 transition shadow-lg"
            >
              <Plus className="w-5 h-5" />
              Νέο Ραντεβού
            </button>
          </div>
        </div>

        {/* Filters */}
        <div className="flex flex-wrap gap-3 mb-8">
          <button
            onClick={() => setFilter('all')}
            className={`px-4 py-2 rounded-lg font-medium transition ${
              filter === 'all'
                ? 'bg-blue-600 text-white shadow-lg'
                : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
          >
            Όλα ({bookings.length})
          </button>
          <button
            onClick={() => setFilter('pending')}
            className={`px-4 py-2 rounded-lg font-medium transition ${
              filter === 'pending'
                ? 'bg-yellow-500 text-white shadow-lg'
                : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
          >
            Εκκρεμεί ({bookings.filter(b => b.status === 'pending').length})
          </button>
          <button
            onClick={() => setFilter('approved')}
            className={`px-4 py-2 rounded-lg font-medium transition ${
              filter === 'approved'
                ? 'bg-green-600 text-white shadow-lg'
                : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
          >
            Εγκρίθηκε ({bookings.filter(b => b.status === 'approved').length})
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
              const professional = getProfessional(booking.professionalId)
              const appointmentDate = new Date(booking.appointmentDate)
              const formattedDate = appointmentDate.toLocaleDateString('el-GR', {
                weekday: 'long',
                year: 'numeric',
                month: 'long',
                day: 'numeric',
              })
              const formattedTime = appointmentDate.toLocaleTimeString('el-GR', {
                hour: '2-digit',
                minute: '2-digit',
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
                            {professional?.name || 'Επαγγελματίας'}
                          </h3>
                          <p className="text-sm text-gray-600">
                            {professional ? professionLabels[professional.profession] : ''}
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
                              {formattedTime}
                            </p>
                          </div>
                        </div>

                        <div className="flex items-start gap-3 text-sm text-gray-700">
                          <MapPin className="w-5 h-5 text-gray-400 flex-shrink-0" />
                          <p>{booking.serviceAddress}</p>
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
                          <span className="font-medium">{booking.estimatedHours}h</span>
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

                      {/* Rating Section (for completed) */}
                      {booking.status === 'completed' && professional && (
                        <div className="mt-4 pt-4 border-t border-gray-300">
                          <p className="text-xs text-gray-600 mb-1">Αξιολόγηση</p>
                          <div className="flex items-center gap-1">
                            {[...Array(5)].map((_, i) => (
                              <span key={i} className={i < Math.floor(professional.rating) ? 'text-yellow-400' : 'text-gray-300'}>
                                ★
                              </span>
                            ))}
                          </div>
                        </div>
                      )}
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
            Πληροφορίες Κρατήσεων
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm text-gray-700">
            <div>
              <h4 className="font-semibold mb-2">Κατάσταση "Εκκρεμεί"</h4>
              <p className="text-gray-600">
                Το ραντεβού σας περιμένει έγκριση από τον Δήμο. Θα ενημερωθείτε εντός 24-48 ωρών.
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-2">Κατάσταση "Εγκρίθηκε"</h4>
              <p className="text-gray-600">
                Η επιδότηση εγκρίθηκε! Ο επαγγελματίας θα επικοινωνήσει μαζί σας για επιβεβαίωση.
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
