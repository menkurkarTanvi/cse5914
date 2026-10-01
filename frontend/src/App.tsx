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

import { initialExercises } from './data/mockData'

import type {
  Exercise,
  Page,
} from './types'

function App() {
  const [page, setPage] =
    useState<Page>('login')

  const [token, setToken] = useState<string | null>(
    localStorage.getItem('token'),
  )

  const loggedIn = token !== null

  const [exercises, setExercises] =
    useState<Exercise[]>(initialExercises)

  const [message, setMessage] =
    useState('')

  const [chatReply, setChatReply] =
    useState(
      'Try dumbbell bench press as the closest substitute. Keep the same 3 sets and use 8–12 reps with a controlled tempo.',
    )

  function handleLogin(token: string) {
    localStorage.setItem('token', token)
    setToken(token)
    setPage('dashboard')
  }

  function handleLogout() {
    localStorage.removeItem('token')
    setToken(null)
    setPage('login')
  }

  function swapExercise(index: number) {
    const replacements = [
      'Dumbbell Bench Press',
      'Machine Chest Press',
      'Arnold Press',
      'Cable Lateral Raise',
    ]

    setExercises((current) =>
      current.map((exercise, i) =>
        i === index
          ? {
              ...exercise,
              name: replacements[index],
            }
          : exercise,
      ),
    )
  }

  function sendMessage() {
    if (!message.trim()) {
      return
    }

    setChatReply(
      `For "${message.trim()}", FitStack would send your profile and current workout to the backend AI service and return a personalized recommendation here.`,
    )

    setMessage('')
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
            exercises={exercises}
          />
        )}

        {page === 'profile' && (
          <Profile setPage={setPage} />
        )}

        {page === 'plan' && (
          <WorkoutPlan
            exercises={exercises}
            swapExercise={swapExercise}
            setPage={setPage}
          />
        )}

        {page === 'coach' && (
          <AICoach
            exercises={exercises}
            message={message}
            setMessage={setMessage}
            chatReply={chatReply}
            sendMessage={sendMessage}
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