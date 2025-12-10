// ============================================
// HelpMeAnytime 2.0 - Complete Type Definitions
// ============================================
// Full platform: Bookings, Help Requests, Civic Projects, Auth
// ============================================

// ============================================
// 1. USER & PROFILES
// ============================================

export interface User {
  id: string
  email: string
  name: string
  phone?: string
  address?: string
  city?: string
  role: 'citizen' | 'volunteer' | 'professional' | 'municipality'
  avatar?: string
  bio?: string
  verified: boolean
  rating: number
  totalReviews: number
  createdAt: Date
  updatedAt: Date
}

export interface Professional {
  id: string
  userId: string
  user?: User
  profession: ProfessionType
  licenseNumber?: string
  yearsExperience: number
  hourlyRate: number
  municipalitySubsidized: boolean
  subsidizedRate: number // Τιμή με επιδότηση
  availability: WeeklyAvailability
  serviceAreas: string[]
  specializations: string[]
  approvedByMunicipality: boolean
  createdAt: Date
}

export type ProfessionType = 
  | 'electrician' // Ηλεκτρολόγος
  | 'plumber' // Υδραυλικός
  | 'carpenter' // Μαραγκός
  | 'painter' // Βαφέας
  | 'mason' // Οικοδόμος
  | 'hvac' // Κλιματισμός
  | 'gardener' // Κηπουρός
  | 'cleaner' // Καθαριστής/Καθαρίστρια
  | 'locksmith' // Κλειδαράς
  | 'appliance_repair' // Επισκευή Συσκευών
  | 'other'

export interface WeeklyAvailability {
  monday?: string[]
  tuesday?: string[]
  wednesday?: string[]
  thursday?: string[]
  friday?: string[]
  saturday?: string[]
  sunday?: string[]
}

// ============================================
// 2. BOOKING SYSTEM
// ============================================

export interface Booking {
  id: string
  citizenId: string
  citizen?: User
  professionalId: string
  professional?: Professional
  serviceType: string
  scheduledDate: Date
  scheduledTime: string
  durationHours: number
  address: string
  description: string
  status: BookingStatus
  
  // Pricing
  basePrice: number
  municipalitySubsidy: number
  citizenPays: number
  
  // Completion
  completionNotes?: string
  citizenRating?: number
  citizenReview?: string
  professionalRating?: number
  
  createdAt: Date
  updatedAt: Date
  completedAt?: Date
}

export type BookingStatus = 
  | 'pending' 
  | 'confirmed' 
  | 'in_progress' 
  | 'completed' 
  | 'cancelled'

// ============================================
// 3. HELP REQUESTS
// ============================================

export interface HelpRequest {
  id: string
  requesterId: string
  requester?: User
  title: string
  description: string
  category: HelpCategory
  urgency: 'low' | 'medium' | 'high'
  location: string
  status: HelpRequestStatus
  
  // Volunteer
  volunteerId?: string
  volunteer?: User
  assignedAt?: Date
  
  // Completion
  completedAt?: Date
  rating?: number
  feedback?: string
  
  images?: string[]
  createdAt: Date
  updatedAt: Date
}

export type HelpCategory = 
  | 'home_repair' // Μικροεπισκευές
  | 'moving' // Μετακόμιση
  | 'gardening' // Κηπουρική
  | 'shopping' // Ψώνια
  | 'companionship' // Συντροφιά
  | 'technology' // Τεχνολογία/Υπολογιστές
  | 'translation' // Μετάφραση
  | 'tutoring' // Ιδιαίτερα Μαθήματα
  | 'pet_care' // Φροντίδα Κατοικιδίων
  | 'other'

export type HelpRequestStatus = 
  | 'open' 
  | 'assigned' 
  | 'in_progress' 
  | 'completed' 
  | 'cancelled'

// ============================================
// 4. CIVIC PROJECTS (Existing)
// ============================================

export interface Project {
  id: string
  title: string
  description: string
  category: ProjectCategory
  status: ProjectStatus
  location: Location
  creatorId: string
  creator?: User
  budgetNeeded: number
  budgetPledged: number
  pledgeCount: number
  images?: string[]
  pledges?: Pledge[]
  municipalityApproved: boolean
  municipalityNotes?: string
  createdAt: string
  updatedAt: string
  completedAt?: string
}

