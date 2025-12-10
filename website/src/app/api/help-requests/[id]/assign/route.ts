// Assign volunteer to help request
import { NextRequest, NextResponse } from 'next/server'

export async function PUT(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const { id } = params
    const body = await request.json()

    // Validation
    if (!body.volunteerId) {
      return NextResponse.json(
        { error: 'volunteerId is required', success: false },
        { status: 400 }
      )
    }

    // In production: Update in Supabase
    // For now, return mock success response

    const updatedRequest = {
      id,
      volunteerId: body.volunteerId,
      volunteerName: body.volunteerName || 'Εθελοντής',
      status: 'assigned',
      assignedAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    }

    return NextResponse.json({
      request: updatedRequest,
      message: 'Volunteer assigned successfully. Requester will be notified.',
      success: true,
    })
  } catch (error) {
    console.error('Error assigning volunteer:', error)
    return NextResponse.json(
      { error: 'Failed to assign volunteer', success: false },
      { status: 500 }
    )
  }
}
