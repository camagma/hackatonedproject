'use client'

import { useState } from 'react'
import { useRouter } from 'next/navigation'
import { cn } from "@/lib/utils"
import { useAppStore, type UserRole } from "@/lib/store"
import { Button } from "@/components/ui/button"
import { Input } from "@/components/ui/input"
import { Label } from "@/components/ui/label"

const skillOptions = [
  'Medical',
  'K9 Handler',
  'Drone Operator',
  'First Aid',
  'Navigation',
  'Communications',
  'Wilderness Survival',
  'Climbing',
  'Water Rescue',
  'Roadside Assistance',
]

const demoAccounts = [
  { username: 'sarah_sar', password: 'demo123', role: 'volunteer' },
  { username: 'marcus_w', password: 'demo123', role: 'volunteer' },
  { username: 'reporter1', password: 'demo123', role: 'reporter' },
]

export default function LoginPage() {
  const router = useRouter()
  const { login, volunteers } = useAppStore()
  
  const [activeTab, setActiveTab] = useState<'signin' | 'create'>('signin')
  
  // Sign In state
  const [signInUsername, setSignInUsername] = useState('')
  const [signInPassword, setSignInPassword] = useState('')
  const [signInError, setSignInError] = useState('')
  
  // Create Account state
  const [createName, setCreateName] = useState('')
  const [createUsername, setCreateUsername] = useState('')
  const [createPassword, setCreatePassword] = useState('')
  const [createPasswordConfirm, setCreatePasswordConfirm] = useState('')
  const [createRole, setCreateRole] = useState<UserRole>('reporter')
  const [createSkill, setCreateSkill] = useState('')
  const [createAddress, setCreateAddress] = useState('')
  const [createError, setCreateError] = useState('')

  const handleSignIn = (e: React.FormEvent) => {
    e.preventDefault()
    setSignInError('')
    
    // Check demo accounts
    const demoAccount = demoAccounts.find(
      a => a.username === signInUsername && a.password === signInPassword
    )
    
    if (demoAccount) {
      if (demoAccount.role === 'volunteer') {
        const volunteer = volunteers.find(v => v.username === signInUsername)
        if (volunteer) {
          login(volunteer)
          router.push('/dashboard')
          return
        }
      } else {
        login({
          id: 'r1',
          name: 'John Reporter',
          username: signInUsername,
          role: 'reporter',
        })
        router.push('/dashboard')
        return
      }
    }
    
    setSignInError('Invalid username or password')
  }

  const handleCreateAccount = (e: React.FormEvent) => {
    e.preventDefault()
    setCreateError('')
    
    if (createPassword !== createPasswordConfirm) {
      setCreateError('Passwords do not match')
      return
    }
    
    if (createPassword.length < 6) {
      setCreateError('Password must be at least 6 characters')
      return
    }
    
    if (createRole === 'volunteer' && !createSkill) {
      setCreateError('Please select a skill')
      return
    }
    
    if (createRole === 'volunteer' && !createAddress) {
      setCreateError('Please enter your address')
      return
    }
    
    const newUser = {
      id: `u-${Date.now()}`,
      name: createName,
      username: createUsername,
      role: createRole,
      skills: createRole === 'volunteer' ? [createSkill] : undefined,
      address: createRole === 'volunteer' ? createAddress : undefined,
      status: createRole === 'volunteer' ? 'active' as const : undefined,
      lastPing: createRole === 'volunteer' ? new Date() : undefined,
    }
    
    login(newUser)
    router.push('/dashboard')
  }

  return (
    <div className="min-h-screen bg-background flex items-center justify-center p-4">
      <div className="w-full max-w-md">
        {/* Logo */}
        <div className="text-center mb-8">
          <div className="flex items-center justify-center gap-1 mb-2">
            <span className="text-4xl font-sans font-extrabold text-foreground">Rescue</span>
            <span className="text-4xl font-sans font-extrabold text-primary">AI</span>
          </div>
          <p className="text-sm font-mono text-muted-foreground">Emergency Coordination Platform</p>
        </div>

        {/* Card */}
        <div className="bg-card rounded-[20px] border border-border p-6">
          {/* Tabs */}
          <div className="flex items-center bg-muted rounded-lg p-1 mb-6">
            <button
              onClick={() => setActiveTab('signin')}
              className={cn(
                "flex-1 py-2 px-4 rounded-md text-sm font-sans font-semibold transition-colors",
                activeTab === 'signin' 
                  ? "bg-card text-foreground shadow-sm" 
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              Sign In
            </button>
            <button
              onClick={() => setActiveTab('create')}
              className={cn(
                "flex-1 py-2 px-4 rounded-md text-sm font-sans font-semibold transition-colors",
                activeTab === 'create' 
                  ? "bg-card text-foreground shadow-sm" 
                  : "text-muted-foreground hover:text-foreground"
              )}
            >
              Create Account
            </button>
          </div>

          {/* Sign In Form */}
          {activeTab === 'signin' && (
            <form onSubmit={handleSignIn} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="username" className="text-xs font-mono uppercase tracking-wide">
                  Username
                </Label>
                <Input
                  id="username"
                  type="text"
                  value={signInUsername}
                  onChange={(e) => setSignInUsername(e.target.value)}
                  placeholder="Enter your username"
                  className="h-11 rounded-[14px] font-mono placeholder:text-muted-foreground focus:ring-2 focus:ring-primary"
                  required
                />
              </div>
              
              <div className="space-y-2">
                <Label htmlFor="password" className="text-xs font-mono uppercase tracking-wide">
                  Password
                </Label>
                <Input
                  id="password"
                  type="password"
                  value={signInPassword}
                  onChange={(e) => setSignInPassword(e.target.value)}
                  placeholder="Enter your password"
                  className="h-11 rounded-[14px] font-mono placeholder:text-muted-foreground focus:ring-2 focus:ring-primary"
                  required
                />
              </div>

              {signInError && (
                <p className="text-sm text-destructive font-mono">{signInError}</p>
              )}

              <Button type="submit" className="w-full h-11 rounded-[14px] font-sans font-bold">
                Sign In
              </Button>

              {/* Demo Accounts Hint */}
              <div className="mt-6 p-4 rounded-lg bg-muted border border-border">
                <p className="text-[10px] font-mono text-muted-foreground uppercase tracking-wide mb-2">
                  Demo Accounts
                </p>
                <div className="space-y-1.5 font-mono text-xs">
                  {demoAccounts.map((account, i) => (
                    <div key={i} className="flex items-center justify-between text-muted-foreground">
                      <span>{account.username}</span>
                      <span className="text-foreground">{account.password}</span>
                      <span className="text-[10px] uppercase">{account.role}</span>
                    </div>
                  ))}
                </div>
              </div>
            </form>
          )}

          {/* Create Account Form */}
          {activeTab === 'create' && (
            <form onSubmit={handleCreateAccount} className="space-y-4">
              <div className="space-y-2">
                <Label htmlFor="create-name" className="text-xs font-mono uppercase tracking-wide">
                  Full Name
                </Label>
                <Input
                  id="create-name"
                  type="text"
                  value={createName}
                  onChange={(e) => setCreateName(e.target.value)}
                  placeholder="Enter your full name"
                  className="h-11 rounded-[14px] font-mono placeholder:text-muted-foreground focus:ring-2 focus:ring-primary"
                  required
                />
              </div>

              <div className="space-y-2">
                <Label htmlFor="create-username" className="text-xs font-mono uppercase tracking-wide">
                  Username
                </Label>
                <Input
                  id="create-username"
                  type="text"
                  value={createUsername}
                  onChange={(e) => setCreateUsername(e.target.value)}
                  placeholder="Choose a username"
                  className="h-11 rounded-[14px] font-mono placeholder:text-muted-foreground focus:ring-2 focus:ring-primary"
                  required
                />
              </div>

              <div className="grid grid-cols-2 gap-4">
                <div className="space-y-2">
                  <Label htmlFor="create-password" className="text-xs font-mono uppercase tracking-wide">
                    Password
                  </Label>
                  <Input
                    id="create-password"
                    type="password"
                    value={createPassword}
                    onChange={(e) => setCreatePassword(e.target.value)}
                    placeholder="Create password"
                    className="h-11 rounded-[14px] font-mono placeholder:text-muted-foreground focus:ring-2 focus:ring-primary"
                    required
                  />
                </div>
                <div className="space-y-2">
                  <Label htmlFor="create-password-confirm" className="text-xs font-mono uppercase tracking-wide">
                    Confirm
                  </Label>
                  <Input
                    id="create-password-confirm"
                    type="password"
                    value={createPasswordConfirm}
                    onChange={(e) => setCreatePasswordConfirm(e.target.value)}
                    placeholder="Confirm password"
                    className="h-11 rounded-[14px] font-mono placeholder:text-muted-foreground focus:ring-2 focus:ring-primary"
                    required
                  />
                </div>
              </div>

              <div className="space-y-2">
                <Label className="text-xs font-mono uppercase tracking-wide">
                  Role
                </Label>
                <div className="flex items-center bg-muted rounded-lg p-1">
                  <button
                    type="button"
                    onClick={() => setCreateRole('reporter')}
                    className={cn(
                      "flex-1 py-2 px-4 rounded-md text-sm font-sans font-semibold transition-colors",
                      createRole === 'reporter' 
                        ? "bg-card text-foreground shadow-sm" 
                        : "text-muted-foreground hover:text-foreground"
                    )}
                  >
                    Reporter
                  </button>
                  <button
                    type="button"
                    onClick={() => setCreateRole('volunteer')}
                    className={cn(
                      "flex-1 py-2 px-4 rounded-md text-sm font-sans font-semibold transition-colors",
                      createRole === 'volunteer' 
                        ? "bg-card text-foreground shadow-sm" 
                        : "text-muted-foreground hover:text-foreground"
                    )}
                  >
                    Volunteer
                  </button>
                </div>
              </div>

              {/* Volunteer-specific fields */}
              {createRole === 'volunteer' && (
                <>
                  <div className="space-y-2">
                    <Label htmlFor="create-skill" className="text-xs font-mono uppercase tracking-wide">
                      Primary Skill
                    </Label>
                    <select
                      id="create-skill"
                      value={createSkill}
                      onChange={(e) => setCreateSkill(e.target.value)}
                      className="w-full h-11 px-3 rounded-[14px] border border-input bg-background text-sm font-mono focus:outline-none focus:ring-2 focus:ring-primary"
                      required
                    >
                      <option value="">Select a skill</option>
                      {skillOptions.map((skill) => (
                        <option key={skill} value={skill}>{skill}</option>
                      ))}
                    </select>
                  </div>

                  <div className="space-y-2">
                    <Label htmlFor="create-address" className="text-xs font-mono uppercase tracking-wide">
                      Address
                    </Label>
                    <Input
                      id="create-address"
                      type="text"
                      value={createAddress}
                      onChange={(e) => setCreateAddress(e.target.value)}
                      placeholder="Enter your address"
                      className="h-11 rounded-[14px] font-mono placeholder:text-muted-foreground focus:ring-2 focus:ring-primary"
                      required
                    />
                    <p className="text-[10px] font-mono text-muted-foreground">
                      Used for proximity-based case assignment
                    </p>
                  </div>
                </>
              )}

              {createError && (
                <p className="text-sm text-destructive font-mono">{createError}</p>
              )}

              <Button type="submit" className="w-full h-11 rounded-[14px] font-sans font-bold">
                Create Account
              </Button>
            </form>
          )}
        </div>
      </div>
    </div>
  )
}
