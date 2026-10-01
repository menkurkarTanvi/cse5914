import PageHeader from '../components/PageHeader'
import type { Exercise, Page } from '../types'

type Props = {
  exercises: Exercise[]
  swapExercise: (index: number) => void
  setPage: (page: Page) => void
}

function WorkoutPlan({
  exercises,
  swapExercise,
  setPage,
}: Props) {
  return (
    <>
      <PageHeader
        title="Workout Plan"
        subtitle="Personalized from your profile and updated with your feedback."
      />

      <section className="panel plan-summary">
        <div>
          <h2>4-day hypertrophy plan</h2>
          <p>
            Goal: Build muscle • 60 min/session • Full gym
          </p>
        </div>

        <button
          className="light-button"
          onClick={() => setPage('coach')}
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
          <p>Chest, shoulders, triceps</p>

          <div className="exercise-list large">
            {exercises.map((exercise, index) => (
              <div
                className="exercise-row"
                key={`${exercise.name}-${index}`}
              >
                <div>
                  <strong>{exercise.name}</strong>
                  <span>{exercise.sets}</span>
                </div>

                <button
                  className="text-button"
                  onClick={() => swapExercise(index)}
                >
                  Swap exercise
                </button>
              </div>
            ))}
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

export default WorkoutPlan