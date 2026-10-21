import { useEffect, useState } from 'react'
import type { ReactNode } from 'react'

import PageHeader from '../components/PageHeader'

import {
  applyExerciseSwap,
  completeWorkout,
  fetchExerciseAlternatives,
  fetchWorkoutPlan,
  skipWorkout,
  type ApiAlternativeExercise,
  type ApiWorkout,
  type ApiWorkoutExercise,
  type CompleteWorkoutPayload,
  type WorkoutPlanResponse,
} from '../api/workouts'

import type {
  LoggedSet,
  Page,
  WorkoutFeedback,
} from '../types'

type Props = {
  setPage: (page: Page) => void
}

type PlanExercise = {
  id: string
  exerciseId: string
  name: string
  sets: string
  setCount: number
}

function toPlanExercise(
  item: ApiWorkoutExercise,
): PlanExercise {
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
  const day =
    workout.day_of_week.slice(0, 3)

  return workout.description
    ? `${day} — ${workout.description}`
    : day
}

function WorkoutDay({
  workout,
}: {
  workout: ApiWorkout
}) {
  const [exercises, setExercises] =
    useState<PlanExercise[]>(() =>
      workout.exercises.map(
        toPlanExercise,
      ),
    )

  const [swapIndex, setSwapIndex] =
    useState<number | null>(null)

  const [
    alternatives,
    setAlternatives,
  ] =
    useState<ApiAlternativeExercise[]>(
      [],
    )

  const [
    loadingAlternatives,
    setLoadingAlternatives,
  ] = useState(false)

  const [
    showCompletion,
    setShowCompletion,
  ] = useState(false)

  const [feedback, setFeedback] =
    useState<WorkoutFeedback>(
      'great',
    )

  const [saving, setSaving] =
    useState(false)

  const [
    actionError,
    setActionError,
  ] = useState<string | null>(null)

  const [logs, setLogs] =
    useState<LoggedSet[][]>(() =>
      workout.exercises.map(
        (item) =>
          Array.from(
            {
              length:
                item.sets_planned,
            },
            () => ({
              reps: '',
              weight: '',
            }),
          ),
      ),
    )

  function updateSet(
    exerciseIndex: number,
    setIndex: number,
    field: keyof LoggedSet,
    value: string,
  ) {
    setLogs((current) =>
      current.map(
        (exerciseSets, i) =>
          i === exerciseIndex
            ? exerciseSets.map(
                (set, j) =>
                  j === setIndex
                    ? {
                        ...set,
                        [field]:
                          value,
                      }
                    : set,
              )
            : exerciseSets,
      ),
    )
  }

  async function openSwap(
    index: number,
  ) {
    if (swapIndex === index) {
      setSwapIndex(null)
      setAlternatives([])
      return
    }

    setSwapIndex(index)
    setAlternatives([])
    setActionError(null)
    setLoadingAlternatives(true)

    try {
      const response =
        await fetchExerciseAlternatives(
          exercises[index].id,
          5,
        )

      setAlternatives(
        response.alternatives,
      )
    } catch (error) {
      setActionError(
        error instanceof Error
          ? error.message
          : 'Could not load alternatives.',
      )
    } finally {
      setLoadingAlternatives(false)
    }
  }

  async function chooseAlternative(
    index: number,
    alternative: ApiAlternativeExercise,
  ) {
    setSaving(true)
    setActionError(null)

    try {
      const updated =
        await applyExerciseSwap(
          exercises[index].id,
          alternative.exercise_id,
        )

      setExercises((current) =>
        current.map(
          (exercise, i) =>
            i === index
              ? toPlanExercise(
                  updated,
                )
              : exercise,
        ),
      )

      setSwapIndex(null)
      setAlternatives([])
    } catch (error) {
      setActionError(
        error instanceof Error
          ? error.message
          : 'Could not swap exercise.',
      )
    } finally {
      setSaving(false)
    }
  }

  async function markIncomplete() {
    setSaving(true)
    setActionError(null)

    try {
      await skipWorkout(
        workout.workout_id,
        'user_marked_incomplete',
      )

      alert(
        'Workout marked incomplete.',
      )
    } catch (error) {
      setActionError(
        error instanceof Error
          ? error.message
          : 'Could not mark workout incomplete.',
      )
    } finally {
      setSaving(false)
    }
  }

  async function submitWorkout() {
    const missingReps =
      logs.some(
        (exerciseSets) =>
          exerciseSets.some(
            (set) =>
              !set.reps ||
              Number(
                set.reps,
              ) <= 0,
          ),
      )

    if (missingReps) {
      setActionError(
        'Please enter the reps completed for every set.',
      )
      return
    }

    const payload: CompleteWorkoutPayload =
      {
        exercises:
          exercises.map(
            (
              exercise,
              exerciseIndex,
            ) => ({
              workout_plan_exercise_id:
                exercise.id,

              sets: logs[
                exerciseIndex
              ].map(
                (
                  set,
                  setIndex,
                ) => ({
                  set_number:
                    setIndex +
                    1,

                  reps: Number(
                    set.reps,
                  ),

                  weight:
                    set.weight ===
                    ''
                      ? null
                      : Number(
                          set.weight,
                        ),

                  weight_unit:
                    'lb',
                }),
              ),
            }),
          ),

        feedback: {
          difficulty:
            feedback,
        },
      }

    setSaving(true)
    setActionError(null)

    try {
      await completeWorkout(
        workout.workout_id,
        payload,
      )

      alert(
        'Workout saved successfully.',
      )

      setShowCompletion(false)
    } catch (error) {
      setActionError(
        error instanceof Error
          ? error.message
          : 'Could not save workout.',
      )
    } finally {
      setSaving(false)
    }
  }

  return (
    <div className="panel workout-detail">
      <h2>
        {workout.day_of_week}

        {workout.description
          ? ` — ${workout.description}`
          : ''}
      </h2>

      <p>
        Week{' '}
        {workout.week_number} •{' '}
        {workout.scheduled_date}
      </p>

      {actionError && (
        <p className="auth-error">
          {actionError}
        </p>
      )}

      <div className="exercise-list large">
        {exercises.map(
          (exercise, index) => (
            <div
              className="exercise-block"
              key={exercise.id}
            >
              <div className="exercise-row">
                <div>
                  <strong>
                    {
                      exercise.name
                    }
                  </strong>

                  <span>
                    {
                      exercise.sets
                    }
                  </span>
                </div>

                <button
                  className="text-button"
                  onClick={() =>
                    openSwap(
                      index,
                    )
                  }
                  disabled={
                    saving
                  }
                >
                  {swapIndex ===
                  index
                    ? 'Cancel'
                    : 'Swap exercise'}
                </button>
              </div>

              {swapIndex ===
                index && (
                <div className="swap-panel">
                  <h3>
                    Alternative
                    exercises
                  </h3>

                  {loadingAlternatives && (
                    <p>
                      Loading
                      alternatives...
                    </p>
                  )}

                  {!loadingAlternatives &&
                    alternatives.length ===
                      0 && (
                      <p>
                        No
                        alternatives
                        available.
                      </p>
                    )}

                  {!loadingAlternatives &&
                    alternatives.length >
                      0 &&
                    alternatives.map(
                      (
                        alternative,
                      ) => (
                        <div
                          className="alternative-row"
                          key={
                            alternative.exercise_id
                          }
                        >
                          <div>
                            <strong>
                              {
                                alternative.name
                              }
                            </strong>

                            <span>
                              {
                                alternative.reason
                              }
                            </span>

                            <small>
                              Equipment:{' '}
                              {alternative.equipment_required.join(
                                ', ',
                              )}
                            </small>
                          </div>

                          <button
                            className="light-button"
                            onClick={() =>
                              chooseAlternative(
                                index,
                                alternative,
                              )
                            }
                            disabled={
                              saving
                            }
                          >
                            {saving
                              ? 'Saving...'
                              : 'Use this'}
                          </button>
                        </div>
                      ),
                    )}
                </div>
              )}
            </div>
          ),
        )}
      </div>

      {!showCompletion && (
        <div className="page-actions inside workout-actions">
          <button
            className="light-button"
            onClick={
              markIncomplete
            }
            disabled={saving}
          >
            Mark Incomplete
          </button>

          <button
            className="gold-button"
            onClick={() =>
              setShowCompletion(
                true,
              )
            }
            disabled={saving}
          >
            Mark Workout
            Complete
          </button>
        </div>
      )}

      {showCompletion && (
        <div className="completion-panel">
          <div className="completion-heading">
            <div>
              <h3>
                Log completed
                workout
              </h3>

              <p>
                Enter the reps
                and weight you
                completed for
                each set. Leave
                weight blank for
                bodyweight
                exercises.
              </p>
            </div>

            <button
              className="text-button"
              onClick={() =>
                setShowCompletion(
                  false,
                )
              }
              disabled={saving}
            >
              Cancel
            </button>
          </div>

          {exercises.map(
            (
              exercise,
              exerciseIndex,
            ) => (
              <div
                className="exercise-log"
                key={`log-${exercise.id}`}
              >
                <strong>
                  {
                    exercise.name
                  }
                </strong>

                <div className="set-log-header">
                  <span>
                    Set
                  </span>

                  <span>
                    Reps
                  </span>

                  <span>
                    Weight (lb)
                  </span>
                </div>

                {logs[
                  exerciseIndex
                ].map(
                  (
                    set,
                    setIndex,
                  ) => (
                    <div
                      className="set-log-row"
                      key={
                        setIndex
                      }
                    >
                      <span>
                        {setIndex +
                          1}
                      </span>

                      <input
                        type="number"
                        min="1"
                        value={
                          set.reps
                        }
                        onChange={(
                          event,
                        ) =>
                          updateSet(
                            exerciseIndex,
                            setIndex,
                            'reps',
                            event
                              .target
                              .value,
                          )
                        }
                        placeholder="10"
                      />

                      <input
                        type="number"
                        min="0"
                        step="2.5"
                        value={
                          set.weight
                        }
                        onChange={(
                          event,
                        ) =>
                          updateSet(
                            exerciseIndex,
                            setIndex,
                            'weight',
                            event
                              .target
                              .value,
                          )
                        }
                        placeholder="Optional"
                      />
                    </div>
                  ),
                )}
              </div>
            ),
          )}

          <div className="workout-feedback">
            <h3>
              How did the
              workout feel?
            </h3>

            <div className="feedback-options">
              {[
                [
                  'great',
                  'Great',
                ],
                [
                  'too_easy',
                  'Too Easy',
                ],
                [
                  'too_hard',
                  'Too Hard',
                ],
              ].map(
                ([
                  value,
                  label,
                ]) => (
                  <button
                    key={value}
                    className={`feedback-button ${
                      feedback ===
                      value
                        ? 'selected'
                        : ''
                    }`}
                    onClick={() =>
                      setFeedback(
                        value as WorkoutFeedback,
                      )
                    }
                    disabled={
                      saving
                    }
                  >
                    {label}
                  </button>
                ),
              )}
            </div>
          </div>

          <div className="page-actions inside">
            <button
              className="gold-button"
              onClick={
                submitWorkout
              }
              disabled={saving}
            >
              {saving
                ? 'Saving...'
                : 'Submit Workout'}
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

function WorkoutPlan({
  setPage,
}: Props) {
  const [data, setData] =
    useState<WorkoutPlanResponse | null>(
      null,
    )

  const [loading, setLoading] =
    useState(true)

  const [error, setError] =
    useState<string | null>(
      null,
    )

  const [
    selectedId,
    setSelectedId,
  ] =
    useState<string | null>(
      null,
    )

  useEffect(() => {
    let cancelled = false

    fetchWorkoutPlan()
      .then((response) => {
        if (cancelled) {
          return
        }

        setData(response)

        setSelectedId(
          response.workouts[0]
            ?.workout_id ??
            null,
        )
      })
      .catch(
        (err: Error) => {
          if (!cancelled) {
            setError(
              err.message,
            )
          }
        },
      )
      .finally(() => {
        if (!cancelled) {
          setLoading(false)
        }
      })

    return () => {
      cancelled = true
    }
  }, [])

  const selected =
    data?.workouts.find(
      (workout) =>
        workout.workout_id ===
        selectedId,
    ) ?? null

  let body: ReactNode

  if (loading) {
    body = (
      <section className="panel">
        <p>
          Loading your workout
          plan...
        </p>
      </section>
    )
  } else if (error) {
    body = (
      <section className="panel">
        <p>
          {error} Refresh the
          page to try again.
        </p>
      </section>
    )
  } else if (
    !data ||
    !data.program ||
    !selected
  ) {
    body = (
      <section className="panel">
        <p>
          {data?.message ??
            'No workouts found.'}
        </p>
      </section>
    )
  } else {
    body = (
      <>
        <section className="panel plan-summary">
          <div>
            <h2>
              {
                data.workouts
                  .length
              }
              -day plan
            </h2>

            <p>
              Goal:{' '}
              {
                data.program
                  .goal
              }

              {data.session_info
                ? ` • ${data.session_info}`
                : ''}
            </p>
          </div>

          <button
            className="light-button"
            onClick={() =>
              setPage(
                'coach',
              )
            }
          >
            Ask AI Coach
          </button>
        </section>

        <section className="plan-grid">
          <div className="panel week-panel">
            <h2>
              This week
            </h2>

            {data.workouts.map(
              (workout) => (
                <button
                  key={
                    workout.workout_id
                  }
                  className={`day-button ${
                    workout.workout_id ===
                    selectedId
                      ? 'active'
                      : ''
                  }`}
                  onClick={() =>
                    setSelectedId(
                      workout.workout_id,
                    )
                  }
                >
                  {dayLabel(
                    workout,
                  )}
                </button>
              ),
            )}
          </div>

          <WorkoutDay
            key={
              selected.workout_id
            }
            workout={
              selected
            }
          />
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