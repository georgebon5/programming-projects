// Help Requests List Page - Αιτήματα Βοήθειας
'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { useHelpRequests } from '@/hooks/useHelpRequests'
import { Heart, MapPin, Clock, User, AlertCircle, Plus, ArrowLeft, CheckCircle } from 'lucide-react'

const categoryLabels: Record<string, string> = {
  moving: 'Μετακόμιση/Μεταφορά',
  technology: 'Τεχνολογία',
  companionship: 'Συντροφιά',
  shopping: 'Ψώνια',
  paperwork: 'Γραφειοκρατία',
  home_maintenance: 'Συντήρηση Σπιτιού',
  childcare: 'Φύλαξη Παιδιών',
  pet_care: 'Φροντίδα Κατοικιδίων',
  other: 'Άλλο',
}

// Category icons (minimal design - no emojis, using text)
const categoryIcons: Record<string, string> = {
  moving: '📦',
  technology: '💻',
  companionship: '👥',
  shopping: '🛒',
  paperwork: '📄',
  home_maintenance: '🔧',
  childcare: '👶',
  pet_care: '🐕',
  other: '•',
}

const urgencyLabels: Record<string, string> = {
  low: 'Χαμηλή',
  medium: 'Μέτρια',
  high: 'Υψηλή',
}

const urgencyColors: Record<string, string> = {
  low: 'bg-blue-100 text-blue-800 border-blue-200',
  medium: 'bg-yellow-100 text-yellow-800 border-yellow-200',
  high: 'bg-red-100 text-red-800 border-red-200',
}

