// Booking Form Page - Κλείσιμο Ραντεβού με Επαγγελματία
'use client'

import { useEffect, useState, Suspense } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { useProfessionals } from '@/hooks/useProfessionals'
import { useBookings } from '@/hooks/useBookings'
import { Calendar, Clock, MapPin, Phone, Euro, Info, Check, ArrowLeft } from 'lucide-react'

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

function BookingFormContent() {
  const router = useRouter()
  const searchParams = useSearchParams()
  const { user, isAuthenticated, loading: authLoading } = useAuth()
  const { professionals, fetchProfessionals } = useProfessionals()
  const { createBooking, loading: submitting } = useBookings()

  const professionalIdParam = searchParams.get('professionalId')

  // Get tomorrow's date as default
  const getTomorrowDate = () => {
    const tomorrow = new Date()
    tomorrow.setDate(tomorrow.getDate() + 1)
    return tomorrow.toISOString().split('T')[0]
  }

  const [selectedProfessionalId, setSelectedProfessionalId] = useState(professionalIdParam || '')
  const [appointmentDate, setAppointmentDate] = useState(getTomorrowDate())
  const [appointmentTime, setAppointmentTime] = useState('09:00')
  const [estimatedHours, setEstimatedHours] = useState(2)
  const [serviceAddress, setServiceAddress] = useState('')
  const [phoneNumber, setPhoneNumber] = useState(user?.phone || '')
  const [description, setDescription] = useState('')
  const [submitted, setSubmitted] = useState(false)
  
  // Availability state
  const [availableSlots, setAvailableSlots] = useState<string[]>([])
  const [bookedSlots, setBookedSlots] = useState<string[]>([])
  const [availabilityLoading, setAvailabilityLoading] = useState(false)
  const [showAvailability, setShowAvailability] = useState(false)

  // Debug: Log form values
  console.log('Form values:', {
    selectedProfessionalId,
    appointmentDate,
    appointmentTime,
    serviceAddress,
    phoneNumber,
    description
  })

  // Function to check availability
  const checkAvailability = async (professionalId: string, date: string) => {
    if (!professionalId || !date) return

    try {
      setAvailabilityLoading(true)
      console.log(`🔍 Checking availability for professional ${professionalId} on ${date}`)
      
      const response = await fetch(`/api/availability?professionalId=${professionalId}&date=${date}`)
      
      if (!response.ok) {
        throw new Error('Failed to check availability')
      }

      const data = await response.json()
      console.log('📅 Availability data:', data)
      
      setAvailableSlots(data.availableSlots || [])
      setBookedSlots(data.bookedSlots || [])
      setShowAvailability(true)
      
      // If current selected time is not available, clear it
      if (data.bookedSlots && data.bookedSlots.includes(appointmentTime)) {
        setAppointmentTime('')
      }
    } catch (error) {
      console.error('❌ Error checking availability:', error)
      // Reset availability state on error
      setAvailableSlots([])
      setBookedSlots([])
      setShowAvailability(false)
    } finally {
      setAvailabilityLoading(false)
    }
  }

  // Auto-check availability when professional or date changes
  useEffect(() => {
    if (selectedProfessionalId && appointmentDate) {
      checkAvailability(selectedProfessionalId, appointmentDate)
    } else {
      setShowAvailability(false)
      setAvailableSlots([])
      setBookedSlots([])
    }
  }, [selectedProfessionalId, appointmentDate])

  useEffect(() => {
    // Περίμενε να τελειώσει η φόρτωση του authentication πριν ελέγξεις
    if (authLoading) return
    
    if (!isAuthenticated) {
      console.log('Redirecting to auth - not authenticated')
      router.push('/auth?mode=signin&redirect=/bookings/new')
      return
    }
    console.log('User authenticated, fetching professionals')
    fetchProfessionals({ approved: true })
  }, [isAuthenticated, authLoading, router])

  // Αν φορτώνει το authentication, δείξε loading
  if (authLoading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-600 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Φόρτωση...</p>
        </div>
      </div>
    )
  }

  // Αν δεν είναι authenticated, μην δείξεις τίποτα (θα γίνει redirect)
  if (!isAuthenticated) {
    return null
  }

  const selectedProfessional = professionals.find(p => p.id === selectedProfessionalId)

  // Calculate costs
  const basePrice = selectedProfessional ? selectedProfessional.hourlyRate * estimatedHours : 0
  const municipalitySubsidy = basePrice * 0.7 // 70% επιδότηση
  const citizenPays = basePrice - municipalitySubsidy

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    
    if (!selectedProfessionalId) {
      alert('⚠️ Παρακαλώ επιλέξτε επαγγελματία')
      return
    }
    
    if (!appointmentDate) {
      alert('⚠️ Παρακαλώ επιλέξτε ημερομηνία')
      return
    }
    
    if (!appointmentTime) {
      alert('⚠️ Παρακαλώ επιλέξτε ώρα')
      return
    }
    
    // Check if selected time is available
    if (showAvailability && !availableSlots.includes(appointmentTime)) {
      alert('⚠️ Η επιλεγμένη ώρα δεν είναι πλέον διαθέσιμη. Παρακαλώ επιλέξτε άλλη ώρα.')
      // Refresh availability
      await checkAvailability(selectedProfessionalId, appointmentDate)
      return
    }
    
    if (!serviceAddress.trim()) {
      alert('⚠️ Παρακαλώ συμπληρώστε τη διεύθυνση')
      return
    }
    
    if (!phoneNumber.trim()) {
      alert('⚠️ Παρακαλώ συμπληρώστε το τηλέφωνο επικοινωνίας')
      return
    }

    // Double-check availability before final submission
    console.log('🔍 Final availability check before submission...')
    try {
      const response = await fetch('/api/availability/check', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          professionalId: selectedProfessionalId,
          date: appointmentDate,
          time: appointmentTime,
        }),
      })

      if (!response.ok) {
        throw new Error('Failed to verify availability')
      }

      const availabilityCheck = await response.json()
      
      if (!availabilityCheck.isAvailable) {
        alert(`❌ Η ώρα ${appointmentTime} δεν είναι πλέον διαθέσιμη. Κάποιος άλλος την έκλεισε την ίδια στιγμή. Παρακαλώ επιλέξτε άλλη ώρα.`)
        // Refresh availability
        await checkAvailability(selectedProfessionalId, appointmentDate)
        return
      }

      console.log('✅ Time slot confirmed available, proceeding with booking...')
    } catch (error) {
      console.error('❌ Error checking final availability:', error)
      alert('⚠️ Σφάλμα στον έλεγχο διαθεσιμότητας. Παρακαλώ δοκιμάστε ξανά.')
      return
    }

    const bookingData = {
      citizenId: 'user-citizen-1', // Add the demo citizen ID
      professionalId: selectedProfessionalId,
      serviceType: selectedProfessional?.profession || 'general',
      appointmentDate: `${appointmentDate}T${appointmentTime}`,
      estimatedHours,
      serviceAddress,
      phoneNumber,
      description,
    }

    console.log('Submitting booking data:', bookingData)
    
    const result = await createBooking(bookingData)
    
    if (result) {
      setSubmitted(true)
      setTimeout(() => {
        router.push('/bookings')
      }, 3000)
    } else {
      alert('❌ Παρουσιάστηκε σφάλμα κατά την κράτηση. Παρακαλώ δοκιμάστε ξανά.')
    }
  }

  // Success State
  if (submitted) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-green-50 to-emerald-50 flex items-center justify-center p-4">
        <div className="max-w-md w-full bg-white rounded-2xl shadow-xl p-8 text-center">
          <div className="w-20 h-20 bg-green-500 rounded-full flex items-center justify-center mx-auto mb-6">
            <Check className="w-12 h-12 text-white" />
          </div>
          <h1 className="text-3xl font-bold text-gray-800 mb-4">
            Επιτυχής Κράτηση! 🎉
          </h1>
          <p className="text-gray-600 mb-2">
            Το ραντεβού σας έχει καταχωρηθεί επιτυχώς.
          </p>
          <p className="text-sm text-gray-500 mb-6">
            Θα ενημερωθείτε σύντομα για την έγκριση του Δήμου.
          </p>
          <div className="bg-blue-50 border border-blue-200 rounded-lg p-4">
            <p className="text-sm text-gray-700">
              Θα μεταφερθείτε στη σελίδα των ραντεβού σας...
            </p>
          </div>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 p-4 sm:p-8">
      <div className="max-w-4xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center gap-4 mb-4">
            <button
              onClick={() => router.back()}
              className="flex items-center gap-2 text-gray-600 hover:text-gray-800 transition"
            >
              <ArrowLeft className="w-5 h-5" />
              <span>Πίσω</span>
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
          <h1 className="text-4xl font-bold text-gray-800 mb-2">
            Κλείστε Ραντεβού
          </h1>
          <p className="text-gray-600">
            Επιλέξτε επαγγελματία και συμπληρώστε τα στοιχεία σας
          </p>
        </div>

        {/* Info Card */}
        <div className="bg-gradient-to-r from-blue-500 to-indigo-600 rounded-2xl p-6 mb-8 text-white shadow-lg">
          <div className="flex items-start gap-3">
            <Info className="w-6 h-6 flex-shrink-0 mt-1" />
            <div>
              <h3 className="font-semibold text-lg mb-2">Πώς λειτουργεί η επιδότηση;</h3>
              <ul className="space-y-1 text-sm opacity-90">
                <li>✓ Ο Δήμος καλύπτει το <strong>70%</strong> του κόστους</li>
                <li>✓ Εσείς πληρώνετε μόνο το <strong>30%</strong></li>
                <li>✓ Η έγκριση γίνεται εντός 24-48 ωρών</li>
              </ul>
            </div>
          </div>
        </div>

        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Form */}
          <form onSubmit={handleSubmit} className="lg:col-span-2 space-y-6">
            <div className="bg-white rounded-2xl shadow-lg p-6 sm:p-8">
              <h2 className="text-2xl font-bold text-gray-800 mb-6">
                Στοιχεία Ραντεβού
              </h2>

              {/* Professional Selection */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Επιλογή Επαγγελματία *
                </label>
                <select
                  value={selectedProfessionalId}
                  onChange={(e) => setSelectedProfessionalId(e.target.value)}
                  required
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition text-gray-900 bg-white"
                >
                  <option value="">-- Επιλέξτε Επαγγελματία --</option>
                  {professionals.map((prof) => (
                    <option key={prof.id} value={prof.id}>
                      {prof.name} - {professionLabels[prof.profession]} (€{prof.hourlyRate}/ώρα)
                    </option>
                  ))}
                </select>
              </div>

              {/* Date and Time */}
              <div className="grid grid-cols-1 sm:grid-cols-2 gap-4 mb-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <Calendar className="w-4 h-4 inline mr-1" />
                    Ημερομηνία *
                  </label>
                  <input
                    type="date"
                    value={appointmentDate}
                    onChange={(e) => setAppointmentDate(e.target.value)}
                    min={new Date().toISOString().split('T')[0]}
                    required
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition text-gray-900 bg-white"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    <Clock className="w-4 h-4 inline mr-1" />
                    Ώρα *
                    {availabilityLoading && <span className="text-blue-600 text-xs ml-2">(Έλεγχος διαθεσιμότητας...)</span>}
                  </label>
                  
                  {showAvailability ? (
                    <div>
                      <select
                        value={appointmentTime}
                        onChange={(e) => setAppointmentTime(e.target.value)}
                        required
                        className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition text-gray-900 bg-white"
                        disabled={availabilityLoading}
                      >
                        <option value="">-- Επιλέξτε Ώρα --</option>
                        {availableSlots.length > 0 ? (
                          availableSlots.map((slot) => (
                            <option key={slot} value={slot}>
                              {slot} ✅ Διαθέσιμο
                            </option>
                          ))
                        ) : (
                          <option disabled>Δεν υπάρχουν διαθέσιμες ώρες</option>
                        )}
                      </select>
                      
                      {/* Show availability info */}
                      <div className="mt-2 text-xs">
                        {availableSlots.length > 0 ? (
                          <p className="text-green-600">
                            ✅ {availableSlots.length} διαθέσιμες ώρες
                          </p>
                        ) : (
                          <p className="text-red-600">
                            ❌ Δεν υπάρχουν διαθέσιμες ώρες για την επιλεγμένη ημερομηνία
                          </p>
                        )}
                        
                        {bookedSlots.length > 0 && (
                          <p className="text-orange-600 mt-1">
                            🚫 Κλεισμένες ώρες: {bookedSlots.join(', ')}
                          </p>
                        )}
                      </div>
                    </div>
                  ) : (
                    <select
                      disabled
                      className="w-full px-4 py-3 border border-gray-300 rounded-lg bg-gray-100 text-gray-500"
                    >
                      <option>
                        {!selectedProfessionalId ? 'Επιλέξτε πρώτα επαγγελματία' : 
                         !appointmentDate ? 'Επιλέξτε ημερομηνία' : 
                         'Έλεγχος διαθεσιμότητας...'}
                      </option>
                    </select>
                  )}
                </div>
              </div>

              {/* Estimated Hours */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Εκτιμώμενες Ώρες Εργασίας
                </label>
                <div className="flex items-center gap-4">
                  <input
                    type="range"
                    min="1"
                    max="8"
                    step="0.5"
                    value={estimatedHours}
                    onChange={(e) => setEstimatedHours(parseFloat(e.target.value))}
                    className="flex-1"
                  />
                  <span className="bg-blue-100 text-blue-800 px-4 py-2 rounded-lg font-semibold min-w-[80px] text-center">
                    {estimatedHours} ώρες
                  </span>
                </div>
              </div>

              {/* Service Address */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <MapPin className="w-4 h-4 inline mr-1" />
                  Διεύθυνση Υπηρεσίας *
                </label>
                <input
                  type="text"
                  value={serviceAddress}
                  onChange={(e) => setServiceAddress(e.target.value)}
                  placeholder="π.χ. Ακαδημίας 123, Αθήνα"
                  required
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition text-gray-900 bg-white placeholder:text-gray-500"
                />
              </div>

              {/* Phone Number */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  <Phone className="w-4 h-4 inline mr-1" />
                  Τηλέφωνο Επικοινωνίας *
                </label>
                <input
                  type="tel"
                  value={phoneNumber}
                  onChange={(e) => setPhoneNumber(e.target.value)}
                  placeholder="210 123 4567"
                  required
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition text-gray-900 bg-white placeholder:text-gray-500"
                />
              </div>

              {/* Description */}
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Περιγραφή Εργασίας (προαιρετικό)
                </label>
                <textarea
                  value={description}
                  onChange={(e) => setDescription(e.target.value)}
                  rows={4}
                  placeholder="Περιγράψτε το πρόβλημα ή την εργασία που χρειάζεται..."
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent transition resize-none text-gray-900 bg-white placeholder:text-gray-500"
                />
              </div>

              {/* Submit Button */}
              <button
                type="submit"
                disabled={submitting}
                className="w-full bg-gradient-to-r from-blue-600 to-indigo-600 text-white py-4 rounded-lg font-semibold hover:from-blue-700 hover:to-indigo-700 transition shadow-lg disabled:opacity-50 disabled:cursor-not-allowed"
              >
                {submitting ? 'Υποβολή...' : 'Κλείσιμο Ραντεβού'}
              </button>
            </div>
          </form>

          {/* Cost Summary Sidebar */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-2xl shadow-lg p-6 sticky top-8">
              <h3 className="text-xl font-bold text-gray-800 mb-4">
                Κόστος Υπηρεσίας
              </h3>

              {selectedProfessional ? (
                <div className="space-y-4">
                  {/* Professional Info */}
                  <div className="pb-4 border-b border-gray-200">
                    <p className="text-sm text-gray-600">Επαγγελματίας</p>
                    <p className="font-semibold text-gray-800">{selectedProfessional.name}</p>
                    <p className="text-xs text-gray-500">
                      {professionLabels[selectedProfessional.profession]}
                    </p>
                  </div>

                  {/* Cost Breakdown */}
                  <div className="space-y-3">
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Ωριαία χρέωση:</span>
                      <span className="font-medium">€{selectedProfessional.hourlyRate}</span>
                    </div>
                    <div className="flex justify-between text-sm">
                      <span className="text-gray-600">Ώρες εργασίας:</span>
                      <span className="font-medium">{estimatedHours}h</span>
                    </div>
                    <div className="border-t border-gray-200 pt-3">
                      <div className="flex justify-between text-sm mb-2">
                        <span className="text-gray-600">Συνολικό κόστος:</span>
                        <span className="font-medium">€{basePrice.toFixed(2)}</span>
                      </div>
                      <div className="flex justify-between text-sm text-green-600 mb-2">
                        <span>Επιδότηση Δήμου (70%):</span>
                        <span className="font-medium">-€{municipalitySubsidy.toFixed(2)}</span>
                      </div>
                    </div>
                  </div>

                  {/* Final Amount */}
                  <div className="bg-gradient-to-r from-blue-50 to-indigo-50 border-2 border-blue-200 rounded-lg p-4">
                    <div className="flex justify-between items-center">
                      <span className="text-gray-700 font-medium">Πληρώνετε εσείς:</span>
                      <div className="text-right">
                        <div className="text-2xl font-bold text-blue-600">
                          €{citizenPays.toFixed(2)}
                        </div>
                        <div className="text-xs text-green-600 font-medium">
                          Εξοικονόμηση €{municipalitySubsidy.toFixed(2)}!
                        </div>
                      </div>
                    </div>
                  </div>

                  {/* Rating */}
                  <div className="pt-4 border-t border-gray-200">
                    <p className="text-sm text-gray-600 mb-1">Αξιολόγηση</p>
                    <div className="flex items-center gap-2">
                      <div className="flex">
                        {[...Array(5)].map((_, i) => (
                          <span key={i} className={i < Math.floor(selectedProfessional.rating) ? 'text-yellow-400' : 'text-gray-300'}>
                            ★
                          </span>
                        ))}
                      </div>
                      <span className="text-sm font-semibold text-gray-700">
                        {selectedProfessional.rating}/5
                      </span>
                    </div>
                  </div>
                </div>
              ) : (
                <div className="text-center py-8 text-gray-500">
                  <Euro className="w-12 h-12 mx-auto mb-3 opacity-30" />
                  <p className="text-sm">Επιλέξτε επαγγελματία για να δείτε το κόστος</p>
                </div>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

export default function BookingFormPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen bg-gradient-to-br from-blue-50 to-indigo-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Φόρτωση...</p>
        </div>
      </div>
    }>
      <BookingFormContent />
    </Suspense>
  )
}
