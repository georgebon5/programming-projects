// ============================================
// 👨‍💻 DEVELOPER 2 - TASK 4 (Hour 6-8)
// ============================================
// 
// Custom hook για Pledges - THE WOW FACTOR HOOK!
//
// ΤΙ ΠΡΕΠΕΙ ΝΑ ΚΑΝΕΙΣ:
// 1. Φτιάξε functions:
//    - fetchPledges(projectId) -> GET /api/pledges?projectId=xxx
//    - createPledge(data) -> POST /api/pledges
//    - fetchStats(projectId) -> GET /api/pledges/stats?projectId=xxx
//
// 2. State management:
//    - pledges: Pledge[]
//    - stats: { total_money, total_hours, total_materials, progress }
//    - loading: boolean
//
// 3. (BONUS) Real-time subscriptions:
//    - Χρησιμοποίησε Supabase real-time
//    - Όταν κάποιος κάνει pledge, ανανέωσε αυτόματα τα stats!
//
// ΠΑΡΑΔΕΙΓΜΑ ΧΡΗΣΗΣ:
// const { pledges, stats, createPledge } = usePledges(projectId)
// 
// <div>Progress: {stats.progress_percentage}%</div>
// <button onClick={() => createPledge({ type: 'money', amount: 50 })}>
//   Pledge €50
// </button>
//
// Αυτό θα το χρησιμοποιείς στο PledgeCounter component!
//
// ΧΡΟΝΟΣ: 2 ώρες
// ============================================

'use client'
import { useState, useEffect } from 'react'
import { Pledge } from '@/types'
// import { supabase } from '@/lib/supabase' // για real-time

interface PledgeStats {
  total_money: number
  total_hours: number
  total_materials: number
  pledge_count: number
  progress_percentage: number
  breakdown: {
    money_pledges: number
    time_pledges: number
    materials_pledges: number
  }
}

export function usePledges(projectId?: string) {
  const [pledges, setPledges] = useState<Pledge[]>([])
  const [stats, setStats] = useState<PledgeStats | null>(null)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  
  // Fetch all pledges for a project
  const fetchPledges = async (projectId: string) => {
    setLoading(true)
    setError(null)
    try {
      const response = await fetch(`/api/pledges?projectId=${projectId}`)
      
      if (!response.ok) {
        throw new Error('Failed to fetch pledges')
      }
      
      const data = await response.json()
      setPledges(data.pledges || [])
    } catch (err) {
      console.error('❌ Error fetching pledges:', err)
      setError('Failed to fetch pledges')
    } finally {
      setLoading(false)
    }
  }
  
  // Fetch stats for a project - ΤΟ ΠΙΟ ΣΗΜΑΝΤΙΚΟ!
  const fetchStats = async (projectId: string) => {
    setError(null)
    try {
      const response = await fetch(`/api/pledges/stats?projectId=${projectId}`)
      
      if (!response.ok) {
        throw new Error('Failed to fetch stats')
      }
      
      const data = await response.json()
      console.log('📊 Stats fetched:', data.stats)
      setStats(data.stats || null)
    } catch (err) {
      console.error('❌ Error fetching stats:', err)
      setError('Failed to fetch stats')
    }
  }
  
  // Create new pledge - THE WOW MOMENT!
  const createPledge = async (pledgeData: {
    project_id: string
    type: 'money' | 'time' | 'materials'
    amount?: number
    hours?: number
    materials?: string
    description?: string
  }) => {
    setLoading(true)
    setError(null)
    try {
      console.log('📥 Creating pledge:', pledgeData)
      
      const response = await fetch('/api/pledges', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify(pledgeData)
      })
      
      if (!response.ok) {
        const error = await response.json()
        throw new Error(error.error || 'Failed to create pledge')
      }
      
      const result = await response.json()
      console.log('✅ Pledge created:', result)
      
      // Refresh pledges and stats immediately
      await fetchPledges(pledgeData.project_id)
      await fetchStats(pledgeData.project_id)
      
      return result
    } catch (err) {
      console.error('❌ Error creating pledge:', err)
      setError(err instanceof Error ? err.message : 'Failed to create pledge')
      throw err
    } finally {
      setLoading(false)
    }
  }
  
  // TODO: BONUS - Real-time subscriptions
  // useEffect(() => {
  //   if (!projectId) return
  //   
  //   const subscription = supabase
  //     .channel('pledges')
  //     .on('postgres_changes', 
  //       { event: '*', schema: 'public', table: 'pledges' },
  //       (payload) => {
  //         console.log('New pledge!', payload)
  //         fetchStats(projectId) // Ανανέωσε τα stats!
  //       }
  //     )
  //     .subscribe()
  //   
  //   return () => {
  //     subscription.unsubscribe()
  //   }
  // }, [projectId])
  
  // Auto-fetch όταν έχουμε projectId
  useEffect(() => {
    if (projectId) {
      fetchPledges(projectId)
      fetchStats(projectId)
    }
  }, [projectId])
  
  return {
    pledges,
    stats,
    loading,
    error,
    fetchPledges,
    fetchStats,
    createPledge,
  }
}
