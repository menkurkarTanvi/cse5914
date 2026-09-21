import { useState } from 'react'
import './App.css'

type Page =
  | 'dashboard'
  | 'plan'
  | 'progress'
  | 'coach'
  | 'nutrition'
  | 'profile'

type Exercise = {
  name: string
  sets: string
}

const navItems: { id: Page; label: string }[] = [
  { id: 'dashboard', label: 'Dashboard' },
  { id: 'plan', label: 'My Plan' },
  { id: 'progress', label: 'Progress' },
  { id: 'coach', label: 'AI Coach' },
  { id: 'nutrition', label: 'Nutrition' },
  { id: 'profile', label: 'Profile' },
]

const initialExercises: Exercise[] = [
  { name: 'Barbell Bench Press', sets: '3 × 8–10' },
  { name: 'Incline Dumbbell Press', sets: '3 × 8–10' },
  { name: 'Shoulder Press', sets: '3 × 10' },
  { name: 'Lateral Raises', sets: '3 × 12–15' },
]

function App() {
  const [page, setPage] = useState<Page>('dashboard')

  const [exercises, setExercises] =
    useState<Exercise[]>(initialExercises)

  const [message, setMessage] = useState('')

  const [chatReply, setChatReply] = useState(
    'Try dumbbell bench press as the closest substitute. Keep the same 3 sets and use 8–12 reps with a controlled tempo.',
  )

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

  return (
    <div className="app-shell">
      <aside className="sidebar">
        <div className="brand">
          <div className="brand-name">FitStack</div>
          <div className="brand-tagline">AI Fitness Coach</div>
        </div>

        <nav className="nav-list">
          {navItems.map((item) => (
            <button
              key={item.id}
              className={`nav-button ${
                page === item.id ? 'active' : ''
              }`}
              onClick={() => setPage(item.id)}
            >
              {item.label}
            </button>
          ))}
        </nav>
      </aside>

      <main className="main-content">
        {page === 'dashboard' && (
          <Dashboard
            setPage={setPage}
            exercises={exercises}
          />
        )}

        {page === 'profile' && (
          <ProfileSetup setPage={setPage} />
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

        {page === 'progress' && <Progress />}

        {page === 'nutrition' && <Nutrition />}
      </main>
    </div>
  )
}

function PageHeader({
  title,
  subtitle,
}: {
  title: string
  subtitle: string
}) {
  return (
    <header className="page-header">
      <h1>{title}</h1>
      <p>{subtitle}</p>
    </header>
  )
}

function Dashboard({
  setPage,
  exercises,
}: {
  setPage: (page: Page) => void
  exercises: Exercise[]
}) {
  return (
    <>
      <PageHeader
        title="Dashboard"
        subtitle="Your daily plan, nutrition targets, and AI coaching in one place."
      />

      <section className="stats-grid">
        <StatCard
          label="Calorie target"
          value="2,650 kcal"
        />

        <StatCard
          label="Protein"
          value="165 g"
        />

        <StatCard
          label="Current streak"
          value="5 days"
        />

        <StatCard
          label="Weight"
          value="154 lb"
        />
      </section>

      <section className="dashboard-grid">
        <div className="panel workout-panel">
          <h2>Today — Push Day</h2>

          <p>
            60 min • Chest, shoulders, triceps
          </p>

          <div className="exercise-list">
            {exercises.map((exercise) => (
              <div
                className="exercise-row"
                key={exercise.name}
              >
                <div>
                  <strong>
                    {exercise.name}
                  </strong>

                  <span>
                    {exercise.sets}
                  </span>
                </div>

                <button
                  className="text-button"
                  onClick={() =>
                    setPage('plan')
                  }
                >
                  View
                </button>
              </div>
            ))}
          </div>
        </div>

        <div className="panel coach-card">
          <h2>AI Coach</h2>

          <p>
            Adapt your workout if your
            schedule, equipment, or energy
            changes.
          </p>

          <button
            className="gold-button full"
            onClick={() =>
              setPage('coach')
            }
          >
            Ask AI Coach
          </button>

          <button
            className="quick-button"
            onClick={() =>
              setPage('coach')
            }
          >
            I only have 30 minutes
          </button>

          <button
            className="quick-button"
            onClick={() =>
              setPage('coach')
            }
          >
            Swap an exercise
          </button>

          <button
            className="quick-button"
            onClick={() =>
              setPage('coach')
            }
          >
            I feel sore today
          </button>
        </div>
      </section>
    </>
  )
}

function StatCard({
  label,
  value,
}: {
  label: string
  value: string
}) {
  return (
    <div className="stat-card">
      <span>{label}</span>
      <strong>{value}</strong>
    </div>
  )
}

function ProfileSetup({
  setPage,
}: {
  setPage: (page: Page) => void
}) {
  const [goal, setGoal] =
    useState('Build muscle')

  const [experience, setExperience] =
    useState('Intermediate')

  const [equipment, setEquipment] =
    useState('Full gym')

  return (
    <>
      <PageHeader
        title="Profile Setup"
        subtitle="Tell FitStack about your goals, schedule, and available equipment."
      />

      <section className="profile-grid">
        <div className="panel form-panel">
          <h2>Personal information</h2>

          <div className="form-grid">
            <label>
              Age
              <input defaultValue="26" />
            </label>

            <label>
              Weight
              <input defaultValue="154" />
            </label>

            <label>
              Primary goal

              <select
                value={goal}
                onChange={(event) =>
                  setGoal(event.target.value)
                }
              >
                <option>
                  Build muscle
                </option>

                <option>
                  Strength
                </option>

                <option>
                  Fat loss
                </option>

                <option>
                  Endurance
                </option>
              </select>
            </label>

            <label>
              Experience level

              <select
                value={experience}
                onChange={(event) =>
                  setExperience(
                    event.target.value,
                  )
                }
              >
                <option>
                  Beginner
                </option>

                <option>
                  Intermediate
                </option>

                <option>
                  Advanced
                </option>
              </select>
            </label>

            <label>
              Activity level

              <select defaultValue="Moderately active">
                <option>
                  Lightly active
                </option>

                <option>
                  Moderately active
                </option>

                <option>
                  Very active
                </option>
              </select>
            </label>

            <label>
              Limitations / injuries

              <input placeholder="None" />
            </label>
          </div>
        </div>

        <div className="panel form-panel">
          <h2>Training preferences</h2>

          <div className="form-grid one-column">
            <label>
              Workout days per week

              <select defaultValue="4 days">
                <option>3 days</option>
                <option>4 days</option>
                <option>5 days</option>
                <option>6 days</option>
              </select>
            </label>

            <label>
              Typical session length

              <select defaultValue="60 minutes">
                <option>
                  30 minutes
                </option>

                <option>
                  45 minutes
                </option>

                <option>
                  60 minutes
                </option>

                <option>
                  90 minutes
                </option>
              </select>
            </label>

            <label>
              Available equipment

              <select
                value={equipment}
                onChange={(event) =>
                  setEquipment(
                    event.target.value,
                  )
                }
              >
                <option>
                  Full gym
                </option>

                <option>
                  Dumbbells only
                </option>

                <option>
                  Bodyweight
                </option>

                <option>
                  Travel / limited
                </option>
              </select>
            </label>

            <label>
              Preferred training style

              <select defaultValue="Hypertrophy / strength">
                <option>
                  Hypertrophy / strength
                </option>

                <option>
                  General fitness
                </option>

                <option>
                  Endurance
                </option>
              </select>
            </label>
          </div>
        </div>
      </section>

      <div className="page-actions">
        <button
          className="gold-button"
          onClick={() =>
            setPage('plan')
          }
        >
          Generate My Plan
        </button>
      </div>
    </>
  )
}

function WorkoutPlan({
  exercises,
  swapExercise,
  setPage,
}: {
  exercises: Exercise[]
  swapExercise: (index: number) => void
  setPage: (page: Page) => void
}) {
  return (
    <>
      <PageHeader
        title="Workout Plan"
        subtitle="Personalized from your profile and updated with your feedback."
      />

      <section className="panel plan-summary">
        <div>
          <h2>
            4-day hypertrophy plan
          </h2>

          <p>
            Goal: Build muscle •
            60 min/session • Full gym
          </p>
        </div>

        <button
          className="light-button"
          onClick={() =>
            setPage('coach')
          }
        >
          Ask AI Coach
        </button>
      </section>

      <section className="plan-grid">
        <div className="panel week-panel">
          <h2>This week</h2>

          <button className="day-button active">
            Mon — Push
          </button>

          <button className="day-button">
            Tue — Pull
          </button>

          <button className="day-button">
            Thu — Legs
          </button>

          <button className="day-button">
            Sat — Upper
          </button>
        </div>

        <div className="panel workout-detail">
          <h2>Monday — Push</h2>

          <p>
            Chest, shoulders, triceps
          </p>

          <div className="exercise-list large">
            {exercises.map(
              (exercise, index) => (
                <div
                  className="exercise-row"
                  key={`${exercise.name}-${index}`}
                >
                  <div>
                    <strong>
                      {exercise.name}
                    </strong>

                    <span>
                      {exercise.sets}
                    </span>
                  </div>

                  <button
                    className="text-button"
                    onClick={() =>
                      swapExercise(index)
                    }
                  >
                    Swap exercise
                  </button>
                </div>
              ),
            )}
          </div>

          <div className="page-actions inside">
            <button className="gold-button">
              Mark Workout Complete
            </button>
          </div>
        </div>
      </section>
    </>
  )
}

function AICoach({
  exercises,
  message,
  setMessage,
  chatReply,
  sendMessage,
}: {
  exercises: Exercise[]
  message: string
  setMessage: (message: string) => void
  chatReply: string
  sendMessage: () => void
}) {
  return (
    <>
      <PageHeader
        title="AI Coach"
        subtitle="Ask questions, swap exercises, and adapt your plan."
      />

      <section className="coach-grid">
        <div className="panel coach-context">
          <h2>Current workout</h2>

          <p className="gold-text">
            Monday — Push
          </p>

          <div className="compact-list">
            {exercises.map((exercise) => (
              <span key={exercise.name}>
                {exercise.name}
              </span>
            ))}
          </div>

          <h3>Quick actions</h3>

          <button
            className="outline-button"
            onClick={() =>
              setMessage(
                'Swap an exercise',
              )
            }
          >
            Swap an exercise
          </button>

          <button
            className="quick-button"
            onClick={() =>
              setMessage(
                'Shorten my workout',
              )
            }
          >
            Shorten workout
          </button>

          <button
            className="quick-button"
            onClick={() =>
              setMessage(
                'Adjust difficulty',
              )
            }
          >
            Adjust difficulty
          </button>
        </div>

        <div className="panel chat-panel">
          <div className="chat-history">
            <div className="user-message">
              I don't have a barbell today.
              What can I do instead?
            </div>

            <div className="ai-message">
              <strong>
                Try dumbbell bench press as
                the closest substitute.
              </strong>

              <span>
                Keep the same 3 sets and use
                8–12 reps with a controlled
                tempo.
              </span>
            </div>

            {chatReply && (
              <div className="ai-message secondary">
                {chatReply}
              </div>
            )}
          </div>

          <div className="chat-input-row">
            <input
              value={message}
              onChange={(event) =>
                setMessage(
                  event.target.value,
                )
              }
              onKeyDown={(event) => {
                if (event.key === 'Enter') {
                  sendMessage()
                }
              }}
              placeholder="Ask FitStack anything about your plan..."
            />

            <button
              className="gold-button"
              onClick={sendMessage}
            >
              Send
            </button>
          </div>
        </div>
      </section>
    </>
  )
}

function Progress() {
  const [feedback, setFeedback] =
    useState('Great')

  return (
    <>
      <PageHeader
        title="Progress & Insights"
        subtitle="Track your results and help the AI refine future plans."
      />

      <section className="stats-grid">
        <StatCard
          label="Workouts"
          value="12"
        />

        <StatCard
          label="Avg calories"
          value="2,450"
        />

        <StatCard
          label="Strength trend"
          value="+6.8%"
        />

        <StatCard
          label="Body weight"
          value="154 lb"
        />
      </section>

      <section className="progress-grid">
        <div className="panel chart-card">
          <h2>Weight Trend</h2>

          <p>Last 6 weeks</p>

          <div className="fake-chart">
            <div className="grid-line line-1" />
            <div className="grid-line line-2" />
            <div className="grid-line line-3" />

            <svg
              viewBox="0 0 600 220"
              preserveAspectRatio="none"
            >
              <polyline
                points="30,45 130,80 230,105 330,135 430,150 560,175"
                fill="none"
                stroke="currentColor"
                strokeWidth="6"
                strokeLinecap="round"
                strokeLinejoin="round"
              />

              <circle
                cx="30"
                cy="45"
                r="7"
                fill="currentColor"
              />

              <circle
                cx="130"
                cy="80"
                r="7"
                fill="currentColor"
              />

              <circle
                cx="230"
                cy="105"
                r="7"
                fill="currentColor"
              />

              <circle
                cx="330"
                cy="135"
                r="7"
                fill="currentColor"
              />

              <circle
                cx="430"
                cy="150"
                r="7"
                fill="currentColor"
              />

              <circle
                cx="560"
                cy="175"
                r="7"
                fill="currentColor"
              />
            </svg>
          </div>

          <p className="insight">
            AI insight: weight is trending
            gradually while workout
            consistency is improving.
          </p>
        </div>

        <div className="panel feedback-card">
          <h2>Workout Feedback</h2>

          <p>
            How did today's workout feel?
          </p>

          {[
            'Great',
            'Too easy',
            'Too hard',
            'Too long',
          ].map((option) => (
            <button
              key={option}
              className={`feedback-button ${
                feedback === option
                  ? 'selected'
                  : ''
              }`}
              onClick={() =>
                setFeedback(option)
              }
            >
              {option}
            </button>
          ))}

          <small>
            FitStack can use your feedback
            to adjust exercise selection,
            volume, and future workouts.
          </small>
        </div>
      </section>
    </>
  )
}

function Nutrition() {
  return (
    <>
      <PageHeader
        title="Nutrition"
        subtitle="Simple daily targets that support your current fitness goal."
      />

      <section className="stats-grid">
        <StatCard
          label="Calories"
          value="2,650 kcal"
        />

        <StatCard
          label="Protein"
          value="165 g"
        />

        <StatCard
          label="Carbs"
          value="320 g"
        />

        <StatCard
          label="Fat"
          value="75 g"
        />
      </section>

      <section className="panel nutrition-panel">
        <h2>Today's targets</h2>

        <p>
          This is placeholder UI for Week 1.
          Later, these values can come from
          the backend based on the user's
          profile and goal.
        </p>
      </section>
    </>
  )
}

export default App