export default function HelpRequestsPage() {
  const router = useRouter()
  const { user, isAuthenticated } = useAuth()
  const { requests: helpRequests, loading, fetchRequests, assignVolunteer } = useHelpRequests()
  const [filter, setFilter] = useState<'all' | string>('all')
  const [assigning, setAssigning] = useState<string | null>(null)

  useEffect(() => {
    // Fetch open requests
    fetchRequests({ status: 'open' })
  }, [])

  const handleHelp = async (requestId: string) => {
    if (!isAuthenticated) {
      router.push('/auth?mode=signin')
      return
    }

    if (!user?.id) {
      alert('Παρακαλώ συνδεθείτε για να προσφέρετε βοήθεια')
      return
    }

    setAssigning(requestId)
    const success = await assignVolunteer(requestId, user.id)
    setAssigning(null)

    if (success) {
      alert('Ευχαριστούμε! Η βοήθειά σας καταχωρήθηκε επιτυχώς.')
      fetchRequests({ status: 'open' }) // Refresh list
    }
  }

  const filteredRequests = filter === 'all' 
    ? helpRequests 
    : helpRequests.filter(r => r.category === filter)

  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-pink-50 to-rose-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-pink-600 mx-auto mb-4"></div>
          <p className="text-gray-600">Φόρτωση αιτημάτων...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-pink-50 to-rose-50 p-4 sm:p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <button
            onClick={() => router.push('/dashboard')}
            className="flex items-center gap-2 text-gray-600 hover:text-gray-800 mb-4 transition"
          >
            <ArrowLeft className="w-5 h-5" />
            <span>Πίσω στο Dashboard</span>
          </button>
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div>
              <h1 className="text-4xl font-bold text-gray-800 mb-2">
                Αιτήματα Βοήθειας
              </h1>
              <p className="text-gray-600">
                Προσφέρετε τη βοήθειά σας σε συνδημότες που τη χρειάζονται
              </p>
            </div>
            <button
              onClick={() => router.push('/help/new')}
              className="flex items-center gap-2 bg-gradient-to-r from-pink-600 to-rose-600 text-white px-6 py-3 rounded-lg font-semibold hover:from-pink-700 hover:to-rose-700 transition shadow-lg"
            >
              <Plus className="w-5 h-5" />
              Νέο Αίτημα
            </button>
          </div>
        </div>

        {/* Info Banner */}
        <div className="bg-gradient-to-r from-pink-500 to-rose-600 rounded-2xl p-6 mb-8 text-white shadow-lg">
          <div className="flex items-start gap-3">
            <Heart className="w-6 h-6 flex-shrink-0 mt-1" />
            <div>
              <h3 className="font-semibold text-lg mb-2">Πώς λειτουργεί το σύστημα;</h3>
              <ul className="space-y-1 text-sm opacity-90">
                <li>✓ Κάθε πολίτης μπορεί να ζητήσει ή να προσφέρει βοήθεια</li>
                <li>✓ Δωρεάν εθελοντική προσφορά - χωρίς χρηματικές συναλλαγές</li>
                <li>✓ Ενισχύουμε τους δεσμούς της κοινότητας μας</li>
              </ul>
            </div>
          </div>
        </div>

        {/* Category Filters */}
        <div className="flex flex-wrap gap-3 mb-8">
          <button
            onClick={() => setFilter('all')}
            className={`px-4 py-2 rounded-lg font-medium transition ${
              filter === 'all'
                ? 'bg-pink-600 text-white shadow-lg'
                : 'bg-white text-gray-700 hover:bg-gray-50'
            }`}
          >
            Όλα ({helpRequests.length})
          </button>
          {Object.entries(categoryLabels).map(([key, label]) => {
            const count = helpRequests.filter(r => r.category === key).length
            if (count === 0) return null
            return (
              <button
                key={key}
                onClick={() => setFilter(key)}
                className={`px-4 py-2 rounded-lg font-medium transition ${
                  filter === key
                    ? 'bg-pink-600 text-white shadow-lg'
                    : 'bg-white text-gray-700 hover:bg-gray-50'
                }`}
              >
                {categoryIcons[key]} {label} ({count})
              </button>
            )
          })}
        </div>

        {/* Help Requests Grid */}
        {filteredRequests.length === 0 ? (
          <div className="bg-white rounded-2xl shadow-lg p-12 text-center">
            <Heart className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-xl font-semibold text-gray-800 mb-2">
              Δεν υπάρχουν ανοιχτά αιτήματα
            </h3>
            <p className="text-gray-600 mb-6">
              {filter === 'all' 
                ? 'Δεν υπάρχουν αιτήματα βοήθειας αυτή τη στιγμή' 
                : `Δεν υπάρχουν αιτήματα στην κατηγορία "${categoryLabels[filter]}"`
              }
            </p>
            <button
              onClick={() => router.push('/help/new')}
              className="bg-gradient-to-r from-pink-600 to-rose-600 text-white px-6 py-3 rounded-lg font-semibold hover:from-pink-700 hover:to-rose-700 transition shadow-lg inline-flex items-center gap-2"
            >
              <Plus className="w-5 h-5" />
              Δημιουργία Αιτήματος
            </button>
          </div>
        ) : (
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
            {filteredRequests.map((request) => {
              const createdDate = new Date(request.createdAt)
              const timeAgo = getTimeAgo(createdDate)

              return (
                <div
                  key={request.id}
                  className="bg-white rounded-2xl shadow-lg hover:shadow-xl transition overflow-hidden flex flex-col"
                >
                  {/* Header with Category Icon */}
                  <div className="bg-gradient-to-r from-pink-500 to-rose-600 p-4 text-white">
                    <div className="flex items-center justify-between mb-2">
                      <div className="text-3xl">
                        {categoryIcons[request.category]}
                      </div>
                      <div className={`px-3 py-1 rounded-lg border text-xs font-medium ${urgencyColors[request.urgency]}`}>
                        {urgencyLabels[request.urgency]}
                      </div>
                    </div>
                    <h3 className="text-lg font-bold">
                      {categoryLabels[request.category]}
                    </h3>
                  </div>

                  {/* Content */}
                  <div className="p-5 flex-1 flex flex-col">
                    <p className="text-gray-700 mb-4 line-clamp-3">
                      {request.description}
                    </p>

                    <div className="space-y-2 text-sm text-gray-600 mb-4">
                      {request.location && (
                        <div className="flex items-start gap-2">
                          <MapPin className="w-4 h-4 text-gray-400 flex-shrink-0 mt-0.5" />
                          <span>{request.location}</span>
                        </div>
                      )}
                      
                      {request.preferredDate && (
                        <div className="flex items-center gap-2">
                          <Clock className="w-4 h-4 text-gray-400" />
                          <span>
                            Προτιμώμενη ημερομηνία: {new Date(request.preferredDate).toLocaleDateString('el-GR')}
                          </span>
                        </div>
                      )}

                      <div className="flex items-center gap-2">
                        <User className="w-4 h-4 text-gray-400" />
                        <span className="text-xs text-gray-500">Δημοσιεύτηκε {timeAgo}</span>
                      </div>
                    </div>

                    {/* Help Button */}
                    <button
                      onClick={() => handleHelp(request.id)}
                      disabled={assigning === request.id}
                      className="w-full bg-gradient-to-r from-pink-600 to-rose-600 text-white py-3 rounded-lg font-semibold hover:from-pink-700 hover:to-rose-700 transition shadow-lg disabled:opacity-50 disabled:cursor-not-allowed flex items-center justify-center gap-2 mt-auto"
                    >
                      {assigning === request.id ? (
                        <>
                          <div className="animate-spin rounded-full h-5 w-5 border-b-2 border-white"></div>
                          Καταχώρηση...
                        </>
                      ) : (
                        <>
                          <Heart className="w-5 h-5" />
                          Θέλω να Βοηθήσω
                        </>
                      )}
                    </button>
                  </div>
                </div>
              )
            })}
          </div>
        )}

        {/* Info Section */}
        <div className="mt-8 bg-white rounded-2xl shadow-lg p-6">
          <h3 className="text-lg font-bold text-gray-800 mb-4">
            Οδηγίες για Εθελοντές
          </h3>
          <div className="grid grid-cols-1 md:grid-cols-2 gap-6 text-sm text-gray-700">
            <div>
              <h4 className="font-semibold mb-2 flex items-center gap-2">
                <CheckCircle className="w-5 h-5 text-green-600" />
                Πώς να βοηθήσω;
              </h4>
              <p className="text-gray-600">
                Πατήστε "Θέλω να Βοηθήσω" σε ένα αίτημα που σας ενδιαφέρει. Θα λάβετε τα στοιχεία επικοινωνίας για να συνεννοηθείτε.
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-2 flex items-center gap-2">
                <Heart className="w-5 h-5 text-pink-600" />
                Δωρεάν προσφορά
              </h4>
              <p className="text-gray-600">
                Όλες οι υπηρεσίες είναι εθελοντικές και δωρεάν. Δεν επιτρέπονται χρηματικές συναλλαγές.
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-2 flex items-center gap-2">
                <AlertCircle className="w-5 h-5 text-yellow-600" />
                Ασφάλεια
              </h4>
              <p className="text-gray-600">
                Συναντηθείτε σε δημόσιους χώρους όταν είναι δυνατόν και ενημερώστε κάποιον για το ραντεβού σας.
              </p>
            </div>
            <div>
              <h4 className="font-semibold mb-2 flex items-center gap-2">
                <Clock className="w-5 h-5 text-blue-600" />
                Αξιοπιστία
              </h4>
              <p className="text-gray-600">
                Αν αναλάβετε να βοηθήσετε, παρακαλούμε να τηρήσετε τη δέσμευσή σας ή να ενημερώσετε έγκαιρα.
              </p>
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}

function getTimeAgo(date: Date): string {
  const seconds = Math.floor((new Date().getTime() - date.getTime()) / 1000)
  
  let interval = seconds / 31536000
  if (interval > 1) return Math.floor(interval) + ' έτη πριν'
  
  interval = seconds / 2592000
  if (interval > 1) return Math.floor(interval) + ' μήνες πριν'
  
  interval = seconds / 86400
  if (interval > 1) return Math.floor(interval) + ' ημέρες πριν'
  
  interval = seconds / 3600
  if (interval > 1) return Math.floor(interval) + ' ώρες πριν'
  
  interval = seconds / 60
  if (interval > 1) return Math.floor(interval) + ' λεπτά πριν'
  
  return 'μόλις τώρα'
}
