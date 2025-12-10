// Help Requests API - Αιτήματα Βοήθειας από Εθελοντές
import { NextRequest, NextResponse } from 'next/server'

// Mock data
const mockHelpRequests = [
  {
    id: '1',
    requesterId: 'user-citizen-1',
    requesterName: 'Ελένη Κωνσταντίνου',
    title: 'Χρειάζομαι βοήθεια για μετακόμιση',
    description: 'Θα μετακομίσω σε νέο διαμέρισμα και χρειάζομαι βοήθεια να μεταφέρω μερικά έπιπλα (καναπές, τραπεζαρία, κρεβάτι).',
    category: 'moving',
    urgency: 'medium',
    location: 'Καλλιθέα, Αθήνα',
    status: 'open',
    volunteerId: null,
    volunteerName: null,
    images: [],
    createdAt: '2025-11-14T09:00:00Z',
    updatedAt: '2025-11-14T09:00:00Z',
  },
  {
    id: '2',
    requesterId: 'user-citizen-2',
    requesterName: 'Γιώργος Μιχαηλίδης',
    title: 'Βοήθεια με υπολογιστή',
    description: 'Ο υπολογιστής μου δεν ανοίγει. Χρειάζομαι κάποιον να με βοηθήσει να τον φτιάξω ή να μεταφέρω τα αρχεία μου.',
    category: 'technology',
    urgency: 'high',
    location: 'Πετράλωνα, Αθήνα',
    status: 'assigned',
    volunteerId: 'user-volunteer-1',
    volunteerName: 'Μαρία Παπαδοπούλου',
    assignedAt: '2025-11-14T10:30:00Z',
    images: [],
    createdAt: '2025-11-13T16:00:00Z',
    updatedAt: '2025-11-14T10:30:00Z',
  },
  {
    id: '3',
    requesterId: 'user-citizen-3',
    requesterName: 'Σοφία Αντωνίου',
    title: 'Συντροφιά για ηλικιωμένη',
    description: 'Η μητέρα μου είναι ηλικιωμένη και μένει μόνη. Θα ήθελα κάποιον να την επισκέπτεται 2-3 φορές την εβδομάδα για συντροφιά.',
    category: 'companionship',
    urgency: 'low',
    location: 'Νέα Σμύρνη, Αθήνα',
    status: 'open',
    volunteerId: null,
    volunteerName: null,
    images: [],
    createdAt: '2025-11-12T14:00:00Z',
    updatedAt: '2025-11-12T14:00:00Z',
  },
]

// GET /api/help-requests - Get all help requests
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const status = searchParams.get('status')
    const category = searchParams.get('category')
    const urgency = searchParams.get('urgency')
    const requesterId = searchParams.get('requesterId')
    const volunteerId = searchParams.get('volunteerId')

    let filtered = [...mockHelpRequests]

    // Filter by status
    if (status) {
      filtered = filtered.filter(r => r.status === status)
    }

    // Filter by category
    if (category) {
      filtered = filtered.filter(r => r.category === category)
    }

    // Filter by urgency
    if (urgency) {
      filtered = filtered.filter(r => r.urgency === urgency)
    }

    // Filter by requester
    if (requesterId) {
      filtered = filtered.filter(r => r.requesterId === requesterId)
    }

    // Filter by volunteer
    if (volunteerId) {
      filtered = filtered.filter(r => r.volunteerId === volunteerId)
    }

    // Sort by urgency (high first) then by date (newest first)
    const urgencyOrder = { high: 3, medium: 2, low: 1 }
    filtered.sort((a, b) => {
      const urgencyDiff = urgencyOrder[b.urgency as keyof typeof urgencyOrder] - 
                          urgencyOrder[a.urgency as keyof typeof urgencyOrder]
      if (urgencyDiff !== 0) return urgencyDiff
      return new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime()
    })

    return NextResponse.json({
      requests: filtered,
      total: filtered.length,
      success: true,
    })
  } catch (error) {
    console.error('Error fetching help requests:', error)
    return NextResponse.json(
      { error: 'Failed to fetch help requests', success: false },
      { status: 500 }
    )
  }
}

// POST /api/help-requests - Create new help request
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    // Validation
    const requiredFields = [
      'requesterId',
      'title',
      'description',
      'category',
      'location',
    ]

    const missingFields = requiredFields.filter(field => !body[field])

    if (missingFields.length > 0) {
      return NextResponse.json(
        {
          error: `Missing required fields: ${missingFields.join(', ')}`,
          success: false,
        },
        { status: 400 }
      )
    }

    // Create new help request
    const newRequest = {
      id: `help-${Date.now()}`,
      ...body,
      urgency: body.urgency || 'medium',
      status: 'open',
      volunteerId: null,
      volunteerName: null,
      images: body.images || [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString(),
    }

    // In production: Save to Supabase and send notifications to volunteers

    return NextResponse.json({
      request: newRequest,
      message: 'Help request created successfully. Volunteers will be notified.',
      success: true,
    }, { status: 201 })
  } catch (error) {
    console.error('Error creating help request:', error)
    return NextResponse.json(
      { error: 'Failed to create help request', success: false },
      { status: 500 }
    )
  }
}
