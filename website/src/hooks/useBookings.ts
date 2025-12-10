// Hook για διαχείριση Bookings (Ραντεβού)
'use client'

import { useState } from 'react'
import { useAuth } from './useAuth'

export interface Booking {
  id: string
  citizenId: string
  professionalId: string
  professionalName?: string
  profession?: string
  serviceType: string
  appointmentDate: string // Combined date+time
  scheduledDate: string
  scheduledTime: string
  estimatedHours: number // Alias for durationHours
  durationHours: number
  serviceAddress: string // Alias for address
  address: string
  description: string
  status: 'pending' | 'approved' | 'confirmed' | 'in_progress' | 'completed' | 'cancelled'
  basePrice: number
  municipalitySubsidy: number
  citizenPays: number
  citizenRating?: number
  citizenReview?: string
  createdAt: string
  updatedAt: string
  completedAt?: string
}

export function useBookings() {
  const { user } = useAuth() // Get current user
  const [bookings, setBookings] = useState<Booking[]>([])
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)

  // Fetch bookings
  const fetchBookings = async (filters?: {
    citizenId?: string
    professionalId?: string
    status?: string
  }) => {
    try {
      setLoading(true)
      setError(null)

      // Build query string
      const params = new URLSearchParams()
      if (filters?.citizenId) params.append('citizenId', filters.citizenId)
      if (filters?.professionalId) params.append('professionalId', filters.professionalId)
      if (filters?.status) params.append('status', filters.status)

      const url = `/api/bookings${params.toString() ? `?${params.toString()}` : ''}`
      const response = await fetch(url)

      if (!response.ok) {
        throw new Error('Failed to fetch bookings')
      }

      const data = await response.json()
      setBookings(data.bookings || [])
      return data
    } catch (err: any) {
      setError(err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }

  // Create new booking (flexible input)
  const createBooking = async (bookingData: {
    professionalId: string
    appointmentDate?: string // ISO date string with time
    estimatedHours?: number
    serviceAddress?: string
    phoneNumber?: string
    description?: string
    // OR old format:
    citizenId?: string
    serviceType?: string
    scheduledDate?: string
    scheduledTime?: string
    durationHours?: number
    address?: string
  }) => {
    try {
      setLoading(true)
      setError(null)

      // Transform to API format
      const apiData = {
        citizenId: bookingData.citizenId || user?.email || 'user-citizen-1', // Use current user email
        professionalId: bookingData.professionalId,
        serviceType: bookingData.serviceType || 'general',
        scheduledDate: bookingData.scheduledDate || bookingData.appointmentDate?.split('T')[0] || '',
        scheduledTime: bookingData.scheduledTime || bookingData.appointmentDate?.split('T')[1] || '',
        durationHours: bookingData.durationHours || bookingData.estimatedHours || 2,
        address: bookingData.address || bookingData.serviceAddress || '',
        description: bookingData.description || '',
      }

      console.log('Creating booking with data:', apiData)

      const response = await fetch('/api/bookings', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(apiData),
      })

      if (!response.ok) {
        const errorData = await response.json()
        throw new Error(errorData.error || 'Failed to create booking')
      }

      const data = await response.json()
      console.log('Booking created successfully:', data)
      
      // Refresh bookings list to show new booking
      if (apiData.citizenId) {
        console.log('Refreshing bookings for user:', apiData.citizenId)
        await fetchBookings({ citizenId: apiData.citizenId })
      }

      return data
    } catch (err: any) {
      setError(err.message)
      throw err
    } finally {
      setLoading(false)
    }
  }

  // Get my bookings (as citizen)
  const getMyBookings = async (citizenId: string) => {
    return fetchBookings({ citizenId })
  }

  // Fetch my bookings (alias)
  const fetchMyBookings = async () => {
    const citizenId = user?.email === 'citizen@helpmeanytime.gr' ? 'user-citizen-1' : user?.email || 'user-citizen-1'
    console.log('Fetching bookings for citizen:', citizenId)
    return fetchBookings({ citizenId })
  }

  // Get bookings by status
  const getBookingsByStatus = async (status: string, userId?: string) => {
    return fetchBookings({ status, citizenId: userId })
  }

  return {
    bookings,
    loading,
    error,
    fetchBookings,
    createBooking,
    getMyBookings,
    fetchMyBookings,
    getBookingsByStatus,
  }
}
