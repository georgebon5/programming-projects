// Hook για διαχείριση Projects (Δημόσια Έργα)
'use client'

import { useState, useEffect } from 'react'

export interface Project {
  id: string
  title: string
  description: string
  category: string
  status: string
  location?: {
    lat: number
    lng: number
    address: string
    district: string
  }
  creatorId: string
  budgetNeeded?: number
  budgetPledged?: number
  municipalityApproved: boolean
  createdAt: string | Date
  updatedAt: string | Date
}

// Hook for fetching projects
export function useProjects(filters?: any) {
  const [projects, setProjects] = useState<Project[]>([])
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchProjects = async (customFilters?: any) => {
    try {
      setLoading(true)
      setError(null)

      // Build query string
      const params = new URLSearchParams()
      const activeFilters = customFilters || filters
      
      if (activeFilters?.category) params.append('category', activeFilters.category)
      if (activeFilters?.status) params.append('status', activeFilters.status)
      if (activeFilters?.district) params.append('district', activeFilters.district)

      const url = `/api/projects${params.toString() ? `?${params.toString()}` : ''}`
      const response = await fetch(url)

      if (!response.ok) {
        throw new Error('Failed to fetch projects')
      }

      const data = await response.json()
      // API returns array directly, not wrapped in { projects: [...] }
      const projectsData = Array.isArray(data) ? data : (data.projects || [])
      setProjects(projectsData)
      console.log('✅ Fetched projects:', projectsData.length)
      return projectsData
    } catch (err: any) {
      setError(err.message)
      console.error('Error fetching projects:', err)
      throw err
    } finally {
      setLoading(false)
    }
  }

  const createProject = async (projectData: {
    title: string
    description: string
    category: string
    location?: string
    budgetNeeded?: number
  }) => {
    try {
      setError(null)

      const response = await fetch('/api/projects', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(projectData),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to create project')
      }

      const data = await response.json()
      
      // Refresh projects list
      await fetchProjects()
      
      return data
    } catch (err: any) {
      setError(err.message)
      throw err
    }
  }

  useEffect(() => {
    fetchProjects()
  }, [])

  return { 
    projects, 
    loading, 
    error,
    fetchProjects,
    createProject,
    setProjects
  }
}

// Hook for fetching single project
export function useProject(id: string) {
  const [project, setProject] = useState<Project | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)

  const fetchProject = async () => {
    try {
      setLoading(true)
      setError(null)

      const response = await fetch(`/api/projects/${id}`)

      if (!response.ok) {
        throw new Error('Failed to fetch project')
      }

      const data = await response.json()
      setProject(data.project)
      return data
    } catch (err: any) {
      setError(err.message)
      console.error('Error fetching project:', err)
      throw err
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => {
    if (id) {
      fetchProject()
    }
  }, [id])

  return { 
    project, 
    loading, 
    error,
    fetchProject,
    setProject
  }
}
