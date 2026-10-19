import { useEffect, useState } from 'react'

import PageHeader from '../components/PageHeader'

import { mockAlternatives } from '../data/mockData'

import {
  fetchWorkoutPlan,
  type ApiWorkout,
  type ApiWorkoutExercise,
  type WorkoutPlanResponse,
} from '../api/workouts'

import type { LoggedSet, Page, WorkoutFeedback } from '../types'

type Props = {
  setPage: (page: Page) => void
}

// What the page needs for each exercise row.
type PlanExercise = {
  id: string // WorkoutPlanExercise id (sent when saving the workout)
  exerciseId: string // Exercise id (used to look up alternatives)
  name: string
  sets: string // e.g. "3 × 8–10"
  setCount: number
}

function toPlanExercise(item: ApiWorkoutExercise): PlanExercise {
  const reps =
    item.reps_min === item.reps_max
      ? `${item.reps_min}`
      : `${item.reps_min}–${item.reps_max}`

  return {
    id: item.id,
    exerciseId: item.exercise_id,
    name: item.name,
    sets: `${item.sets_planned} × ${reps}`,
    setCount: item.sets_planned,
  }
}

function dayLabel(workout: ApiWorkout) {
  const day = workout.day_of_week.slice(0, 3)
  return workout.description ? `${day} — ${workout.description}` : day
}

/* -------------------------------------------------------------------------- */
/*  One day's workout. Keyed by workout_id so its state resets on day change.  */
/* -------------------------------------------------------------------------- */

