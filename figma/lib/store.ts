import { create } from 'zustand'
import { persist } from 'zustand/middleware'

export type UserRole = 'volunteer' | 'reporter'
export type Priority = 'critical' | 'high' | 'medium' | 'low'
export type CaseStatus = 'active' | 'assigned' | 'found' | 'closed'
export type VolunteerStatus = 'active' | 'busy' | 'offline'
export type WeatherCondition = 'clear' | 'rain' | 'storm' | 'snow' | 'fog' | 'extreme_heat'

export interface User {
  id: string
  name: string
  username: string
  role: UserRole
  skills?: string[]
  address?: string
  status?: VolunteerStatus
  lastPing?: Date
  deviceId?: string
  avatarColor?: string
}

export interface Case {
  id: string
  name: string
  age: number
  ageGroup: string
  emergencyType: string
  description: string
  lastKnownAddress: string
  hoursMissing: number
  phone?: string
  photo?: string
  priority: Priority
  priorityScore: number
  status: CaseStatus
  reporterId: string
  assignedVolunteerId?: string
  assignedTeamId?: string
  createdAt: Date
  aiAnalysis?: {
    reasoning: string
    riskFactors: string[]
    skills: string[]
    recommendedAction: string
    weatherModifier: number
    timeModifier: number
    effectiveScore: number
  }
}

export interface Team {
  id: string
  name: string
  caseId: string
  members: string[]
  requiredRoles: string[]
  type: string
}

export interface CheckIn {
  id: string
  volunteerId: string
  volunteerName: string
  address: string
  status: string
  gpsLat?: number
  gpsLon?: number
  area?: string
  caseId?: string
  notes?: string
  timestamp: Date
}

export interface AILogEntry {
  id: string
  timestamp: Date
  priority: Priority
  eventTitle: string
  detail: string
}

interface AppState {
  // Auth
  currentUser: User | null
  isAuthenticated: boolean
  
  // Theme & Settings
  theme: 'light' | 'dark'
  weatherCondition: WeatherCondition
  sidebarCollapsed: boolean
  
  // Data
  cases: Case[]
  volunteers: User[]
  teams: Team[]
  checkIns: CheckIn[]
  aiLog: AILogEntry[]
  
  // Actions
  login: (user: User) => void
  logout: () => void
  setTheme: (theme: 'light' | 'dark') => void
  setWeatherCondition: (condition: WeatherCondition) => void
  toggleSidebar: () => void
  
  // Case actions
  addCase: (caseData: Omit<Case, 'id' | 'createdAt'>) => void
  updateCase: (id: string, updates: Partial<Case>) => void
  
  // Volunteer actions
  addVolunteer: (volunteer: User) => void
  updateVolunteer: (id: string, updates: Partial<User>) => void
  
  // Team actions
  createTeam: (team: Omit<Team, 'id'>) => void
  updateTeam: (id: string, updates: Partial<Team>) => void
  
  // Check-in actions
  addCheckIn: (checkIn: Omit<CheckIn, 'id' | 'timestamp'>) => void
  
  // AI Log actions
  addAILogEntry: (entry: Omit<AILogEntry, 'id' | 'timestamp'>) => void
  clearAILog: () => void
}

// Demo data
const demoVolunteers: User[] = [
  { id: 'v1', name: 'Sarah Chen', username: 'sarah_sar', role: 'volunteer', skills: ['Medical', 'K9 Handler'], address: '123 Main St', status: 'active', lastPing: new Date(), deviceId: 'DEV001', avatarColor: 'green' },
  { id: 'v2', name: 'Marcus Williams', username: 'marcus_w', role: 'volunteer', skills: ['Drone Operator', 'First Aid'], address: '456 Oak Ave', status: 'active', lastPing: new Date(Date.now() - 120000), deviceId: 'DEV002', avatarColor: 'blue' },
  { id: 'v3', name: 'Elena Rodriguez', username: 'elena_r', role: 'volunteer', skills: ['Navigation', 'Communications'], address: '789 Pine Rd', status: 'busy', lastPing: new Date(Date.now() - 300000), deviceId: 'DEV003', avatarColor: 'purple' },
  { id: 'v4', name: 'James Thompson', username: 'james_t', role: 'volunteer', skills: ['Wilderness Survival', 'Climbing'], address: '321 Cedar Ln', status: 'offline', lastPing: new Date(Date.now() - 3600000), deviceId: 'DEV004', avatarColor: 'orange' },
]

