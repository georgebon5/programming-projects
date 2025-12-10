'use client'
import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { ChevronLeftIcon, MapPinIcon, CalendarIcon, UserIcon, CurrencyEuroIcon } from '@heroicons/react/24/outline'
import { CheckCircleIcon, ClockIcon, ExclamationCircleIcon } from '@heroicons/react/24/solid'

interface Project {
  id: string
  title: string
  description: string
  category: string
  budgetNeeded: number
  budgetPledged: number
  status: string
  location: {
    address: string
    district: string
  }
  createdAt: string
  municipalityApproved?: boolean
}

interface Pledge {
  id: string
  projectId: string
  userId: string
  type: 'money' | 'time' | 'materials'
  amount?: number
  hours?: number
  materials?: string
  description: string
  status: string
  createdAt: string
}

export default function ProjectPage({ params }: { params: { id: string } }) {
  const router = useRouter()
  const [project, setProject] = useState<Project | null>(null)
  const [pledges, setPledges] = useState<Pledge[]>([])
  const [loading, setLoading] = useState(true)
  const [newPledge, setNewPledge] = useState({
    type: 'money' as 'money' | 'time' | 'materials',
    amount: '',
    hours: '',
    materials: '',
    description: ''
  })
  const [showPledgeForm, setShowPledgeForm] = useState(false)

  useEffect(() => {
    const fetchProject = async () => {
      try {
        setLoading(true)
        const response = await fetch(`/api/projects/${params.id}`)
        if (response.ok) {
          const data = await response.json()
          setProject(data)
          
          // Fetch pledges
          const pledgesResponse = await fetch(`/api/pledges?projectId=${params.id}`)
          if (pledgesResponse.ok) {
            const pledgesData = await pledgesResponse.json()
            setPledges(pledgesData)
          }
        }
      } catch (error) {
        console.error('Error fetching project:', error)
      } finally {
        setLoading(false)
      }
    }
    
    fetchProject()
  }, [params.id])

  const handlePledgeSubmit = async (e: React.FormEvent) => {
    e.preventDefault()
    try {
      const response = await fetch('/api/pledges', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          projectId: params.id,
          ...newPledge
        })
      })
      
      if (response.ok) {
        alert('Η συμβολή σας καταχωρήθηκε επιτυχώς!')
        setShowPledgeForm(false)
        setNewPledge({
          type: 'money',
          amount: '',
          hours: '',
          materials: '',
          description: ''
        })
        // Refresh pledges
        const pledgesResponse = await fetch(`/api/pledges?projectId=${params.id}`)
        if (pledgesResponse.ok) {
          const pledgesData = await pledgesResponse.json()
          setPledges(pledgesData)
        }
      }
    } catch (error) {
      console.error('Error creating pledge:', error)
      alert('Σφάλμα κατά την καταχώρηση της συμβολής')
    }
  }

  if (loading) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <div className="w-16 h-16 border-4 border-blue-900 border-t-transparent rounded-full animate-spin mx-auto mb-4"></div>
          <p className="text-gray-600">Φόρτωση έργου...</p>
        </div>
      </div>
    )
  }

  if (!project) {
    return (
      <div className="min-h-screen bg-gray-50 flex items-center justify-center">
        <div className="text-center">
          <h1 className="text-2xl font-bold text-gray-900">Έργο δεν βρέθηκε</h1>
          <button
            onClick={() => router.push('/projects')}
            className="mt-4 bg-blue-900 text-white px-6 py-2 rounded-lg hover:bg-blue-800"
          >
            Επιστροφή στα Έργα
          </button>
        </div>
      </div>
    )
  }

  const progressPercentage = (project.budgetPledged / project.budgetNeeded) * 100

  const getStatusIcon = (status: string) => {
    switch (status) {
      case 'completed':
        return <CheckCircleIcon className="h-5 w-5 text-green-500" />
      case 'in_progress':
        return <ClockIcon className="h-5 w-5 text-blue-500" />
      case 'pending_approval':
      case 'approved':
      case 'draft':
        return <ExclamationCircleIcon className="h-5 w-5 text-yellow-500" />
      default:
        return <ExclamationCircleIcon className="h-5 w-5 text-gray-500" />
    }
  }

  const getStatusText = (status: string) => {
    switch (status) {
      case 'completed':
        return 'Ολοκληρώθηκε'
      case 'in_progress':
        return 'Σε εξέλιξη'
      case 'pending_approval':
        return 'Αναμονή έγκρισης'
      case 'approved':
        return 'Εγκρίθηκε'
      case 'draft':
        return 'Προσχέδιο'
      case 'rejected':
        return 'Απορρίφθηκε'
      default:
        return status
    }
  }

  const getCategoryText = (category: string) => {
    switch (category) {
      case 'infrastructure':
        return 'Υποδομές'
      case 'environment':
        return 'Περιβάλλον'
      case 'community':
        return 'Κοινότητα'
      case 'parks':
        return 'Πάρκα'
      case 'culture':
        return 'Πολιτισμός'
      case 'safety':
        return 'Ασφάλεια'
      default:
        return category
    }
  }

  return (
    <div className="min-h-screen bg-neutral-50">
      {/* Header */}
      <div className="bg-white border-b border-neutral-200">
        <div className="max-w-6xl mx-auto px-4 py-6">
          <div className="flex items-center gap-4">
            <button
              onClick={() => router.push('/projects')}
              className="flex items-center text-primary-600 hover:text-primary-900 transition-colors font-medium"
            >
              <ChevronLeftIcon className="h-5 w-5 mr-2" />
              Επιστροφή στα Έργα
            </button>
            <span className="text-neutral-300">|</span>
            <button
              onClick={() => router.push('/')}
              className="flex items-center text-primary-600 hover:text-primary-900 transition-colors font-medium"
            >
              <ChevronLeftIcon className="h-5 w-5 mr-2" />
              Αρχική Σελίδα
            </button>
          </div>
        </div>
      </div>

      <div className="max-w-6xl mx-auto px-4 py-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Main Content */}
          <div className="lg:col-span-2">
            {/* Project Header */}
            <div className="bg-white rounded-2xl shadow-card p-10 mb-8 border border-neutral-200">
              <div className="flex items-start justify-between mb-8">
                <div>
                  <h1 className="text-4xl font-bold text-primary-900 mb-4">{project.title}</h1>
                  <div className="flex items-center space-x-6 text-sm text-primary-600">
                    <div className="flex items-center">
                      {getStatusIcon(project.status)}
                      <span className="ml-2 font-medium">{getStatusText(project.status)}</span>
                    </div>
                    <span className="bg-accent-50 text-accent-700 px-3 py-2 rounded-full border border-accent-200 font-medium">
                      {getCategoryText(project.category)}
                    </span>
                    {project.municipalityApproved && (
                      <span className="bg-success-50 text-success-700 px-3 py-2 rounded-full text-sm border border-success-200 font-medium">
                        Εγκρίθηκε από Δήμο
                      </span>
                    )}
                  </div>
                </div>
              </div>

              <div className="flex items-center text-primary-600 mb-6">
                <MapPinIcon className="h-5 w-5 mr-3" />
                <span className="font-medium">{project.location.address}, {project.location.district}</span>
              </div>

              <div className="flex items-center text-primary-600 mb-8">
                <CalendarIcon className="h-5 w-5 mr-3" />
                <span className="font-medium">Δημιουργήθηκε: {new Date(project.createdAt).toLocaleDateString('el-GR')}</span>
              </div>

              <p className="text-primary-700 text-lg leading-relaxed">{project.description}</p>
            </div>

            {/* Funding Progress */}
            <div className="bg-white rounded-2xl shadow-card p-8 mb-8 border border-neutral-100">
              <h2 className="text-2xl font-bold text-primary-900 mb-6">Πρόοδος Χρηματοδότησης</h2>
              <div className="mb-4">
                <div className="flex justify-between items-center mb-2">
                  <span className="text-primary-700 font-medium">Συγκεντρώθηκαν</span>
                  <span className="font-semibold text-primary-900">{project.budgetPledged}€ / {project.budgetNeeded}€</span>
                </div>
                <div className="w-full bg-neutral-200 rounded-full h-3">
                  <div
                    className="bg-blue-900 h-3 rounded-full transition-all duration-300"
                    style={{ width: `${Math.min(progressPercentage, 100)}%` }}
                  />
                </div>
                <div className="text-right text-sm text-primary-600 mt-2 font-medium">
                  {progressPercentage.toFixed(1)}% ολοκληρώθηκε
                </div>
              </div>
            </div>

            {/* Pledges List */}
            <div className="bg-white rounded-2xl shadow-lg p-8">
              <h2 className="text-2xl font-bold text-gray-900 mb-6">Συμβολές ({pledges.length})</h2>
              {pledges.length === 0 ? (
                <p className="text-gray-500 text-center py-8">Δεν υπάρχουν συμβολές ακόμα</p>
              ) : (
                <div className="space-y-4">
                  {pledges.map((pledge) => (
                    <div key={pledge.id} className="border rounded-lg p-4 hover:bg-gray-50 transition-colors">
                      <div className="flex items-start justify-between">
                        <div className="flex-1">
                          <div className="flex items-center space-x-2 mb-2">
                            <UserIcon className="h-4 w-4 text-gray-500" />
                            <span className="text-sm text-gray-600">Χρήστης {pledge.userId}</span>
                            <span className={`px-2 py-1 rounded-full text-xs ${
                              pledge.status === 'confirmed' ? 'bg-green-100 text-green-800' : 'bg-yellow-100 text-yellow-800'
                            }`}>
                              {pledge.status === 'confirmed' ? 'Επιβεβαιώθηκε' : 'Αναμονή'}
                            </span>
                          </div>
                          <p className="text-gray-700 mb-2">{pledge.description}</p>
                          <div className="flex items-center space-x-4 text-sm">
                            {pledge.type === 'money' && pledge.amount && (
                              <span className="flex items-center text-green-600">
                                <CurrencyEuroIcon className="h-4 w-4 mr-1" />
                                {pledge.amount}€
                              </span>
                            )}
                            {pledge.type === 'time' && pledge.hours && (
                              <span className="text-blue-600">{pledge.hours} ώρες</span>
                            )}
                            {pledge.type === 'materials' && pledge.materials && (
                              <span className="text-purple-600">{pledge.materials}</span>
                            )}
                          </div>
                        </div>
                        <div className="text-xs text-gray-500">
                          {new Date(pledge.createdAt).toLocaleDateString('el-GR')}
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>

          {/* Sidebar */}
          <div className="lg:col-span-1">
            {/* Pledge Form */}
            <div className="bg-white rounded-2xl shadow-card p-6 sticky top-8 border border-neutral-100">
              <h3 className="text-xl font-bold text-primary-900 mb-6">Κάντε τη Συμβολή σας</h3>
              
              {!showPledgeForm ? (
                <button
                  onClick={() => setShowPledgeForm(true)}
                  className="w-full bg-primary-900 text-white py-4 px-6 rounded-xl font-semibold hover:bg-primary-800 transition-all duration-200 transform hover:scale-105 shadow-soft"
                >
                  Συμβάλλω στο Έργο
                </button>
              ) : (
                <form onSubmit={handlePledgeSubmit} className="space-y-4">
                  <div>
                    <label className="block text-sm font-medium text-gray-700 mb-2">Τύπος Συμβολής</label>
                    <select
                      value={newPledge.type}
                      onChange={(e) => setNewPledge({ ...newPledge, type: e.target.value as any })}
                      className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-900 focus:border-blue-900 text-gray-900 bg-white"
                    >
                      <option value="money">Χρήματα</option>
                      <option value="time">Χρόνος</option>
                      <option value="materials">Υλικά</option>
                    </select>
                  </div>

                  {newPledge.type === 'money' && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Ποσό (€)</label>
                      <input
                        type="number"
                        min="1"
                        value={newPledge.amount}
                        onChange={(e) => setNewPledge({ ...newPledge, amount: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-900 focus:border-blue-900 text-gray-900 bg-white placeholder:text-gray-500"
                        placeholder="Εισάγετε ποσό"
                        required
                      />
                    </div>
                  )}

                  {newPledge.type === 'time' && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Ώρες</label>
                      <input
                        type="number"
                        min="1"
                        value={newPledge.hours}
                        onChange={(e) => setNewPledge({ ...newPledge, hours: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-900 focus:border-blue-900 text-gray-900 bg-white placeholder:text-gray-500"
                        placeholder="Εισάγετε ώρες"
                        required
                      />
                    </div>
                  )}

                  {newPledge.type === 'materials' && (
                    <div>
                      <label className="block text-sm font-medium text-gray-700 mb-2">Υλικά</label>
                      <input
                        type="text"
                        value={newPledge.materials}
                        onChange={(e) => setNewPledge({ ...newPledge, materials: e.target.value })}
                        className="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-900 focus:border-blue-900 text-gray-900 bg-white placeholder:text-gray-500"
                        placeholder="Περιγράψτε τα υλικά"
                        required
                      />
                    </div>
                  )}

                  <div>
                    <label className="block text-sm font-medium text-primary-700 mb-2">Περιγραφή</label>
                    <textarea
                      value={newPledge.description}
                      onChange={(e) => setNewPledge({ ...newPledge, description: e.target.value })}
                      rows={3}
                      className="w-full px-3 py-2 border border-neutral-300 rounded-lg focus:ring-2 focus:ring-accent-500 focus:border-accent-500 text-primary-900 bg-white placeholder:text-primary-500"
                      placeholder="Περιγράψτε τη συμβολή σας"
                      required
                    />
                  </div>

                  <div className="flex space-x-3">
                    <button
                      type="submit"
                      className="flex-1 bg-primary-900 text-white py-3 px-4 rounded-xl hover:bg-primary-800 transition-colors font-medium"
                    >
                      Υποβολή
                    </button>
                    <button
                      type="button"
                      onClick={() => setShowPledgeForm(false)}
                      className="flex-1 bg-neutral-200 text-primary-700 py-3 px-4 rounded-xl hover:bg-neutral-300 transition-colors font-medium"
                    >
                      Άκυρο
                    </button>
                  </div>
                </form>
              )}
            </div>
          </div>
        </div>
      </div>
    </div>
  )
}
