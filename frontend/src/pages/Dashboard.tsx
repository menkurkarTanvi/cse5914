import { useEffect, useState } from 'react'

import PageHeader from '../components/PageHeader'
import StatCard from '../components/StatCard'

import {
  fetchWorkoutPlan,
  type ApiWorkout,
  type ApiWorkoutExercise,
  type WorkoutPlanResponse,
} from '../api/workouts'

import type { Page } from '../types'

type Props = {
  setPage: (page: Page) => void
  // Opens the AI Coach with this message typed in, ready to edit or send.
  openCoach: (draft: string) => void
}

function formatLabel(
  value: string | null | undefined,
) {
  if (!value) {
    return 'Not available'
  }

  return value
    .replaceAll('_', ' ')
    .replace(/\b\w/g, (letter) =>
      letter.toUpperCase(),
    )
}

function formatWorkoutDate(
  value: string,
) {
  const date = new Date(
    `${value}T00:00:00`,
  )

  return date.toLocaleDateString(
    undefined,
    {
      weekday: 'short',
      month: 'short',
      day: 'numeric',
    },
  )
}

function getLocalDateString() {
  const today = new Date()

  const year = today.getFullYear()

  const month = String(
    today.getMonth() + 1,
  ).padStart(2, '0')

  const day = String(
    today.getDate(),
  ).padStart(2, '0')

  return `${year}-${month}-${day}`
}

function chooseDashboardWorkout(
  workouts: ApiWorkout[],
) {
  if (workouts.length === 0) {
    return null
  }

  const today = getLocalDateString()

  const todaysWorkout =
    workouts.find(
      (workout) =>
        workout.scheduled_date === today,
    )

  if (todaysWorkout) {
    return todaysWorkout
  }

  return (
    workouts.find(
      (workout) =>
        workout.status !== 'completed',
    ) ?? workouts[0]
  )
}

function exerciseSets(
  exercise: ApiWorkoutExercise,
) {
  const reps =
    exercise.reps_min ===
    exercise.reps_max
      ? `${exercise.reps_min}`
      : `${exercise.reps_min}–${exercise.reps_max}`

  return `${exercise.sets_planned} × ${reps}`
}

const COACH_SHORTCUTS = [
  'I only have 30 minutes',
  'Swap an exercise',
  'I feel sore today',
]

function Dashboard({
  setPage,
  openCoach,
}: Props) {
  const [plan, setPlan] =
    useState<WorkoutPlanResponse | null>(
      null,
    )

  const [loading, setLoading] =
    useState(true)

  const [error, setError] =
    useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    async function loadDashboard() {
      try {
        const response =
          await fetchWorkoutPlan()

        if (!cancelled) {
          setPlan(response)
          setError(null)
        }
      } catch (loadError) {
        if (!cancelled) {
          setError(
            loadError instanceof Error
              ? loadError.message
              : 'Could not load dashboard data.',
          )
        }
      } finally {
        if (!cancelled) {
          setLoading(false)
        }
      }
    }

    loadDashboard()

    return () => {
      cancelled = true
    }
  }, [])

  const workouts =
    plan?.workouts ?? []

  const completedWorkouts =
    workouts.filter(
      (workout) =>
        workout.status === 'completed',
    ).length

  const dashboardWorkout =
    chooseDashboardWorkout(workouts)

  const isToday =
    dashboardWorkout?.scheduled_date ===
    getLocalDateString()

  return (
    <>
      <PageHeader
        title="Dashboard"
        subtitle="Your current program and upcoming workout in one place."
      />

      <section className="stats-grid">
        <StatCard
          label="Current goal"
          value={
            loading
              ? '...'
              : formatLabel(
                  plan?.program?.goal,
                )
          }
        />

        <StatCard
          label="Workouts this week"
          value={
            loading
              ? '...'
              : `${workouts.length}`
          }
        />

        <StatCard
          label="Completed workouts"
          value={
            loading
              ? '...'
              : `${completedWorkouts}`
          }
        />

        <StatCard
          label="Program status"
          value={
            loading
              ? '...'
              : formatLabel(
                  plan?.program?.status,
                )
          }
        />
      </section>

      {error && (
        <p className="auth-error">
          {error}
        </p>
      )}

      <section className="dashboard-grid">
        <div className="panel workout-panel">
          {loading && (
            <p>
              Loading workout data...
            </p>
          )}

          {!loading &&
            !error &&
            !dashboardWorkout && (
              <>
                <h2>
                  No workout available
                </h2>

                <p>
                  {plan?.message ??
                    'No workouts found for this week.'}
                </p>

                <button
                  className="gold-button"
                  onClick={() =>
                    setPage('plan')
                  }
                >
                  View My Plan
                </button>
              </>
            )}

          {!loading &&
            dashboardWorkout && (
              <>
                <h2>
                  {isToday
                    ? 'Today'
                    : 'Next Workout'}
                  {' — '}
                  {dashboardWorkout
                    .description ??
                    dashboardWorkout
                      .day_of_week}
                </h2>

                <p>
                  {formatWorkoutDate(
                    dashboardWorkout
                      .scheduled_date,
                  )}
                  {' • Week '}
                  {
                    dashboardWorkout
                      .week_number
                  }
                  {' • '}
                  {formatLabel(
                    dashboardWorkout
                      .status,
                  )}
                </p>

                <div className="exercise-list">
                  {dashboardWorkout.exercises.map(
                    (exercise) => (
                      <div
                        className="exercise-row"
                        key={exercise.id}
                      >
                        <div>
                          <strong>
                            {exercise.name}
                          </strong>

                          <span>
                            {exerciseSets(
                              exercise,
                            )}
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
                    ),
                  )}
                </div>

                {dashboardWorkout
                  .exercises.length ===
                  0 && (
                  <p>
                    No exercises have
                    been added to this
                    workout yet.
                  </p>
                )}
              </>
            )}
        </div>

        <div className="panel coach-card">
          <h2>AI Coach</h2>

          <p>
            Adapt your workout if your
            schedule, equipment, or
            energy changes.
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