const demoCases: Case[] = [
  {
    id: 'CASE-001',
    name: 'Emily Watson',
    age: 7,
    ageGroup: 'Child',
    emergencyType: 'Missing Person',
    description: 'Last seen wearing a red jacket and blue jeans near Riverside Park. She was walking her dog, a golden retriever named Max.',
    lastKnownAddress: 'Riverside Park, Section B',
    hoursMissing: 4,
    phone: '555-0123',
    priority: 'critical',
    priorityScore: 95,
    status: 'active',
    reporterId: 'r1',
    createdAt: new Date(Date.now() - 4 * 3600000),
    aiAnalysis: {
      reasoning: 'Young child missing in park area during evening hours. High traffic area but multiple exit points. Time-sensitive due to approaching nightfall.',
      riskFactors: ['Young age (7)', 'Evening hours', 'Large search area', 'Potential water hazard nearby'],
      skills: ['K9 Handler', 'Drone Operator', 'First Aid'],
      recommendedAction: 'Deploy K9 unit and drone for aerial coverage. Establish perimeter at park exits.',
      weatherModifier: 0,
      timeModifier: 15,
      effectiveScore: 95
    }
  },
  {
    id: 'CASE-002',
    name: 'Robert Chen',
    age: 72,
    ageGroup: 'Elderly',
    emergencyType: 'Missing Person',
    description: 'Alzheimer patient who wandered from assisted living facility. Last seen wearing gray sweater and khaki pants.',
    lastKnownAddress: 'Sunrise Care Home, 500 Elm St',
    hoursMissing: 2,
    phone: '555-0456',
    priority: 'high',
    priorityScore: 82,
    status: 'assigned',
    reporterId: 'r2',
    assignedVolunteerId: 'v1',
    createdAt: new Date(Date.now() - 2 * 3600000),
    aiAnalysis: {
      reasoning: 'Elderly patient with cognitive impairment. May be disoriented and unable to ask for help. Medical concerns due to age.',
      riskFactors: ['Alzheimer disease', 'Age 72', 'May need medication'],
      skills: ['Medical', 'Communication'],
      recommendedAction: 'Check nearby familiar locations. Alert local businesses.',
      weatherModifier: 0,
      timeModifier: 10,
      effectiveScore: 82
    }
  },
  {
    id: 'CASE-003',
    name: 'Michael Torres',
    age: 35,
    ageGroup: 'Adult',
    emergencyType: 'Lost Hiker',
    description: 'Experienced hiker went on solo trail. Did not return by scheduled time. Has basic gear but limited supplies.',
    lastKnownAddress: 'Mountain View Trail, North Entrance',
    hoursMissing: 8,
    priority: 'medium',
    priorityScore: 65,
    status: 'active',
    reporterId: 'r1',
    createdAt: new Date(Date.now() - 8 * 3600000),
    aiAnalysis: {
      reasoning: 'Experienced adult hiker, likely able to self-rescue if not injured. Extended time missing warrants investigation.',
      riskFactors: ['Solo hiker', 'Remote terrain', 'Limited supplies'],
      skills: ['Navigation', 'Wilderness Survival', 'First Aid'],
      recommendedAction: 'Send search team along planned route. Check emergency shelter locations.',
      weatherModifier: 0,
      timeModifier: 5,
      effectiveScore: 65
    }
  },
  {
    id: 'CASE-004',
    name: 'Lisa Park',
    age: 28,
    ageGroup: 'Adult',
    emergencyType: 'Vehicle Breakdown',
    description: 'Car broke down on rural highway. Has shelter in vehicle but low phone battery.',
    lastKnownAddress: 'Highway 42, Mile Marker 78',
    hoursMissing: 1,
    phone: '555-0789',
    priority: 'low',
    priorityScore: 35,
    status: 'active',
    reporterId: 'r3',
    createdAt: new Date(Date.now() - 1 * 3600000),
    aiAnalysis: {
      reasoning: 'Adult with vehicle shelter. Known location. Low immediate risk but assistance needed.',
      riskFactors: ['Low phone battery', 'Rural location'],
      skills: ['Roadside Assistance'],
      recommendedAction: 'Dispatch roadside assistance. Maintain phone contact.',
      weatherModifier: 0,
      timeModifier: 0,
      effectiveScore: 35
    }
  },
]

