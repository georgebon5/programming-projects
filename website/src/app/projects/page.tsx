// Projects Page - Δημόσια Έργα & Κοινοτικές Πρωτοβουλίες
'use client'

import { useEffect, useState } from 'react'
import { useRouter } from 'next/navigation'
import { useAuth } from '@/hooks/useAuth'
import { useProjects } from '@/hooks/useProjects'
import ProjectCard from '@/components/ProjectCard'
import { Project } from '@/types'
import { 
  MapPin, 
  Calendar, 
  Euro, 
  Target, 
  Users, 
  Filter,
  Plus,
  ArrowRight,
  Clock,
  CheckCircle,
  AlertCircle,
  Heart
} from 'lucide-react'

const categoryLabels: Record<string, string> = {
  infrastructure: 'Υποδομή',
  parks: 'Πάρκα',
  community: 'Κοινότητα',
  environment: 'Περιβάλλον',
  culture: 'Πολιτισμός',
  sports: 'Αθλητισμός',
}

const categoryColors: Record<string, string> = {
  infrastructure: 'bg-neutral-100 text-neutral-700 border-neutral-200',
  parks: 'bg-success-50 text-success-700 border-success-200',
  community: 'bg-accent-50 text-accent-700 border-accent-200',
  environment: 'bg-success-50 text-success-600 border-success-200',
  culture: 'bg-primary-50 text-primary-700 border-primary-200',
  sports: 'bg-warning-50 text-warning-700 border-warning-200',
}

const statusLabels: Record<string, string> = {
  pending: 'Αναμένει Έγκριση',
  pending_approval: 'Εκκρεμεί έγκριση',
  approved: 'Εγκρίθηκε',
  active: 'Ενεργό',
  in_progress: 'Σε εξέλιξη',
  completed: 'Ολοκληρώθηκε',
  cancelled: 'Ακυρώθηκε',
}

const statusColors: Record<string, string> = {
  pending: 'bg-yellow-50 text-yellow-700 border-yellow-200',
  pending_approval: 'bg-warning-50 text-warning-700 border-warning-200',
  approved: 'bg-success-50 text-success-700 border-success-200',
  active: 'bg-green-50 text-green-700 border-green-200',
  in_progress: 'bg-accent-50 text-accent-700 border-accent-200',
  completed: 'bg-success-50 text-success-600 border-success-200',
  cancelled: 'bg-danger-50 text-danger-700 border-danger-200',
}

const statusIcons: Record<string, React.ReactNode> = {
  pending: <Clock className="w-4 h-4" />,
  pending_approval: <Clock className="w-4 h-4" />,
  approved: <CheckCircle className="w-4 h-4" />,
  active: <CheckCircle className="w-4 h-4" />,
  in_progress: <AlertCircle className="w-4 h-4" />,
  completed: <CheckCircle className="w-4 h-4" />,
  cancelled: <AlertCircle className="w-4 h-4" />,
}

