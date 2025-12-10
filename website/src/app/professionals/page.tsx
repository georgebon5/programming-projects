// Professionals List Page - Λίστα Ειδικών
'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useProfessionals } from '@/hooks/useProfessionals'
import { useAuth } from '@/hooks/useAuth'

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

export default function ProfessionalsPage() {
  const router = useRouter()
  const { user, isAuthenticated } = useAuth()
  const { professionals, loading, fetchProfessionals } = useProfessionals()
  const [selectedProfession, setSelectedProfession] = useState<string>('all')

  useEffect(() => {
    // Fetch all approved professionals
    fetchProfessionals({ approved: true })
  }, [])

  const handleFilterChange = async (profession: string) => {
    setSelectedProfession(profession)
    if (profession === 'all') {
      await fetchProfessionals({ approved: true })
    } else {
      await fetchProfessionals({ profession, approved: true })
    }
  }

  const handleBooking = (professionalId: string) => {
    if (!isAuthenticated) {
      router.push('/auth?mode=signin')
      return
    }
    router.push(`/bookings/new?professionalId=${professionalId}`)
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-100 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-900 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Φόρτωση ειδικών...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-white to-blue-100">
      {/* Navigation */}
      <nav className="bg-white shadow-sm sticky top-0 z-50">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <div className="flex justify-between items-center h-16">
            <button 
              onClick={() => router.push('/')} 
              className="text-2xl font-bold text-gray-900"
            >
              HelpMeAnytime
            </button>
            <div className="flex items-center gap-4">
              {isAuthenticated ? (
                <>
                  <button onClick={() => router.push('/dashboard')} className="text-gray-600 hover:text-blue-900">
                    Dashboard
                  </button>
                  <span className="text-sm text-gray-600">
                    {user?.name || user?.email}
                  </span>
                </>
              ) : (
                <button
                  onClick={() => router.push('/auth')}
                  className="px-4 py-2 bg-blue-900 text-white rounded-lg hover:bg-blue-800"
                >
                  Σύνδεση
                </button>
              )}
            </div>
          </div>
        </div>
      </nav>

      {/* Header */}
      <div className="bg-gradient-to-r from-blue-900 to-blue-800 text-white py-12">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
          <h1 className="text-4xl font-bold mb-4">Βρες Ειδικό με Επιδότηση Δήμου</h1>
          <p className="text-xl text-blue-100">
            Κλείσε ραντεβού με πιστοποιημένους επαγγελματίες σε χαμηλές τιμές
          </p>
          <div className="mt-4 flex items-center gap-3">
            <div className="bg-white/20 backdrop-blur-sm px-4 py-2 rounded-lg">
              <span className="text-sm">Έως 70% επιδότηση</span>
            </div>
            <div className="bg-white/20 backdrop-blur-sm px-4 py-2 rounded-lg">
              <span className="text-sm">Πιστοποιημένοι ειδικοί</span>
            </div>
            <div className="bg-white/20 backdrop-blur-sm px-4 py-2 rounded-lg">
              <span className="text-sm">Αξιολογήσεις χρηστών</span>
            </div>
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-12">
        {/* Filters */}
        <div className="mb-8">
          <h2 className="text-lg font-semibold text-gray-900 mb-4">Επάγγελμα</h2>
          <div className="flex flex-wrap gap-3">
            <button
              onClick={() => handleFilterChange('all')}
              className={`px-6 py-2 rounded-full transition ${
                selectedProfession === 'all'
                  ? 'bg-blue-900 text-white'
                  : 'bg-white text-gray-700 hover:bg-gray-100'
              } shadow-md`}
            >
              Όλοι
            </button>
            {Object.entries(professionLabels).map(([key, label]) => (
              <button
                key={key}
                onClick={() => handleFilterChange(key)}
                className={`px-6 py-2 rounded-full transition ${
                  selectedProfession === key
                    ? 'bg-blue-900 text-white'
                    : 'bg-white text-gray-700 hover:bg-gray-100'
                } shadow-md`}
              >
                {label}
              </button>
            ))}
          </div>
        </div>

        {/* Results Count */}
        <div className="mb-6">
          <p className="text-gray-600">
            Βρέθηκαν <strong>{professionals.length}</strong> διαθέσιμοι ειδικοί
          </p>
        </div>

        {/* Professionals Grid */}
        {professionals.length === 0 ? (
          <div className="text-center py-12">
            <h3 className="text-2xl font-bold text-gray-900 mb-2">
              Δεν βρέθηκαν ειδικοί
            </h3>
            <p className="text-gray-600">
              Δοκίμασε να αλλάξεις τα φίλτρα αναζήτησης
            </p>
          </div>
        ) : (
          <div className="grid md:grid-cols-2 lg:grid-cols-3 gap-6">
            {professionals.map((professional) => (
              <div
                key={professional.id}
                className="bg-white rounded-2xl shadow-lg hover:shadow-2xl transition transform hover:-translate-y-2 overflow-hidden"
              >
                {/* Professional Header */}
                <div className="bg-gradient-to-r from-blue-900 to-blue-800 p-6 text-white">
                  <div className="flex items-center gap-4">
                    <div className="w-16 h-16 bg-white/20 rounded-full flex items-center justify-center text-3xl backdrop-blur-sm">
                      <span className="text-2xl font-bold">{professional.name.charAt(0)}</span>
                    </div>
                    <div>
                      <h3 className="text-xl font-bold">{professional.name}</h3>
                      <p className="text-blue-100">
                        {professionLabels[professional.profession] || professional.profession}
                      </p>
                    </div>
                  </div>
                </div>

                {/* Professional Details */}
                <div className="p-6">
                  {/* Rating */}
                  <div className="flex items-center gap-2 mb-4">
                    <div className="flex items-center">
                      {[...Array(5)].map((_, i) => (
                        <span key={i} className={i < Math.floor(professional.rating) ? 'text-yellow-400 text-xl' : 'text-gray-300 text-xl'}>
                          ★
                        </span>
                      ))}
                    </div>
                    <span className="text-sm text-gray-600">
                      {professional.rating} ({professional.totalReviews} αξιολογήσεις)
                    </span>
                  </div>

                  {/* Bio */}
                  {professional.bio && (
                    <p className="text-gray-600 text-sm mb-4 line-clamp-2">
                      {professional.bio}
                    </p>
                  )}

                  {/* Experience */}
                  <div className="flex items-center gap-2 mb-2 text-sm text-gray-600">
                    <span className="font-semibold">Εμπειρία:</span>
                    <span>{professional.yearsExperience} χρόνια</span>
                  </div>

                  {/* Service Areas */}
                  <div className="flex items-start gap-2 mb-4 text-sm text-gray-600">
                    <span className="font-semibold">Περιοχές:</span>
                    <span>{professional.serviceAreas.join(', ')}</span>
                  </div>

                  {/* Pricing */}
                  <div className="bg-green-50 border-2 border-green-200 rounded-xl p-4 mb-4">
                    <div className="flex items-center justify-between mb-2">
                      <span className="text-sm text-gray-600">Κανονική τιμή:</span>
                      <span className="text-gray-400 line-through">€{professional.hourlyRate}/ώρα</span>
                    </div>
                    <div className="flex items-center justify-between">
                      <span className="font-semibold text-green-700">Πληρώνεις μόνο:</span>
                      <span className="text-2xl font-bold text-green-600">
                        €{professional.subsidizedRate}/ώρα
                      </span>
                    </div>
                    <div className="mt-2 text-xs text-green-600 text-center">
                      Εξοικονόμησε €{professional.hourlyRate - professional.subsidizedRate}/ώρα με επιδότηση δήμου
                    </div>
                  </div>

                  {/* Specializations */}
                  {professional.specializations && professional.specializations.length > 0 && (
                    <div className="mb-4">
                      <div className="flex flex-wrap gap-2">
                        {professional.specializations.slice(0, 3).map((spec, index) => (
                          <span
                            key={index}
                            className="px-3 py-1 bg-blue-100 text-blue-900 text-xs rounded-full font-medium"
                          >
                            {spec}
                          </span>
                        ))}
                      </div>
                    </div>
                  )}

                  {/* Book Button */}
                  <button
                    onClick={() => handleBooking(professional.id)}
                    className="w-full px-6 py-3 bg-blue-900 text-white font-semibold rounded-xl hover:bg-blue-800 transition shadow-lg hover:shadow-xl"
                  >
                    Κλείσε Ραντεβού
                  </button>
                </div>
              </div>
            ))}
          </div>
        )}

        {/* Info Section */}
        <div className="mt-12 bg-blue-50 border-2 border-blue-200 rounded-2xl p-8">
          <h3 className="text-2xl font-bold text-gray-900 mb-4 text-center">
            Πώς Λειτουργεί το Πρόγραμμα Επιδότησης;
          </h3>
          <div className="grid md:grid-cols-3 gap-6">
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-900 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-white text-2xl font-bold">1</span>
              </div>
              <h4 className="font-semibold text-gray-900 mb-2">Επέλεξε Ειδικό</h4>
              <p className="text-gray-600 text-sm">
                Διάλεξε τον επαγγελματία που σου ταιριάζει από τη λίστα μας
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-900 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-white text-2xl font-bold">2</span>
              </div>
              <h4 className="font-semibold text-gray-900 mb-2">Κλείσε Ραντεβού</h4>
              <p className="text-gray-600 text-sm">
                Επέλεξε ημερομηνία και ώρα που σε βολεύει
              </p>
            </div>
            <div className="text-center">
              <div className="w-16 h-16 bg-blue-900 rounded-full flex items-center justify-center mx-auto mb-4">
                <span className="text-white text-2xl font-bold">3</span>
              </div>
              <h4 className="font-semibold text-gray-900 mb-2">Πλήρωσε Μόνο €15-30</h4>
              <p className="text-gray-600 text-sm">
                Ο δήμος καλύπτει το 70% του κόστους
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