const demoTeams: Team[] = [
  {
    id: 'team-001',
    name: 'Alpha Response',
    caseId: 'CASE-001',
    members: ['v1', 'v2'],
    requiredRoles: ['K9 Handler', 'Drone Operator', 'First Aid'],
    type: 'Critical Response'
  }
]

const demoAILog: AILogEntry[] = [
  { id: 'log-1', timestamp: new Date(Date.now() - 300000), priority: 'critical', eventTitle: 'New Case Priority Assigned', detail: 'CASE-001 assigned CRITICAL priority due to young age and time factors.' },
  { id: 'log-2', timestamp: new Date(Date.now() - 600000), priority: 'high', eventTitle: 'Team Recommendation Generated', detail: 'Recommended Sarah Chen and Marcus Williams for CASE-001 based on skills match.' },
  { id: 'log-3', timestamp: new Date(Date.now() - 900000), priority: 'medium', eventTitle: 'Weather Risk Update', detail: 'Weather conditions remain clear. No modifier applied to active cases.' },
]

export const useAppStore = create<AppState>()(
  persist(
    (set) => ({
      // Initial state
      currentUser: null,
      isAuthenticated: false,
      theme: 'light',
      weatherCondition: 'clear',
      sidebarCollapsed: false,
      cases: demoCases,
      volunteers: demoVolunteers,
      teams: demoTeams,
      checkIns: [],
      aiLog: demoAILog,
      
      // Auth actions
      login: (user) => set({ currentUser: user, isAuthenticated: true }),
      logout: () => set({ currentUser: null, isAuthenticated: false }),
      
      // Settings actions
      setTheme: (theme) => set({ theme }),
      setWeatherCondition: (weatherCondition) => set({ weatherCondition }),
      toggleSidebar: () => set((state) => ({ sidebarCollapsed: !state.sidebarCollapsed })),
      
      // Case actions
      addCase: (caseData) => set((state) => ({
        cases: [...state.cases, { ...caseData, id: `CASE-${String(state.cases.length + 1).padStart(3, '0')}`, createdAt: new Date() }]
      })),
      updateCase: (id, updates) => set((state) => ({
        cases: state.cases.map(c => c.id === id ? { ...c, ...updates } : c)
      })),
      
      // Volunteer actions
      addVolunteer: (volunteer) => set((state) => ({
        volunteers: [...state.volunteers, volunteer]
      })),
      updateVolunteer: (id, updates) => set((state) => ({
        volunteers: state.volunteers.map(v => v.id === id ? { ...v, ...updates } : v)
      })),
      
      // Team actions
      createTeam: (team) => set((state) => ({
        teams: [...state.teams, { ...team, id: `team-${String(state.teams.length + 1).padStart(3, '0')}` }]
      })),
      updateTeam: (id, updates) => set((state) => ({
        teams: state.teams.map(t => t.id === id ? { ...t, ...updates } : t)
      })),
      
      // Check-in actions
      addCheckIn: (checkIn) => set((state) => ({
        checkIns: [...state.checkIns, { ...checkIn, id: `checkin-${Date.now()}`, timestamp: new Date() }]
      })),
      
      // AI Log actions
      addAILogEntry: (entry) => set((state) => ({
        aiLog: [{ ...entry, id: `log-${Date.now()}`, timestamp: new Date() }, ...state.aiLog]
      })),
      clearAILog: () => set({ aiLog: [] }),
    }),
    {
      name: 'rescueai-storage',
      partialize: (state) => ({ 
        theme: state.theme,
        weatherCondition: state.weatherCondition,
        sidebarCollapsed: state.sidebarCollapsed,
      }),
    }
  )
)
