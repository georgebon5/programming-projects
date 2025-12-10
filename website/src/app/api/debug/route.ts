// Debug endpoint - Δες τι έχει το in-memory store
import { NextRequest, NextResponse } from 'next/server'

export async function GET(request: NextRequest) {
  try {
    const projects = globalThis.projectsStore || []
    const bookings = globalThis.newBookings || []
    
    return NextResponse.json({
      message: 'In-Memory Store Debug Info',
      timestamp: new Date().toISOString(),
      stores: {
        projects: {
          count: projects.length,
          data: projects
        },
        bookings: {
          count: bookings.length,
          data: bookings
        }
      },
      warning: '⚠️ Αυτά τα δεδομένα χάνονται όταν κάνεις refresh ή restart τον server!'
    })
  } catch (error) {
    return NextResponse.json({
      error: 'Failed to get debug info',
      message: error instanceof Error ? error.message : 'Unknown error'
    }, { status: 500 })
  }
}
