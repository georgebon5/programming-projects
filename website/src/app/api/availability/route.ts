// Availability Check API - Έλεγχος Διαθεσιμότητας Επαγγελματιών
import { NextRequest, NextResponse } from 'next/server'

// All possible time slots (9:00 - 18:00, every hour)
const ALL_TIME_SLOTS = [
  '09:00', '10:00', '11:00', '12:00', '13:00', 
  '14:00', '15:00', '16:00', '17:00', '18:00'
]

// GET /api/availability - Check availability for a professional on a specific date
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const professionalId = searchParams.get('professionalId')
    const date = searchParams.get('date')

    if (!professionalId || !date) {
      return NextResponse.json(
        { error: 'Missing professionalId or date', success: false },
        { status: 400 }
      )
    }

    console.log(`🔍 Checking availability for professional ${professionalId} on ${date}`)

    // Fetch all bookings for this professional on this date
    const bookingsResponse = await fetch(
      `${request.nextUrl.origin}/api/bookings?professionalId=${professionalId}`,
      { cache: 'no-store' }
    )

    if (!bookingsResponse.ok) {
      throw new Error('Failed to fetch bookings')
    }

    const bookingsData = await bookingsResponse.json()
    const bookings = bookingsData.bookings || []

    // Filter bookings for the specific date
    const dateBookings = bookings.filter((booking: any) => {
      const bookingDate = booking.scheduledDate
      return bookingDate === date
    })

    console.log(`📅 Found ${dateBookings.length} bookings on ${date}:`, dateBookings)

    // Extract booked time slots
    const bookedSlots = dateBookings.map((booking: any) => booking.scheduledTime)

    // Calculate available slots
    const availableSlots = ALL_TIME_SLOTS.filter(slot => !bookedSlots.includes(slot))

    console.log(`✅ Available slots:`, availableSlots)
    console.log(`🚫 Booked slots:`, bookedSlots)

    return NextResponse.json({
      success: true,
      professionalId,
      date,
      allSlots: ALL_TIME_SLOTS,
      availableSlots,
      bookedSlots,
      totalSlots: ALL_TIME_SLOTS.length,
      availableCount: availableSlots.length,
      bookedCount: bookedSlots.length,
    })
  } catch (error) {
    console.error('❌ Error checking availability:', error)
    return NextResponse.json(
      { error: 'Failed to check availability', success: false },
      { status: 500 }
    )
  }
}