function WorkoutDay({ workout }: { workout: ApiWorkout }) {
  const [exercises, setExercises] = useState<PlanExercise[]>(() =>
    workout.exercises.map(toPlanExercise),
  )

  const [swapIndex, setSwapIndex] = useState<number | null>(null)
  const [showCompletion, setShowCompletion] = useState(false)
  const [feedback, setFeedback] = useState<WorkoutFeedback>('great')

  const [logs, setLogs] = useState<LoggedSet[][]>(() =>
    workout.exercises.map((item) =>
      Array.from({ length: item.sets_planned }, () => ({
        reps: '',
        weight: '',
      })),
    ),
  )

  function swapExercise(
    index: number,
    replacement: { id: string; name: string },
  ) {
    setExercises((current) =>
      current.map((exercise, i) =>
        i === index
          ? {
              ...exercise,
              exerciseId: replacement.id,
              name: replacement.name,
            }
          : exercise,
      ),
    )
  }

  function updateSet(
    exerciseIndex: number,
    setIndex: number,
    field: keyof LoggedSet,
    value: string,
  ) {
    setLogs((current) =>
      current.map((exerciseSets, i) =>
        i === exerciseIndex
          ? exerciseSets.map((set, j) =>
              j === setIndex ? { ...set, [field]: value } : set,
            )
          : exerciseSets,
      ),
    )
  }

  function skipWorkout() {
    const payload = {
      workout_id: workout.workout_id,
      reason: 'user_marked_incomplete',
    }

    console.log('Workout skip payload:', payload)
    alert('Incomplete workout is ready for backend integration.')
  }

  function submitWorkout() {
    const payload = {
      workout_id: workout.workout_id,

      exercises: exercises.map((exercise, exerciseIndex) => ({
        workout_plan_exercise_id: exercise.id,

        sets: logs[exerciseIndex].map((set, setIndex) => ({
          set_number: setIndex + 1,
          reps: Number(set.reps),
          weight: set.weight === '' ? null : Number(set.weight),
          weight_unit: 'lb',
        })),
      })),

      feedback: {
        difficulty: feedback,
      },
    }

    console.log('Workout completion payload:', payload)
    alert('Workout log is ready for backend integration.')

    setShowCompletion(false)
  }

  return (
    <div className="panel workout-detail">
      <h2>
        {workout.day_of_week}
        {workout.description ? ` — ${workout.description}` : ''}
      </h2>

      <p>
        Week {workout.week_number} • {workout.scheduled_date}
      </p>

      <div className="exercise-list large">
        {exercises.map((exercise, index) => {
          const alternatives = mockAlternatives[exercise.exerciseId] ?? []

          return (
            <div className="exercise-block" key={exercise.id}>
              <div className="exercise-row">
                <div>
                  <strong>{exercise.name}</strong>
                  <span>{exercise.sets}</span>
                </div>

                <button
                  className="text-button"
                  onClick={() =>
                    setSwapIndex(swapIndex === index ? null : index)
                  }
                >
                  {swapIndex === index ? 'Cancel' : 'Swap exercise'}
                </button>
              </div>

              {swapIndex === index && (
                <div className="swap-panel">
                  <h3>Alternative exercises</h3>

                  {alternatives.length === 0 ? (
                    <p>No alternatives available yet.</p>
                  ) : (
                    alternatives.map((alternative) => (
                      <div
                        className="alternative-row"
                        key={alternative.exerciseId}
                      >
                        <div>
                          <strong>{alternative.name}</strong>
                          <span>{alternative.reason}</span>
                          <small>
                            Equipment:{' '}
                            {alternative.equipmentRequired.join(', ')}
                          </small>
                        </div>

                        <button
                          className="light-button"
                          onClick={() => {
                            swapExercise(index, {
                              id: alternative.exerciseId,
                              name: alternative.name,
                            })
                            setSwapIndex(null)
                          }}
                        >
                          Use this
                        </button>
                      </div>
                    ))
                  )}
                </div>
              )}
            </div>
          )
        })}
      </div>

      {!showCompletion ? (
        <div className="page-actions inside workout-actions">
          <button className="light-button" onClick={skipWorkout}>
            Mark Incomplete
          </button>

          <button
            className="gold-button"
            onClick={() => setShowCompletion(true)}
          >
            Mark Workout Complete
          </button>
        </div>
      ) : (
        <div className="completion-panel">
          <div className="completion-heading">
            <div>
              <h3>Log completed workout</h3>
              <p>Enter the reps and weight you completed for each set.</p>
            </div>

            <button
              className="text-button"
              onClick={() => setShowCompletion(false)}
            >
              Cancel
            </button>
          </div>

          {exercises.map((exercise, exerciseIndex) => (
            <div className="exercise-log" key={`log-${exercise.id}`}>
              <strong>{exercise.name}</strong>

              <div className="set-log-header">
                <span>Set</span>
                <span>Reps</span>
                <span>Weight (lb)</span>
              </div>

              {logs[exerciseIndex].map((set, setIndex) => (
                <div className="set-log-row" key={setIndex}>
                  <span>{setIndex + 1}</span>

                  <input
                    type="number"
                    min="1"
                    value={set.reps}
                    onChange={(event) =>
                      updateSet(
                        exerciseIndex,
                        setIndex,
                        'reps',
                        event.target.value,
                      )
                    }
                    placeholder="10"
                  />

                  <input
                    type="number"
                    min="0"
                    step="2.5"
                    value={set.weight}
                    onChange={(event) =>
                      updateSet(
                        exerciseIndex,
                        setIndex,
                        'weight',
                        event.target.value,
                      )
                    }
                    placeholder="135"
                  />
                </div>
              ))}
            </div>
          ))}

          <div className="workout-feedback">
            <h3>How did the workout feel?</h3>

            <div className="feedback-options">
              {[
                ['great', 'Great'],
                ['too_easy', 'Too Easy'],
                ['too_hard', 'Too Hard'],
              ].map(([value, label]) => (
                <button
                  key={value}
                  className={`feedback-button ${
                    feedback === value ? 'selected' : ''
                  }`}
                  onClick={() => setFeedback(value as WorkoutFeedback)}
                >
                  {label}
                </button>
              ))}
            </div>
          </div>

          <div className="page-actions inside">
            <button className="gold-button" onClick={submitWorkout}>
              Submit Workout
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

/* -------------------------------------------------------------------------- */
/*  Page: loads the plan from GET /workouts/workoutPlan                        */
/* -------------------------------------------------------------------------- */

function WorkoutPlan({ setPage }: Props) {
  const [data, setData] = useState<WorkoutPlanResponse | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [selectedId, setSelectedId] = useState<string | null>(null)

  useEffect(() => {
    let cancelled = false

    fetchWorkoutPlan()
      .then((response) => {
        if (cancelled) return
        setData(response)
        setSelectedId(response.workouts[0]?.workout_id ?? null)
      })
      .catch((err: Error) => {
        if (!cancelled) setError(err.message)
      })
      .finally(() => {
        if (!cancelled) setLoading(false)
      })

    return () => {
      cancelled = true
    }
  }, [])

  const selected =
    data?.workouts.find((w) => w.workout_id === selectedId) ?? null

  let body: React.ReactNode

  if (loading) {
    body = (
      <section className="panel">
        <p>Loading your workout plan...</p>
      </section>
    )
  } else if (error) {
    body = (
      <section className="panel">
        <p>{error} Refresh the page to try again.</p>
      </section>
    )
  } else if (!data || !data.program || !selected) {
    body = (
      <section className="panel">
        <p>{data?.message ?? 'No workouts found.'}</p>
      </section>
    )
  } else {
    body = (
      <>
        <section className="panel plan-summary">
          <div>
            <h2>{data.workouts.length}-day plan</h2>

            <p>
              Goal: {data.program.goal}
              {data.session_info ? ` • ${data.session_info}` : ''}
            </p>
          </div>

          <button className="light-button" onClick={() => setPage('coach')}>
            Ask AI Coach
          </button>
        </section>

        <section className="plan-grid">
          <div className="panel week-panel">
            <h2>This week</h2>

            {data.workouts.map((workout) => (
              <button
                key={workout.workout_id}
                className={`day-button ${
                  workout.workout_id === selectedId ? 'active' : ''
                }`}
                onClick={() => setSelectedId(workout.workout_id)}
              >
                {dayLabel(workout)}
              </button>
            ))}
          </div>

          <WorkoutDay key={selected.workout_id} workout={selected} />
        </section>
      </>
    )
  }

  return (
    <>
      <PageHeader
        title="Workout Plan"
        subtitle="Personalized from your profile and updated with your feedback."
      />

      {body}
    </>
  )
}

export default WorkoutPlan
