// ============================================
// 👨‍💻 DEVELOPER 2 - TASK 4 (Hour 6-8)
// ============================================
// 
// 🚀 ΤΟ REAL-TIME COUNTER - THE WOW MOMENT!
//
// ΤΙ ΠΡΕΠΕΙ ΝΑ ΚΑΝΕΙΣ:
// 1. Πάρε projectId από query: ?projectId=xxx
//
// 2. ΥΠΟΛΟΓΙΣΕ τα totals:
//    SELECT 
//      SUM(amount) as total_money,
//      SUM(hours) as total_hours,
//      COUNT(*) FILTER (WHERE type='materials') as total_materials
//    FROM pledges 
//    WHERE project_id = xxx
//
// 3. Πάρε το budget_needed από το project
//
// 4. ΥΠΟΛΟΓΙΣΕ το progress percentage:
//    progress = (total_money / budget_needed) * 100
//
// 5. Return:
//    {
//      stats: {
//        total_money: 450,
//        total_hours: 35,
//        total_materials: 8,
//        pledge_count: 15,
//        progress_percentage: 90,
//        breakdown: {
//          money_pledges: 10,
//          time_pledges: 3,
//          materials_pledges: 2
//        }
//      }
//    }
//
// ΑΥΤΟ θα το χρησιμοποιήσεις για τον animated counter!
//
// BONUS (αν έχεις χρόνο):
// - Πρόσθεσε Supabase real-time subscriptions
// - Ο counter θα ανανεώνεται αυτόματα όταν κάποιος κάνει pledge!
//
// TESTING:
// curl http://localhost:3000/api/pledges/stats?projectId=1
//
// ΧΡΟΝΟΣ: 2 ώρες
// COMMIT: "feat: implement pledge statistics and real-time updates"
// ============================================

import { NextRequest, NextResponse } from 'next/server'
import { mockPledges, mockProjects } from '@/lib/mockData'

export async function GET(request: NextRequest) {
  const { searchParams } = new URL(request.url)
  const projectId = searchParams.get('projectId')
  
  if (!projectId) {
    return NextResponse.json(
      { error: 'Project ID required' },
      { status: 400 }
    )
  }
  
  const projectPledges = mockPledges.filter(p => String(p.projectId) === projectId)
  const project = mockProjects.find(p => String(p.id) === projectId)
  
  // Υπολόγισε totals
  const total_money = projectPledges
    .filter(p => p.type === 'money')
    .reduce((sum, p) => sum + (p.amount || 0), 0)
  
  const total_hours = projectPledges
    .filter(p => p.type === 'time')
    .reduce((sum, p) => sum + (p.hours || 0), 0)
  
  const total_materials = projectPledges
    .filter(p => p.type === 'materials').length
  
  const progress_percentage = project 
    ? Math.round((total_money / project.budgetNeeded) * 100)
    : 0
  
  return NextResponse.json({
    stats: {
      total_money,
      total_hours,
      total_materials,
      pledge_count: projectPledges.length,
      progress_percentage,
      breakdown: {
        money_pledges: projectPledges.filter(p => p.type === 'money').length,
        time_pledges: projectPledges.filter(p => p.type === 'time').length,
        materials_pledges: projectPledges.filter(p => p.type === 'materials').length,
      }
    }
  })
}
