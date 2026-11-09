import PageHeader from '../components/PageHeader'
import StatCard from '../components/StatCard'
import type { Exercise, Page } from '../types'

const COACH_SHORTCUTS = [
  'I only have 30 minutes',
  'Swap an exercise',
  'I feel sore today',
]

function Dashboard({
  setPage,
  openCoach,
  exercises,
}: {
  setPage: (page: Page) => void
  // Opens the AI Coach with this message typed in, ready to edit or send.
  openCoach: (draft: string) => void
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

          {COACH_SHORTCUTS.map((shortcut) => (
            <button
              key={shortcut}
              className="quick-button"
              onClick={() =>
                openCoach(shortcut)
              }
            >
              {shortcut}
            </button>
          ))}
        </div>
      </section>
    </>
  )
}

export default Dashboard