// Professionals API - Ειδικοί (Ηλεκτρολόγοι, Υδραυλικοί, κλπ)
import { NextRequest, NextResponse } from 'next/server'

// Mock data για testing (θα το αντικαταστήσουμε με Supabase αργότερα)
const mockProfessionals = [
  {
    id: '1',
    userId: 'user-1',
    profession: 'electrician',
    name: 'Γιάννης Παπαδόπουλος',
    email: 'john@example.com',
    phone: '6912345678',
    licenseNumber: 'EL-12345',
    yearsExperience: 10,
    hourlyRate: 50,
    municipalitySubsidized: true,
    subsidizedRate: 15,
    rating: 4.8,
    totalReviews: 24,
    availability: {
      monday: ['09:00-17:00'],
      tuesday: ['09:00-17:00'],
      wednesday: ['09:00-17:00'],
      thursday: ['09:00-17:00'],
      friday: ['09:00-17:00'],
    },
    serviceAreas: ['Αθήνα Κέντρο', 'Καλλιθέα', 'Νέα Σμύρνη'],
    specializations: ['Εγκαταστάσεις', 'Επισκευές', 'Συντήρηση'],
    approvedByMunicipality: true,
    bio: 'Επαγγελματίας ηλεκτρολόγος με 10 χρόνια εμπειρίας. Εξειδικεύομαι σε οικιακές και εμπορικές εγκαταστάσεις.',
    avatar: null,
  },
  {
    id: '2',
    userId: 'user-2',
    profession: 'plumber',
    name: 'Μαρία Γεωργίου',
    email: 'maria@example.com',
    phone: '6987654321',
    licenseNumber: 'PL-67890',
    yearsExperience: 8,
    hourlyRate: 45,
    municipalitySubsidized: true,
    subsidizedRate: 12,
    rating: 4.9,
    totalReviews: 31,
    availability: {
      monday: ['08:00-16:00'],
      tuesday: ['08:00-16:00'],
      wednesday: ['08:00-16:00'],
      thursday: ['08:00-16:00'],
      friday: ['08:00-16:00'],
      saturday: ['10:00-14:00'],
    },
    serviceAreas: ['Αθήνα', 'Πειραιάς', 'Γλυφάδα'],
    specializations: ['Υδραυλικά', 'Θέρμανση', 'Επισκευές'],
    approvedByMunicipality: true,
    bio: 'Έμπειρη υδραυλικός με εξειδίκευση σε συστήματα θέρμανσης και ηλιακούς θερμοσίφωνες.',
    avatar: null,
  },
  {
    id: '3',
    userId: 'user-3',
    profession: 'carpenter',
    name: 'Κώστας Αντωνίου',
    email: 'kostas@example.com',
    phone: '6945678901',
    licenseNumber: 'CA-11111',
    yearsExperience: 15,
    hourlyRate: 40,
    municipalitySubsidized: true,
    subsidizedRate: 10,
    rating: 4.7,
    totalReviews: 18,
    availability: {
      tuesday: ['09:00-17:00'],
      wednesday: ['09:00-17:00'],
      thursday: ['09:00-17:00'],
      friday: ['09:00-17:00'],
      saturday: ['09:00-13:00'],
    },
    serviceAreas: ['Αθήνα', 'Χαλάνδρι', 'Μαρούσι'],
    specializations: ['Έπιπλα', 'Πόρτες', 'Παράθυρα'],
    approvedByMunicipality: true,
    bio: 'Μαραγκός με πάθος για την δουλειά μου. Φτιάχνω custom έπιπλα και κάνω ανακαινίσεις.',
    avatar: null,
  },
]

// GET /api/professionals - Get all professionals
export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const profession = searchParams.get('profession')
    const serviceArea = searchParams.get('serviceArea')
    const approved = searchParams.get('approved')

    let filtered = [...mockProfessionals]

    // Filter by profession
    if (profession) {
      filtered = filtered.filter(p => p.profession === profession)
    }

    // Filter by service area
    if (serviceArea) {
      filtered = filtered.filter(p => 
        p.serviceAreas.some(area => 
          area.toLowerCase().includes(serviceArea.toLowerCase())
        )
      )
    }

    // Filter by approval status
    if (approved !== null) {
      const isApproved = approved === 'true'
      filtered = filtered.filter(p => p.approvedByMunicipality === isApproved)
    }

    return NextResponse.json({
      professionals: filtered,
      total: filtered.length,
      success: true,
    })
  } catch (error) {
    console.error('Error fetching professionals:', error)
    return NextResponse.json(
      { error: 'Failed to fetch professionals', success: false },
      { status: 500 }
    )
  }
}

// POST /api/professionals - Register new professional
export async function POST(request: NextRequest) {
  try {
    const body = await request.json()

    // Validation
    const requiredFields = ['userId', 'profession', 'name', 'email', 'phone', 'hourlyRate']
    const missingFields = requiredFields.filter(field => !body[field])

    if (missingFields.length > 0) {
      return NextResponse.json(
        { 
          error: `Missing required fields: ${missingFields.join(', ')}`,
          success: false 
        },
        { status: 400 }
      )
    }

    // Create new professional (mock - θα γίνει με Supabase)
    const newProfessional = {
      id: `prof-${Date.now()}`,
      ...body,
      rating: 5.0,
      totalReviews: 0,
      approvedByMunicipality: false, // Needs municipality approval
      createdAt: new Date().toISOString(),
    }

    return NextResponse.json({
      professional: newProfessional,
      message: 'Professional registered successfully. Pending municipality approval.',
      success: true,
    }, { status: 201 })
  } catch (error) {
    console.error('Error creating professional:', error)
    return NextResponse.json(
      { error: 'Failed to create professional', success: false },
      { status: 500 }
    )
  }
}