export default function ProjectsPage() {
  const router = useRouter()
  const { user, isAuthenticated } = useAuth()
  const { projects, loading: projectsLoading, fetchProjects, setProjects } = useProjects()

  const [filter, setFilter] = useState<'all' | string>('all')
  const [statusFilter, setStatusFilter] = useState<'all' | string>('all')
  const [sortBy, setSortBy] = useState<'recent' | 'popular' | 'budget'>('recent')
  const [showFilters, setShowFilters] = useState(false)

  useEffect(() => {
    fetchProjects()
  }, [])

  // Refresh projects when page becomes visible (e.g., when returning from create page)
  useEffect(() => {
    const handleFocus = () => {
      fetchProjects()
    }
    window.addEventListener('focus', handleFocus)
    return () => window.removeEventListener('focus', handleFocus)
  }, [])

  const handleDeleteProject = async (projectId: string) => {
    try {
      const response = await fetch(`/api/projects/${projectId}`, {
        method: 'DELETE',
      });

      if (!response.ok) {
        throw new Error('Failed to delete project');
      }

      // Update the state to remove the deleted project
      setProjects(prevProjects => prevProjects.filter(p => p.id !== projectId));
      console.log(`Project ${projectId} deleted successfully from UI.`);
    } catch (err) {
      console.error("Error deleting project:", err);
      // Optionally, show an error message to the user
    }
  };

  // Filter projects
  const filteredProjects = projects.filter(project => {
    if (filter !== 'all' && project.category !== filter) return false
    if (statusFilter !== 'all' && project.status !== statusFilter) return false
    return true
  })

  // Sort projects
  const sortedProjects = [...filteredProjects].sort((a, b) => {
    switch (sortBy) {
      case 'recent':
        return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
      case 'popular':
        return (b.budgetPledged || 0) - (a.budgetPledged || 0)
      case 'budget':
        return (b.budgetNeeded || 0) - (a.budgetNeeded || 0)
      default:
        return 0
    }
  })

  const calculateProgress = (project: any) => {
    if (!project.budgetNeeded || project.budgetNeeded === 0) return 0
    return Math.min((project.budgetPledged || 0) / project.budgetNeeded * 100, 100)
  }

  if (projectsLoading) {
    return (
      <div className="min-h-screen bg-neutral-50 flex items-center justify-center">
        <div className="text-center">
          <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
          <p className="text-primary-600">Φόρτωση έργων...</p>
        </div>
      </div>
    )
  }

  return (
    <div className="min-h-screen bg-neutral-50">
      {/* Header */}
      <div className="bg-white border-b border-neutral-200">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-10">
          {/* Navigation Buttons */}
          <div className="mb-6">
            <button
              onClick={() => router.push('/')}
              className="flex items-center gap-2 text-primary-600 hover:text-primary-900 transition-colors font-medium"
            >
              <ArrowRight className="w-5 h-5 rotate-180" />
              <span>Αρχική Σελίδα</span>
            </button>
          </div>
          
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-6">
            <div>
              <h1 className="text-4xl font-bold text-gray-900 mb-3">
                Δημόσια Έργα
              </h1>
              <p className="text-gray-600 text-lg leading-relaxed">
                Πρωτοβουλίες πολιτών για βελτίωση της πόλης
              </p>
            </div>
            
            {isAuthenticated && (
              <button
                onClick={() => router.push('/projects/create')}
                className="flex items-center gap-2 bg-primary-900 text-white px-8 py-4 rounded-2xl font-semibold hover:bg-primary-800 transition shadow-soft hover:shadow-card"
              >
                <Plus className="w-5 h-5" />
                <span>Νέο Έργο</span>
              </button>
            )}
          </div>
        </div>
      </div>

      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Stats */}
        <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
          <div className="bg-white rounded-xl p-6 shadow-md">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                  <Target className="w-6 h-6 text-blue-900" />
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Ενεργά Έργα</p>
                <p className="text-2xl font-bold text-gray-900">{projects.filter(p => p.status === 'approved' || p.status === 'in_progress').length+2}</p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-md">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                  <Euro className="w-6 h-6 text-blue-900" />
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Συνολικά Χρήματα</p>
                <p className="text-2xl font-bold text-gray-900">
                  €{projects.reduce((sum, p) => sum + (p.budgetPledged || 0), 0).toLocaleString()}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-md">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                  <Users className="w-6 h-6 text-blue-900" />
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Συμμετέχοντες</p>
                <p className="text-2xl font-bold text-gray-900">
                  {projects.filter(p => (p.budgetPledged || 0) > 0).length * 3}
                </p>
              </div>
            </div>
          </div>

          <div className="bg-white rounded-xl p-6 shadow-md">
            <div className="flex items-center">
              <div className="flex-shrink-0">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center">
                  <CheckCircle className="w-6 h-6 text-blue-900" />
                </div>
              </div>
              <div className="ml-4">
                <p className="text-sm font-medium text-gray-500">Ολοκληρώθηκαν</p>
                <p className="text-2xl font-bold text-gray-900">{projects.filter(p => p.status === 'completed').length}</p>
              </div>
            </div>
          </div>
        </div>

        {/* Filters */}
        <div className="bg-white rounded-xl shadow-md p-6 mb-8">
          <div className="flex flex-col sm:flex-row sm:items-center sm:justify-between gap-4">
            <div className="flex items-center gap-2">
              <Filter className="w-5 h-5 text-gray-500" />
              <span className="font-semibold text-gray-900">Φίλτρα:</span>
            </div>
            
            <div className="flex flex-wrap gap-3">
              {/* Category Filter */}
              <select
                value={filter}
                onChange={(e) => setFilter(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-900 focus:border-transparent transition text-gray-900 bg-white"
              >
                <option value="all">Όλες οι Κατηγορίες</option>
                {Object.entries(categoryLabels).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>

              {/* Status Filter */}
              <select
                value={statusFilter}
                onChange={(e) => setStatusFilter(e.target.value)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-900 focus:border-transparent transition text-gray-900 bg-white"
              >
                <option value="all">Όλα τα Status</option>
                {Object.entries(statusLabels).map(([value, label]) => (
                  <option key={value} value={value}>{label}</option>
                ))}
              </select>

              {/* Sort */}
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value as any)}
                className="px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-900 focus:border-transparent transition text-gray-900 bg-white"
              >
                <option value="recent">Πρόσφατα</option>
                <option value="popular">Δημοφιλή</option>
                <option value="budget">Μεγαλύτερος Προϋπολογισμός</option>
              </select>
            </div>
          </div>
        </div>

        {/* Projects Grid */}
        <div className="grid grid-cols-1 lg:grid-cols-2 xl:grid-cols-3 gap-8">
          {sortedProjects.map((project) => (
            <ProjectCard key={project.id} project={project} onDelete={handleDeleteProject} />
          ))}
        </div>

        {/* Empty State */}
        {sortedProjects.length === 0 && (
          <div className="bg-white rounded-xl shadow-md p-12 text-center">
            <div className="w-16 h-16 bg-gray-100 rounded-full flex items-center justify-center mx-auto mb-4">
              <Target className="w-8 h-8 text-gray-400" />
            </div>
            <h3 className="text-xl font-semibold text-gray-900 mb-2">
              Δεν βρέθηκαν έργα
            </h3>
            <p className="text-gray-500 mb-6">
              Δοκιμάστε να αλλάξετε τα φίλτρα ή δημιουργήστε ένα νέο έργο.
            </p>
            {isAuthenticated && (
              <button
                onClick={() => router.push('/projects/create')}
                className="inline-flex items-center gap-2 bg-blue-900 text-white px-6 py-3 rounded-lg font-semibold hover:bg-blue-800 transition"
              >
                <Plus className="w-5 h-5" />
                <span>Δημιουργήστε ένα Έργο</span>
              </button>
            )}
          </div>
        )}

        {/* Call to Action */}
        {!isAuthenticated && sortedProjects.length > 0 && (
          <div className="bg-blue-900 rounded-xl p-8 text-center text-white mt-12">
            <Heart className="w-12 h-12 mx-auto mb-4 opacity-90" />
            <h3 className="text-2xl font-bold mb-2">
              Θέλετε να συμμετέχετε;
            </h3>
            <p className="text-white/90 mb-6 text-lg">
              Συνδεθείτε για να υποστηρίξετε έργα ή να προτείνετε τις δικές σας ιδέες!
            </p>
            <button
              onClick={() => router.push('/auth?mode=signin')}
              className="bg-white text-blue-900 px-8 py-3 rounded-lg font-semibold hover:bg-gray-100 transition shadow-lg"
            >
              Σύνδεση / Εγγραφή
            </button>
          </div>
        )}
      </div>
    </div>
  )
}
