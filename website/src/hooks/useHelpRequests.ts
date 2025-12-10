// Hook για διαχείριση Help Requests (Αιτήματα Βοήθειας)
'use client'

import { useState } from 'react'

export interface HelpRequest {
  id: string
  requesterId: string
  requesterName?: string
  title: string
  description: string
  category: string
  urgency: 'low' | 'medium' | 'high'
  location: string
  preferredDate?: string
  phoneNumber?: string
  status: 'open' | 'assigned' | 'in_progress' | 'completed' | 'cancelled'
  volunteerId?: string | null
  volunteerName?: string | null
  assignedAt?: string
  completedAt?: string
  rating?: number
  feedback?: string
  images?: string[]
  createdAt: string
  updatedAt: string
}

export function useHelpRequests() {
  const [requests, setRequests] = useState<HelpRequest[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Fetch help requests
  const fetchRequests = async (filters?: {
    status?: string
    category?: string
    urgency?: string
    requesterId?: string
    volunteerId?: string
  }) => {
    try {
      setLoading(true)
      setError(null)

      // Build query string
      const params = new URLSearchParams()
      if (filters?.status) params.append('status', filters.status)
      if (filters?.category) params.append('category', filters.category)
      if (filters?.urgency) params.append('urgency', filters.urgency)
      if (filters?.requesterId) params.append('requesterId', filters.requesterId)
      if (filters?.volunteerId) params.append('volunteerId', filters.volunteerId)

      const url = `/api/help-requests${params.toString() ? `?${params.toString()}` : ''}`
      const response = await fetch(url)

      if (!response.ok) {
        throw new Error('Failed to fetch help requests')
      }

      const data = await response.json()
      setRequests(data.requests || [])
      return data
    } catch (err: any) {
      setError(err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }

  // Create new help request (flexible input)
  const createRequest = async (requestData: {
    category: string
    description: string
    location?: string
    preferredDate?: string
    phoneNumber?: string
    urgency?: 'low' | 'medium' | 'high'
    // OR old format:
    requesterId?: string
    title?: string
    images?: string[]
  }) => {
    try {
      setLoading(true)
      setError(null)

      // Transform to API format
      const apiData = {
        requesterId: requestData.requesterId || 'current-user-id', // TODO: Get from auth
        title: requestData.title || `${requestData.category} - Αίτημα Βοήθειας`,
        description: requestData.description,
        category: requestData.category,
        urgency: requestData.urgency || 'medium',
        location: requestData.location || '',
        images: requestData.images || [],
      }

      const response = await fetch('/api/help-requests', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(apiData),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to create help request')
      }

      const data = await response.json()
      
      // Refresh requests list
      await fetchRequests()

      return data
    } catch (err: any) {
      setError(err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }

  // Assign volunteer to request
  const assignVolunteer = async (requestId: string, volunteerId: string, volunteerName?: string) => {
    try {
      setLoading(true)
      setError(null)

      const response = await fetch(`/api/help-requests/${requestId}/assign`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ volunteerId, volunteerName }),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to assign volunteer')
      }

      const data = await response.json()
      
      // Refresh requests list
      await fetchRequests()

      return data
    } catch (err: any) {
      setError(err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }

  // Get open requests (available for volunteers)
  const getOpenRequests = async () => {
    return fetchRequests({ status: 'open' })
  }

  // Get my requests (as requester)
  const getMyRequests = async (requesterId: string) => {
    return fetchRequests({ requesterId })
  }

  // Get my volunteer assignments
  const getMyAssignments = async (volunteerId: string) => {
    return fetchRequests({ volunteerId })
  }

  return {
    requests,
    loading,
    error,
    fetchRequests,
    createRequest,
    assignVolunteer,
    getOpenRequests,
    getMyRequests,
    getMyAssignments,
  }
}
