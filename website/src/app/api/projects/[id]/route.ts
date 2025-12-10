import { NextRequest, NextResponse } from 'next/server'

export async function GET(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const id = params.id

    // Get projects from global store
    const projects = globalThis.projectsStore || []
    const project = projects.find((p: any) => p.id === id)

    if (!project) {
      return NextResponse.json(
        { error: 'Project not found' },
        { status: 404 }
      )
    }

    return NextResponse.json(project)
  } catch (error) {
    console.error('Error fetching project:', error)
    return NextResponse.json(
      { error: 'Failed to fetch project' },
      { status: 500 }
    )
  }
}

export async function PUT(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const id = params.id
    const body = await request.json()

    // Get projects from global store
    const projects = globalThis.projectsStore || []
    const projectIndex = projects.findIndex((p: any) => p.id === id)

    if (projectIndex === -1) {
      return NextResponse.json(
        { error: 'Project not found' },
        { status: 404 }
      )
    }

    // Update project
    const updatedProject = {
      ...projects[projectIndex],
      ...body,
      updatedAt: new Date().toISOString().split('T')[0]
    }

    projects[projectIndex] = updatedProject
    globalThis.projectsStore = projects

    console.log('✅ Updated project:', updatedProject.title)

    return NextResponse.json(updatedProject)
  } catch (error) {
    console.error('Error updating project:', error)
    return NextResponse.json(
      { error: 'Failed to update project' },
      { status: 500 }
    )
  }
}

export async function DELETE(
  request: NextRequest,
  { params }: { params: { id: string } }
) {
  try {
    const projectId = params.id
    const initialCount = globalThis.projectsStore.length

    // Find project index
    const projectIndex = globalThis.projectsStore.findIndex(p => p.id === projectId)

    if (projectIndex === -1) {
      return NextResponse.json({ error: 'Project not found' }, { status: 404 })
    }

    // Remove project from store
    globalThis.projectsStore.splice(projectIndex, 1)

    console.log(`🗑️ Deleted project with ID: ${projectId}`)
    console.log(`📦 Projects in store before: ${initialCount}, after: ${globalThis.projectsStore.length}`)

    return NextResponse.json({ message: 'Project deleted successfully' }, { status: 200 })
  } catch (error) {
    console.error('Error deleting project:', error)
    return NextResponse.json(
      { error: 'Failed to delete project' },
      { status: 500 }
    )
  }
}
