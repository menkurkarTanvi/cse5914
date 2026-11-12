import { useState } from 'react'
import './App.css'

import Sidebar from './components/Sidebar'

import Dashboard from './pages/Dashboard'
import Profile from './pages/Profile'
import WorkoutPlan from './pages/WorkoutPlan'
import AICoach from './pages/AICoach'
import Progress from './pages/Progress'
import Nutrition from './pages/Nutrition'
import Login from './pages/Login'
import SignUp from './pages/SignUp'

import { clearCoachChat } from './hooks/useCoachChat'

import type { Page } from './types'

function App() {
  const [token, setToken] = useState<string | null>(
    localStorage.getItem('token'),
  )

  const [page, setPage] = useState<Page>(
    localStorage.getItem('token')
      ? 'dashboard'
      : 'login',
  )

  const loggedIn = token !== null

  // A message to type into the AI Coach's text box when it opens, set by the
  // dashboard's shortcuts. Used once, then cleared.
  const [coachDraft, setCoachDraft] =
    useState('')

  function openCoach(draft: string) {
    setCoachDraft(draft)
    setPage('coach')
  }

  function handleLogin(token: string) {
    localStorage.setItem('token', token)
    clearCoachChat()
    setToken(token)
    setPage('dashboard')
  }

  function handleLogout() {
    localStorage.removeItem('token')
    clearCoachChat()
    setToken(null)
    setPage('login')
  }

  if (!loggedIn) {
    if (page === 'signup') {
      return (
        <SignUp setPage={setPage} />
      )
    }

    return (
      <Login
        setPage={setPage}
        onLogin={handleLogin}
      />
    )
  }

  return (
    <div className="app-shell">
      <Sidebar
        page={page}
        setPage={setPage}
        logout={handleLogout}
      />

      <main className="main-content">
        {page === 'dashboard' && (
          <Dashboard
            setPage={setPage}
            openCoach={openCoach}
          />
        )}

        {page === 'profile' && (
          <Profile setPage={setPage} />
        )}

        {page === 'plan' && (
          <WorkoutPlan setPage={setPage} />
        )}

        {page === 'coach' && (
          <AICoach
            draft={coachDraft}
            onDraftUsed={() => setCoachDraft('')}
          />
        )}

        {page === 'progress' && (
          <Progress />
        )}

        {page === 'nutrition' && (
          <Nutrition />
        )}
      </main>
    </div>
  )
}

export default App