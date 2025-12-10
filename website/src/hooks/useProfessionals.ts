// Hook για διαχείριση Professionals (Ειδικών)
'use client'

import { useState, useEffect } from 'react'

export interface Professional {
  id: string
  userId: string
  profession: string
  name: string
  email: string
  phone: string
  licenseNumber?: string
  yearsExperience: number
  hourlyRate: number
  municipalitySubsidized: boolean
  subsidizedRate: number
  rating: number
  totalReviews: number
  availability: Record<string, string[]>
  serviceAreas: string[]
  specializations: string[]
  approvedByMunicipality: boolean
  bio?: string
  avatar?: string | null
}

export function useProfessionals() {
  const [professionals, setProfessionals] = useState<Professional[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Fetch all professionals
  const fetchProfessionals = async (filters?: {
    profession?: string
    serviceArea?: string
    approved?: boolean
  }) => {
    try {
      setLoading(true)
      setError(null)

      // Build query string
      const params = new URLSearchParams()
      if (filters?.profession) params.append('profession', filters.profession)
      if (filters?.serviceArea) params.append('serviceArea', filters.serviceArea)
      if (filters?.approved !== undefined) params.append('approved', String(filters.approved))

      const url = `/api/professionals${params.toString() ? `?${params.toString()}` : ''}`
      const response = await fetch(url)

      if (!response.ok) {
        throw new Error('Failed to fetch professionals')
      }

      const data = await response.json()
      setProfessionals(data.professionals || [])
      return data
    } catch (err: any) {
      setError(err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }

  // Register new professional
  const registerProfessional = async (professionalData: Partial<Professional>) => {
    try {
      setLoading(true)
      setError(null)

      const response = await fetch('/api/professionals', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(professionalData),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to register professional')
      }

      const data = await response.json()
      return data
    } catch (err: any) {
      setError(err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }

  // Get professional by profession type
  const getProfessionalsByType = async (profession: string) => {
    return fetchProfessionals({ profession, approved: true })
  }

  return {
    professionals,
    loading,
    error,
    fetchProfessionals,
    registerProfessional,
    getProfessionalsByType,
  }
}