export interface Pledge {
  id: string
  projectId: string
  userId: string
  user?: User
  type: PledgeType
  amount?: number
  hours?: number
  materials?: string
  description: string
  status: 'pending' | 'confirmed' | 'completed' | 'cancelled'
  createdAt: Date
}

export interface Location {
  lat: number
  lng: number
  address: string
  district?: string
}

export type ProjectCategory = 
  | 'infrastructure' 
  | 'parks' 
  | 'community' 
  | 'environment' 
  | 'culture' 
  | 'safety'
  | 'other'

export type ProjectStatus = 
  | 'draft'
  | 'pending_approval'
  | 'approved'
  | 'in_progress'
  | 'completed'
  | 'rejected'

export type PledgeType = 'time' | 'money' | 'materials'

// ============================================
// 5. CHATBOT
// ============================================

export interface ChatMessage {
  role: 'user' | 'assistant' | 'system'
  content: string
  timestamp: Date
}

export interface ChatbotConversation {
  id: string
  userId: string
  messages: ChatMessage[]
  context: 'booking' | 'help_request' | 'project' | 'general'
  recommendedAction?: {
    type: 'create_booking' | 'create_help_request' | 'view_professionals' | 'other'
    data: any
  }
  createdAt: Date
  updatedAt: Date
}

// ============================================
// 6. NOTIFICATIONS
// ============================================

export interface Notification {
  id: string
  userId: string
  type: NotificationType
  title: string
  message: string
  link?: string
  read: boolean
  createdAt: Date
}

export type NotificationType = 
  | 'booking_confirmed'
  | 'booking_cancelled'
  | 'booking_completed'
  | 'help_request_assigned'
  | 'help_request_completed'
  | 'pledge_received'
  | 'project_approved'
  | 'project_rejected'
  | 'new_message'
  | 'rating_received'

// ============================================
// 7. STATISTICS & ANALYTICS
// ============================================

export interface MunicipalityStats {
  totalProjects: number
  pendingApprovals: number
  activeProjects: number
  completedProjects: number
  totalPledges: number
  totalMoneyPledged: number
  totalVolunteerHours: number
  activeBookings: number
  completedBookings: number
  totalSubsidySpent: number
  openHelpRequests: number
  completedHelpRequests: number
}

export interface PledgeStats {
  total_money: number
  total_hours: number
  total_materials: number
  total_pledges: number
  progress_percentage: number
  breakdown: {
    money: { count: number; total_amount: number }
    time: { count: number; total_hours: number }
    materials: { count: number }
  }
}

// ============================================
// 8. API RESPONSES
// ============================================

export interface ApiResponse<T> {
  data?: T
  error?: string
  message?: string
  success: boolean
}

export interface PaginatedResponse<T> {
  data: T[]
  total: number
  page: number
  pageSize: number
  hasMore: boolean
}

// ============================================
// 9. FORM INPUTS
// ============================================

export type CreateBookingInput = Omit<Booking, 'id' | 'createdAt' | 'updatedAt' | 'status' | 'completedAt'>
export type CreateHelpRequestInput = Omit<HelpRequest, 'id' | 'createdAt' | 'updatedAt' | 'status' | 'volunteerId' | 'assignedAt' | 'completedAt'>
export type CreateProjectInput = Omit<Project, 'id' | 'createdAt' | 'updatedAt' | 'status' | 'municipalityApproved'>
export type CreatePledgeInput = Omit<Pledge, 'id' | 'createdAt' | 'status'>
export type RegisterProfessionalInput = Omit<Professional, 'id' | 'createdAt' | 'approvedByMunicipality'>

// ============================================
// 10. FILTERS
// ============================================

export interface BookingFilters {
  status?: BookingStatus
  citizenId?: string
  professionalId?: string
  dateFrom?: Date
  dateTo?: Date
}

export interface HelpRequestFilters {
  status?: HelpRequestStatus
  category?: HelpCategory
  urgency?: 'low' | 'medium' | 'high'
  requesterId?: string
  volunteerId?: string
}

export interface ProjectFilters {
  status?: ProjectStatus
  category?: ProjectCategory
  municipalityApproved?: boolean
}

export interface ProfessionalFilters {
  profession?: ProfessionType
  approved?: boolean
  serviceArea?: string
  available?: boolean
}
