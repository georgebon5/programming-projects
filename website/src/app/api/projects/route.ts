import { NextRequest, NextResponse } from 'next/server'

// Mock data για projects
const mockProjects = [
  {
    id: '1',
    title: 'Ανακαίνιση Παιδικής Χαράς Εξαρχείων',
    description: 'Η παιδική χαρά χρειάζεται επισκευή των παιχνιδιών και βελτίωση της ασφάλειας',
    category: 'parks',
    budgetNeeded: 5000,
    budgetPledged: 2340,
    pledgeCount: 23,
    status: 'active',
    creatorId: '1',
    creatorName: 'Μαρία Παπαδοπούλου',
    location: {
      address: 'Πλατεία Εξαρχείων',
      district: 'Εξάρχεια',
      lat: 37.9888,
      lng: 23.7334
    },
    createdAt: '2025-01-10',
    updatedAt: '2025-01-14'
  },
  {
    id: '2',
    title: 'Δημιουργία Πράσινου Σημείου',
    description: 'Πρόταση για δημιουργία σημείου ανακύκλωσης και κομποστοποίησης',
    category: 'environment',
    budgetNeeded: 3500,
    budgetPledged: 1200,
    pledgeCount: 15,
    status: 'active',
    creatorId: '2',
    creatorName: 'Γιώργος Κωνσταντίνου',
    location: {
      address: 'Πάρκο Αλσους',
      district: 'Παγκράτι',
      lat: 37.9695,
      lng: 23.7539
    },
    createdAt: '2025-01-08',
    updatedAt: '2025-01-13'
  }
]

// Store new projects in memory
declare global {
  var projectsStore: any[]
}

globalThis.projectsStore = globalThis.projectsStore || [...mockProjects]

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const category = searchParams.get('category')
    const status = searchParams.get('status')

    let projects = [...globalThis.projectsStore]

    // Filter by category
    if (category && category !== 'all') {
      projects = projects.filter(p => p.category === category)
    }

    // Filter by status
    if (status && status !== 'all') {
      projects = projects.filter(p => p.status === status)
    }

    // Sort by date (newest first)
    projects.sort((a, b) => new Date(b.createdAt).getTime() - new Date(a.createdAt).getTime())

    return NextResponse.json(projects)
  } catch (error) {
    console.error('Error fetching projects:', error)
    return NextResponse.json(
      { error: 'Failed to fetch projects' },
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    // Validation
    if (!body.title || !body.description || !body.category || !body.budgetNeeded) {
      return NextResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      )
    }

    if (body.description.length < 50) {
      return NextResponse.json(
        { error: 'Description must be at least 50 characters' },
        { status: 400 }
      )
    }

    // Create new project
    const newProject = {
      id: `project-${Date.now()}`,
      title: body.title,
      description: body.description,
      category: body.category,
      budgetNeeded: parseFloat(body.budgetNeeded),
      budgetPledged: 0,
      pledgeCount: 0,
      status: 'active',
      creatorId: body.creatorId || 'user-1',
      creatorName: body.creatorName || 'Χρήστης',
      location: {
        address: body.location?.address || '',
        district: body.location?.district || '',
        lat: body.location?.lat || 37.9755,
        lng: body.location?.lng || 23.7348
      },
      createdAt: new Date().toISOString().split('T')[0],
      updatedAt: new Date().toISOString().split('T')[0]
    }

    // Add to store
    globalThis.projectsStore.push(newProject)

    console.log('✅ Created new project:', newProject.title)

    return NextResponse.json(newProject, { status: 201 })
  } catch (error) {
    console.error('Error creating project:', error)
    return NextResponse.json(
      { error: 'Failed to create project' },
      { status: 500 }
    )
  }
}
