import { NextRequest, NextResponse } from 'next/server'

// Store pledges in memory
declare global {
  var pledgesStore: any[]
}

globalThis.pledgesStore = globalThis.pledgesStore || []

export async function GET(request: NextRequest) {
  try {
    const { searchParams } = new URL(request.url)
    const projectId = searchParams.get('projectId')

    let pledges = [...globalThis.pledgesStore]

    // Filter by project ID if provided
    if (projectId) {
      pledges = pledges.filter(p => p.projectId === projectId)
    }

    return NextResponse.json(pledges)
  } catch (error) {
    console.error('Error fetching pledges:', error)
    return NextResponse.json(
      { error: 'Failed to fetch pledges' },
      { status: 500 }
    )
  }
}

export async function POST(request: NextRequest) {
  try {
    const body = await request.json()
    
    // Validation
    if (!body.projectId || !body.amount || !body.type) {
      return NextResponse.json(
        { error: 'Missing required fields' },
        { status: 400 }
      )
    }

    // Create new pledge
    const newPledge = {
      id: `pledge-${Date.now()}`,
      projectId: body.projectId,
      userId: body.userId || 'user-1',
      userName: body.userName || 'Χρήστης',
      amount: parseFloat(body.amount),
      type: body.type, // 'money', 'time', 'materials'
      message: body.message || '',
      status: 'pending',
      createdAt: new Date().toISOString()
    }

    // Add to store
    globalThis.pledgesStore.push(newPledge)

    // Update project with new pledge amount
    const projects = globalThis.projectsStore || []
    const projectIndex = projects.findIndex((p: any) => p.id === body.projectId)
    
    if (projectIndex !== -1) {
      projects[projectIndex].pledgedAmount = (projects[projectIndex].pledgedAmount || 0) + newPledge.amount
      projects[projectIndex].pledgeCount = (projects[projectIndex].pledgeCount || 0) + 1
      globalThis.projectsStore = projects
    }

    console.log('✅ Created new pledge for project:', body.projectId)

    return NextResponse.json(newPledge, { status: 201 })
  } catch (error) {
    console.error('Error creating pledge:', error)
    return NextResponse.json(
      { error: 'Failed to create pledge' },
      { status: 500 }
    )
  }
}
