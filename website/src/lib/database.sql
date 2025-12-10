-- PolisPraxis 2.0 - Complete Database Schema
-- Full platform: Bookings, Help Requests, Civic Projects, Auth
-- Run these SQL commands in Supabase SQL Editor

-- ============================================
-- 1. USERS & PROFILES
-- ============================================

-- Extended user profiles (links to Supabase auth.users)
CREATE TABLE IF NOT EXISTS public.profiles (
  id UUID REFERENCES auth.users(id) PRIMARY KEY,
  email TEXT UNIQUE NOT NULL,
  name TEXT NOT NULL,
  phone TEXT,
  address TEXT,
  city TEXT DEFAULT 'Athens',
  role TEXT CHECK (role IN ('citizen', 'volunteer', 'professional', 'municipality')) DEFAULT 'citizen',
  avatar TEXT,
  bio TEXT,
  verified BOOLEAN DEFAULT false,
  rating DECIMAL(3,2) DEFAULT 5.0,
  total_reviews INTEGER DEFAULT 0,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Professional profiles (ειδικοί - ηλεκτρολόγοι, υδραυλικοί κλπ)
CREATE TABLE IF NOT EXISTS public.professionals (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES public.profiles(id) ON DELETE CASCADE UNIQUE,
  profession TEXT NOT NULL, -- 'electrician', 'plumber', 'carpenter', etc
  license_number TEXT,
  years_experience INTEGER,
  hourly_rate DECIMAL(10,2),
  municipality_subsidized BOOLEAN DEFAULT true,
  subsidized_rate DECIMAL(10,2), -- Τιμή με επιδότηση δήμου
  availability JSONB, -- { "monday": ["09:00-17:00"], ... }
  service_areas TEXT[], -- Περιοχές που εξυπηρετεί
  specializations TEXT[],
  approved_by_municipality BOOLEAN DEFAULT false,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- 2. BOOKING SYSTEM (Ραντεβού με Ειδικούς)
-- ============================================

CREATE TABLE IF NOT EXISTS public.bookings (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  citizen_id UUID REFERENCES public.profiles(id) NOT NULL,
  professional_id UUID REFERENCES public.professionals(id) NOT NULL,
  service_type TEXT NOT NULL, -- 'electrical', 'plumbing', 'carpentry', etc
  scheduled_date DATE NOT NULL,
  scheduled_time TIME NOT NULL,
  duration_hours INTEGER DEFAULT 2,
  address TEXT NOT NULL,
  description TEXT NOT NULL,
  status TEXT CHECK (status IN ('pending', 'confirmed', 'in_progress', 'completed', 'cancelled')) DEFAULT 'pending',
  
  -- Pricing
  base_price DECIMAL(10,2) NOT NULL,
  municipality_subsidy DECIMAL(10,2) DEFAULT 0,
  citizen_pays DECIMAL(10,2) NOT NULL, -- Αυτό πληρώνει ο δημότης
  
  -- Completion & Rating
  completion_notes TEXT,
  citizen_rating INTEGER CHECK (citizen_rating BETWEEN 1 AND 5),
  citizen_review TEXT,
  professional_rating INTEGER CHECK (professional_rating BETWEEN 1 AND 5),
  
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  completed_at TIMESTAMP WITH TIME ZONE
);

-- ============================================
-- 3. HELP REQUESTS (Αιτήματα Βοήθειας)
-- ============================================

CREATE TABLE IF NOT EXISTS public.help_requests (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  requester_id UUID REFERENCES public.profiles(id) NOT NULL,
  title TEXT NOT NULL,
  description TEXT NOT NULL,
  category TEXT NOT NULL, -- 'home_repair', 'moving', 'gardening', 'shopping', 'companionship', etc
  urgency TEXT CHECK (urgency IN ('low', 'medium', 'high')) DEFAULT 'medium',
  location TEXT NOT NULL,
  status TEXT CHECK (status IN ('open', 'assigned', 'in_progress', 'completed', 'cancelled')) DEFAULT 'open',
  
  -- Volunteer assignment
  volunteer_id UUID REFERENCES public.profiles(id),
  assigned_at TIMESTAMP WITH TIME ZONE,
  
  -- Completion
  completed_at TIMESTAMP WITH TIME ZONE,
  rating INTEGER CHECK (rating BETWEEN 1 AND 5),
  feedback TEXT,
  
  images TEXT[],
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- 4. CIVIC PROJECTS (Προτάσεις Έργων)
-- ============================================

CREATE TABLE IF NOT EXISTS public.projects (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  title TEXT NOT NULL,
  description TEXT,
  category TEXT NOT NULL,
  status TEXT DEFAULT 'pending_approval',
  location JSONB NOT NULL,
  creator_id UUID REFERENCES public.profiles(id),
  budget_needed DECIMAL(10,2) DEFAULT 0,
  budget_pledged DECIMAL(10,2) DEFAULT 0,
  images TEXT[],
  municipality_approved BOOLEAN DEFAULT false,
  municipality_notes TEXT,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Pledges table
CREATE TABLE IF NOT EXISTS public.pledges (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  project_id UUID REFERENCES public.projects(id) ON DELETE CASCADE,
  user_id UUID REFERENCES public.profiles(id),
  type TEXT CHECK (type IN ('time', 'money', 'materials')),
  amount DECIMAL(10,2),
  hours INTEGER,
  materials TEXT,
  description TEXT,
  status TEXT DEFAULT 'pending',
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- 5. CHATBOT CONVERSATIONS (AI Βοηθός)
-- ============================================

CREATE TABLE IF NOT EXISTS public.chatbot_conversations (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES public.profiles(id),
  messages JSONB NOT NULL DEFAULT '[]', -- Array of {role, content, timestamp}
  context TEXT, -- 'booking', 'help_request', 'project', 'general'
  recommended_action JSONB, -- What the AI suggested
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
  updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- 6. NOTIFICATIONS
-- ============================================

CREATE TABLE IF NOT EXISTS public.notifications (
  id UUID DEFAULT gen_random_uuid() PRIMARY KEY,
  user_id UUID REFERENCES public.profiles(id) NOT NULL,
  type TEXT NOT NULL, -- 'booking_confirmed', 'help_request_assigned', 'pledge_received', etc
  title TEXT NOT NULL,
  message TEXT NOT NULL,
  link TEXT,
  read BOOLEAN DEFAULT false,
  created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ============================================
-- 7. ROW LEVEL SECURITY
-- ============================================

ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.professionals ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.bookings ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.help_requests ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.projects ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.pledges ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.chatbot_conversations ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.notifications ENABLE ROW LEVEL SECURITY;

-- ============================================
-- 8. POLICIES
-- ============================================

-- Profiles
CREATE POLICY "Public profiles viewable by everyone" ON public.profiles FOR SELECT USING (true);
CREATE POLICY "Users can update own profile" ON public.profiles FOR UPDATE USING (auth.uid() = id);

-- Professionals
CREATE POLICY "Approved professionals viewable by everyone" ON public.professionals FOR SELECT USING (approved_by_municipality = true);
CREATE POLICY "Professionals can update own profile" ON public.professionals FOR UPDATE USING (auth.uid() = user_id);

-- Bookings
CREATE POLICY "Users can view own bookings" ON public.bookings FOR SELECT USING (
  auth.uid() = citizen_id OR 
  auth.uid() IN (SELECT user_id FROM public.professionals WHERE id = professional_id)
);
CREATE POLICY "Citizens can create bookings" ON public.bookings FOR INSERT WITH CHECK (auth.uid() = citizen_id);
CREATE POLICY "Users can update own bookings" ON public.bookings FOR UPDATE USING (
  auth.uid() = citizen_id OR 
  auth.uid() IN (SELECT user_id FROM public.professionals WHERE id = professional_id)
);

-- Help Requests
CREATE POLICY "Help requests viewable by everyone" ON public.help_requests FOR SELECT USING (true);
CREATE POLICY "Authenticated users can create help requests" ON public.help_requests FOR INSERT WITH CHECK (auth.uid() = requester_id);
CREATE POLICY "Requester and volunteer can update" ON public.help_requests FOR UPDATE USING (
  auth.uid() = requester_id OR auth.uid() = volunteer_id
);

-- Projects
CREATE POLICY "Projects viewable by everyone" ON public.projects FOR SELECT USING (true);
CREATE POLICY "Authenticated users can create projects" ON public.projects FOR INSERT WITH CHECK (auth.uid() = creator_id);

-- Pledges
CREATE POLICY "Pledges viewable by everyone" ON public.pledges FOR SELECT USING (true);
CREATE POLICY "Authenticated users can create pledges" ON public.pledges FOR INSERT WITH CHECK (auth.uid() = user_id);

-- Notifications
CREATE POLICY "Users can view own notifications" ON public.notifications FOR SELECT USING (auth.uid() = user_id);
CREATE POLICY "Users can update own notifications" ON public.notifications FOR UPDATE USING (auth.uid() = user_id);

-- ============================================
-- 9. INDEXES FOR PERFORMANCE
-- ============================================

-- Profiles
CREATE INDEX IF NOT EXISTS idx_profiles_role ON public.profiles(role);
CREATE INDEX IF NOT EXISTS idx_profiles_city ON public.profiles(city);

-- Professionals
CREATE INDEX IF NOT EXISTS idx_professionals_profession ON public.professionals(profession);
CREATE INDEX IF NOT EXISTS idx_professionals_approved ON public.professionals(approved_by_municipality);

-- Bookings
CREATE INDEX IF NOT EXISTS idx_bookings_citizen ON public.bookings(citizen_id);
CREATE INDEX IF NOT EXISTS idx_bookings_professional ON public.bookings(professional_id);
CREATE INDEX IF NOT EXISTS idx_bookings_status ON public.bookings(status);
CREATE INDEX IF NOT EXISTS idx_bookings_date ON public.bookings(scheduled_date);

-- Help Requests
CREATE INDEX IF NOT EXISTS idx_help_requests_status ON public.help_requests(status);
CREATE INDEX IF NOT EXISTS idx_help_requests_category ON public.help_requests(category);
CREATE INDEX IF NOT EXISTS idx_help_requests_requester ON public.help_requests(requester_id);
CREATE INDEX IF NOT EXISTS idx_help_requests_volunteer ON public.help_requests(volunteer_id);

-- Projects
CREATE INDEX IF NOT EXISTS idx_projects_status ON public.projects(status);
CREATE INDEX IF NOT EXISTS idx_projects_category ON public.projects(category);

-- Pledges
CREATE INDEX IF NOT EXISTS idx_pledges_project ON public.pledges(project_id);
CREATE INDEX IF NOT EXISTS idx_pledges_user ON public.pledges(user_id);

-- Notifications
CREATE INDEX IF NOT EXISTS idx_notifications_user ON public.notifications(user_id);
CREATE INDEX IF NOT EXISTS idx_notifications_read ON public.notifications(read);

-- ============================================
-- 10. FUNCTIONS & TRIGGERS
-- ============================================

-- Update updated_at timestamp
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
  NEW.updated_at = NOW();
  RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER update_profiles_updated_at BEFORE UPDATE ON public.profiles FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_bookings_updated_at BEFORE UPDATE ON public.bookings FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_help_requests_updated_at BEFORE UPDATE ON public.help_requests FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();
CREATE TRIGGER update_projects_updated_at BEFORE UPDATE ON public.projects FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

