// Final Availability Check API - Τελικός έλεγχος πριν την κράτηση
import { NextRequest, NextResponse } from 'next/server'

// POST /api/availability/check - Final check before booking confirmation
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    const { professionalId, date, time } = body

    if (!professionalId || !date || !time) {
      return NextResponse.json(
        { error: 'Missing required fields', success: false },
        { status: 400 }
      )
    }

    console.log(`🔍 Final availability check: Professional ${professionalId}, Date ${date}, Time ${time}`)

    // Fetch bookings for this professional on this date
    const bookingsResponse = await fetch(
      `${request.nextUrl.origin}/api/bookings?professionalId=${professionalId}`,
      { cache: 'no-store' }
    )

    if (!bookingsResponse.ok) {
      throw new Error('Failed to fetch bookings')
    }

    const bookingsData = await bookingsResponse.json()
    const bookings = bookingsData.bookings || []

    // Check if the time slot is already booked
    const isBooked = bookings.some((booking: any) => 
      booking.scheduledDate === date && booking.scheduledTime === time
    )

    const isAvailable = !isBooked

    console.log(isAvailable ? `✅ Time slot ${time} is available` : `❌ Time slot ${time} is already booked`)

    return NextResponse.json({
      success: true,
      isAvailable,
      professionalId,
      date,
      time,
      message: isAvailable 
        ? 'Time slot is available' 
        : 'Time slot is already booked',
    })
  } catch (error) {
    console.error('❌ Error checking final availability:', error)
    return NextResponse.json(
      { error: 'Failed to check availability', success: false },
      { status: 500 }
    )
  }
}
