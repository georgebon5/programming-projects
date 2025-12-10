'use client'
import { useState, useEffect } from 'react'
import { useRouter } from 'next/navigation'
import { ChevronLeftIcon, MapPinIcon, CurrencyEuroIcon, InformationCircleIcon } from '@heroicons/react/24/outline'
import { ProjectCategory } from '@/types'
import { useAuth } from '@/hooks/useAuth'

interface ProjectForm {
  title: string
  description: string
  category: ProjectCategory | ''
  budgetNeeded: string
  location: {
    address: string
    district: string
    lat: number
    lng: number
  }
}

export default function CreateProjectPage() {
  const router = useRouter()
  const { user, isAuthenticated, loading } = useAuth()
  const [isSubmitting, setIsSubmitting] = useState(false)
  const [formData, setFormData] = useState<ProjectForm>({
    title: '',
    description: '',
    category: '',
    budgetNeeded: '',
    location: {
      address: '',
      district: '',
      lat: 37.9755,
      lng: 23.7348
    }
  })

  const districts = [
    'Κέντρο Αθήνας',
    'Εξάρχεια',
    'Κολωνάκι',
    'Ψυρρή',
    'Πλάκα',
    'Μοναστηράκι',
    'Θησείο',
    'Γκάζι',
    'Κεραμεικός',
    'Παγκράτι',
    'Κυψέλη',
    'Άλλο'
  ]

  // Redirect if not authenticated (only after loading is complete)
  useEffect(() => {
    if (!loading && !isAuthenticated) {
      console.log('❌ User not authenticated, redirecting to /auth')
      router.push('/auth')
    }
  }, [loading, isAuthenticated, router])

  // Show loading state while checking authentication
  if (loading) {
    return (
      <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-900 mx-auto mb-4"></div>
          <p className="text-gray-600 text-lg">Φόρτωση...</p>
        </div>
      </div>
    )
  }

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    setIsSubmitting(true)

    try {
      const response = await fetch('/api/projects', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          ...formData,
          budgetNeeded: parseFloat(formData.budgetNeeded),
          creatorId: user?.id || '1',
          creatorName: user?.name || 'Χρήστης',
        }),
      })

      if (response.ok) {
        const newProject = await response.json()
        alert('Το έργο δημιουργήθηκε επιτυχώς! Αναμένει έγκριση από τον Δήμο.')
        router.push('/projects')
      } else {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to create project')
      }
    } catch (error: any) {
      console.error('Error creating project:', error)
      alert(error.message || 'Σφάλμα κατά τη δημιουργία του έργου. Παρακαλώ προσπαθήστε ξανά.')
    } finally {
      setIsSubmitting(false)
    }
  }

  const handleInputChange = (field: string, value: string) => {
    if (field.startsWith('location.')) {
      const locationField = field.split('.')[1]
      setFormData(prev => ({
        ...prev,
        location: {
          ...prev.location,
          [locationField]: value
        }
      }))
    } else {
      setFormData(prev => ({
        ...prev,
        [field]: value
      }))
    }
  }

  return (
    <div className="min-h-screen bg-gradient-to-br from-purple-50 via-pink-50 to-orange-50">
      {/* Header */}
      <div className="bg-white shadow-sm border-b">
        <div className="max-w-4xl mx-auto px-4 py-4">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.push('/projects')}
              className="flex items-center text-gray-600 hover:text-gray-900 transition-colors"
            >
              <ChevronLeftIcon className="h-5 w-5 mr-2" />
              Επιστροφή στα Έργα
            </button>
            <span className="text-gray-400">|</span>
            <button
              onClick={() => router.push('/')}
              className="flex items-center text-gray-600 hover:text-gray-900 transition-colors"
            >
              <ChevronLeftIcon className="h-5 w-5 mr-2" />
              Αρχική Σελίδα
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-4xl mx-auto px-4 py-8">
        {/* Page Title */}
        <div className="text-center mb-8">
          <h1 className="text-4xl font-bold text-gray-900 mb-4">Δημιουργία Νέου Έργου</h1>
          <p className="text-xl text-gray-600 max-w-2xl mx-auto">
            Προτείνετε ένα νέο έργο για τη γειτονιά σας και συλλέξτε υποστήριξη από την κοινότητα
          </p>
        </div>

        {/* Form */}
        <div className="bg-white rounded-2xl shadow-lg overflow-hidden">
          <form onSubmit={handleSubmit} className="p-8 space-y-8">
            {/* Basic Information */}
            <div className="space-y-6">
              <div className="border-b border-gray-200 pb-4">
                <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                  <InformationCircleIcon className="h-6 w-6 mr-2 text-pink-600" />
                  Βασικές Πληροφορίες
                </h2>
              </div>

              <div>
                <label htmlFor="title" className="block text-sm font-medium text-gray-700 mb-2">
                  Τίτλος Έργου *
                </label>
                <input
                  type="text"
                  id="title"
                  value={formData.title}
                  onChange={(e) => handleInputChange('title', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-pink-500 text-gray-900 bg-white placeholder:text-gray-500"
                  placeholder="π.χ. Επισκευή παιδικής χαράς"
                  required
                />
              </div>

              <div>
                <label htmlFor="description" className="block text-sm font-medium text-gray-700 mb-2">
                  Περιγραφή *
                </label>
                <textarea
                  id="description"
                  rows={5}
                  value={formData.description}
                  onChange={(e) => handleInputChange('description', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-pink-500 text-gray-900 bg-white placeholder:text-gray-500"
                  placeholder="Περιγράψτε λεπτομερώς το έργο, τι χρειάζεται να γίνει και γιατί είναι σημαντικό για τη γειτονιά..."
                  required
                />
                <p className="mt-2 text-sm text-gray-500">
                  Ελάχιστο 50 χαρακτήρες. Περιγράψτε το πρόβλημα και την προτεινόμενη λύση.
                </p>
              </div>

              <div>
                <label htmlFor="category" className="block text-sm font-medium text-gray-700 mb-2">
                  Κατηγορία *
                </label>
                <select
                  id="category"
                  value={formData.category}
                  onChange={(e) => handleInputChange('category', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-pink-500 text-gray-900 bg-white"
                  required
                >
                  <option value="">Επιλέξτε κατηγορία</option>
                  <option value="infrastructure">Υποδομές</option>
                  <option value="environment">Περιβάλλον</option>
                  <option value="community">Κοινότητα</option>
                  <option value="parks">Πάρκα</option>
                  <option value="culture">Πολιτισμός</option>
                  <option value="safety">Ασφάλεια</option>
                  <option value="other">Άλλο</option>
                </select>
              </div>
            </div>

            {/* Location Information */}
            <div className="space-y-6">
              <div className="border-b border-gray-200 pb-4">
                <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                  <MapPinIcon className="h-6 w-6 mr-2 text-pink-600" />
                  Τοποθεσία
                </h2>
              </div>

              <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                <div>
                  <label htmlFor="district" className="block text-sm font-medium text-gray-700 mb-2">
                    Περιοχή *
                  </label>
                  <select
                    id="district"
                    value={formData.location.district}
                    onChange={(e) => handleInputChange('location.district', e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-pink-500 text-gray-900 bg-white"
                    required
                  >
                    <option value="">Επιλέξτε περιοχή</option>
                    {districts.map(district => (
                      <option key={district} value={district}>{district}</option>
                    ))}
                  </select>
                </div>

                <div>
                  <label htmlFor="address" className="block text-sm font-medium text-gray-700 mb-2">
                    Διεύθυνση *
                  </label>
                  <input
                    type="text"
                    id="address"
                    value={formData.location.address}
                    onChange={(e) => handleInputChange('location.address', e.target.value)}
                    className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-pink-500 text-gray-900 bg-white placeholder:text-gray-500"
                    placeholder="π.χ. Πλατεία Εξαρχείων"
                    required
                  />
                </div>
              </div>
            </div>

            {/* Budget Information */}
            <div className="space-y-6">
              <div className="border-b border-gray-200 pb-4">
                <h2 className="text-2xl font-bold text-gray-900 flex items-center">
                  <CurrencyEuroIcon className="h-6 w-6 mr-2 text-pink-600" />
                  Προϋπολογισμός
                </h2>
              </div>

              <div>
                <label htmlFor="budget" className="block text-sm font-medium text-gray-700 mb-2">
                  Εκτιμώμενο Κόστος (€) *
                </label>
                <input
                  type="number"
                  id="budget"
                  min="1"
                  step="0.01"
                  value={formData.budgetNeeded}
                  onChange={(e) => handleInputChange('budgetNeeded', e.target.value)}
                  className="w-full px-4 py-3 border border-gray-300 rounded-lg focus:ring-2 focus:ring-pink-500 focus:border-pink-500 text-gray-900 bg-white placeholder:text-gray-500"
                  placeholder="π.χ. 1500"
                  required
                />
                <p className="mt-2 text-sm text-gray-500">
                  Εκτιμήστε το συνολικό κόστος υλικών και εργασίας που χρειάζεται.
                </p>
              </div>
            </div>

            {/* Important Notes */}
            <div className="bg-blue-50 border-l-4 border-blue-400 p-6 rounded-lg">
              <h3 className="text-lg font-semibold text-blue-900 mb-2">Σημαντικές Πληροφορίες</h3>
              <ul className="text-blue-800 space-y-2">
                <li>• Το έργο θα χρειαστεί έγκριση από τον αρμόδιο δήμο</li>
                <li>• Η κοινότητα μπορεί να συμβάλει με χρήματα, χρόνο ή υλικά</li>
                <li>• Θα λάβετε ειδοποιήσεις για την πρόοδο του έργου</li>
                <li>• Μπορείτε να επεξεργαστείτε το έργο μετά τη δημιουργία</li>
              </ul>
            </div>

            {/* Submit Button */}
            <div className="flex justify-end space-x-4 pt-6 border-t border-gray-200">
              <button
                type="button"
                onClick={() => router.push('/projects')}
                className="px-8 py-3 border border-gray-300 rounded-lg text-gray-700 hover:bg-gray-50 transition-colors"
                disabled={isSubmitting}
              >
                Άκυρο
              </button>
              <button
                type="submit"
                disabled={isSubmitting}
                className="px-8 py-3 bg-gradient-to-r from-pink-600 to-orange-600 text-white rounded-lg font-semibold hover:from-pink-700 hover:to-orange-700 transition-all duration-200 transform hover:scale-105 shadow-lg disabled:opacity-50 disabled:cursor-not-allowed disabled:transform-none"
              >
                {isSubmitting ? 'Δημιουργία...' : 'Δημιουργία Έργου'}
              </button>
            </div>
          </form>
        </div>

        {/* Help Text */}
        <div className="text-center mt-8 text-gray-600">
          <p>Χρειάζεστε βοήθεια; <a href="/help" className="text-pink-600 hover:text-pink-700 font-medium">Επικοινωνήστε μαζί μας</a></p>
        </div>
      </div>
    </div>
  )
}
