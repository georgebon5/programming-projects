// Project card component for grid displays
import React from 'react'
import { Project } from '@/types'
import Link from 'next/link'
import ProgressBar from '@/components/ui/ProgressBar' // Corrected import
import Badge from '@/components/ui/Badge' // Corrected import
import { MapPinIcon, CalendarIcon, UsersIcon } from '@heroicons/react/24/outline'

interface ProjectCardProps {
  project: Project
  onDelete: (projectId: string) => void
}

export default function ProjectCard({ project, onDelete }: ProjectCardProps) {
  const fundingStatus = project.budgetNeeded > 0 ? (project.budgetPledged / project.budgetNeeded) * 100 : 100

  const handleDelete = async (e: React.MouseEvent) => {
    e.stopPropagation() // Prevent card click event
    e.preventDefault(); // Prevent navigation
    if (window.confirm(`Είστε σίγουροι ότι θέλετε να διαγράψετε το έργο "${project.title}";`)) {
      onDelete(project.id)
    }
  }

  return (
    <div className="bg-white rounded-lg shadow-md overflow-hidden transform hover:-translate-y-1 transition-transform duration-300 relative">
       <div className="absolute top-2 right-2 z-10">
        <button
          onClick={handleDelete}
          className="bg-red-500 text-white rounded-full p-2 hover:bg-red-700 transition-colors focus:outline-none focus:ring-2 focus:ring-red-500"
          aria-label="Διαγραφή έργου"
        >
          <svg xmlns="http://www.w3.org/2000/svg" className="h-5 w-5" viewBox="0 0 20 20" fill="currentColor">
            <path fillRule="evenodd" d="M9 2a1 1 0 00-.894.553L7.382 4H4a1 1 0 000 2v10a2 2 0 002 2h8a2 2 0 002-2V6a1 1 0 100-2h-3.382l-.724-1.447A1 1 0 0011 2H9zM7 8a1 1 0 012 0v6a1 1 0 11-2 0V8zm4 0a1 1 0 012 0v6a1 1 0 11-2 0V8z" clipRule="evenodd" />
          </svg>
        </button>
      </div>
      <Link href={`/projects/${project.id}`} passHref>
        <div className="block">
          <div className="p-6 bg-blue-900 text-white">
            <div className="flex justify-between items-start">
              <Badge variant={project.category}>{project.category}</Badge>
              <Badge variant={project.status}>{project.status}</Badge>
            </div>
            <h3 className="text-2xl font-bold mt-4 truncate">{project.title}</h3>
            <div className="flex items-center mt-2 text-blue-200">
              <MapPinIcon className="h-5 w-5 mr-2" />
              <span>{project.location.district}</span>
            </div>
          </div>
          <div className="p-6">
            <p className="text-gray-600 h-12 overflow-hidden text-ellipsis">{project.description}</p>
            
            <div className="mt-6">
              <div className="flex justify-between items-center mb-2">
                <span className="text-sm font-medium text-gray-700">Χρηματοδότηση</span>
                <span className="text-sm font-bold text-blue-900">{fundingStatus.toFixed(0)}%</span>
              </div>
              <ProgressBar current={project.budgetPledged} target={project.budgetNeeded} />
              <div className="flex justify-between items-center mt-2 text-sm">
                <span className="text-gray-600">€{project.budgetPledged.toLocaleString('el-GR')} συγκεντρώθηκαν</span>
                <span className="text-gray-800 font-medium">€{project.budgetNeeded.toLocaleString('el-GR')} στόχος</span>
              </div>
            </div>

            <div className="mt-6 border-t pt-4 flex justify-between items-center text-sm text-gray-600">
              <div className="flex items-center">
                <CalendarIcon className="h-5 w-5 mr-2" />
                <span>{new Date(project.createdAt).toLocaleDateString('el-GR')}</span>
              </div>
              <div className="flex items-center">
                <UsersIcon className="h-5 w-5 mr-2" />
                <span>{project.pledgeCount} Υποστηρικτές</span>
              </div>
            </div>
          </div>
        </div>
      </Link>
    </div>
  )
}
