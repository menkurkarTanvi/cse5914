import { useState } from 'react'

import PageHeader from '../components/PageHeader'

import { mockAlternatives } from '../data/mockData'

import type {
  Exercise,
  LoggedSet,
  Page,
  WorkoutFeedback,
} from '../types'

type Props = {
  exercises: Exercise[]

  swapExercise: (
    index: number,
    replacement: {
      id: string
      name: string
    },
  ) => void

  setPage: (page: Page) => void
}

function getSetCount(sets: string) {
  const match = sets.match(/^\d+/)

  return match
    ? Number(match[0])
    : 3
}

function WorkoutPlan({
  exercises,
  swapExercise,
  setPage,
}: Props) {
  const [swapIndex, setSwapIndex] =
    useState<number | null>(null)

  const [
    showCompletion,
    setShowCompletion,
  ] = useState(false)

  const [feedback, setFeedback] =
    useState<WorkoutFeedback>('great')

  const [logs, setLogs] =
    useState<LoggedSet[][]>(() =>
      exercises.map((exercise) =>
        Array.from(
          {
            length: getSetCount(
              exercise.sets,
            ),
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
                        [field]: value,
                      }
                    : set,
              )
            : exerciseSets,
      ),
    )
  }

  function skipWorkout() {
    const payload = {
      reason:
        'user_marked_incomplete',
    }

    console.log(
      'Workout skip payload:',
      payload,
    )

    alert(
      'Incomplete workout is ready for backend integration.',
    )
  }

  function submitWorkout() {
    const payload = {
      exercises: exercises.map(
        (
          exercise,
          exerciseIndex,
        ) => ({
          workout_plan_exercise_id:
            exercise.id,

          sets: logs[
            exerciseIndex
          ].map(
            (set, setIndex) => ({
              set_number:
                setIndex + 1,

              reps: Number(
                set.reps,
              ),

              weight:
                set.weight === ''
                  ? null
                  : Number(
                      set.weight,
                    ),

              weight_unit: 'lb',
            }),
          ),
        }),
      ),

      feedback: {
        difficulty: feedback,
      },
    }

    console.log(
      'Workout completion payload:',
      payload,
    )

    alert(
      'Workout log is ready for backend integration.',
    )

    setShowCompletion(false)
  }

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
            Goal: Build muscle • 60
            min/session • Full gym
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
              (exercise, index) => {
                const alternatives =
                  mockAlternatives[
                    exercise.id
                  ] ?? []

                return (
                  <div
                    className="exercise-block"
                    key={`${exercise.id}-${index}`}
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
                          setSwapIndex(
                            swapIndex ===
                              index
                              ? null
                              : index,
                          )
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

                        {alternatives.length ===
                        0 ? (
                          <p>
                            No
                            alternatives
                            available yet.
                          </p>
                        ) : (
                          alternatives.map(
                            (
                              alternative,
                            ) => (
                              <div
                                className="alternative-row"
                                key={
                                  alternative.exerciseId
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
                                    {alternative.equipmentRequired.join(
                                      ', ',
                                    )}
                                  </small>
                                </div>

                                <button
                                  className="light-button"
                                  onClick={() => {
                                    swapExercise(
                                      index,
                                      {
                                        id: alternative.exerciseId,
                                        name: alternative.name,
                                      },
                                    )

                                    setSwapIndex(
                                      null,
                                    )
                                  }}
                                >
                                  Use this
                                </button>
                              </div>
                            ),
                          )
                        )}
                      </div>
                    )}
                  </div>
                )
              },
            )}
          </div>

          {!showCompletion ? (
            <div className="page-actions inside workout-actions">
              <button
                className="light-button"
                onClick={skipWorkout}
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
              >
                Mark Workout
                Complete
              </button>
            </div>
          ) : (
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
                    each set.
                  </p>
                </div>

                <button
                  className="text-button"
                  onClick={() =>
                    setShowCompletion(
                      false,
                    )
                  }
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
                    key={`log-${exercise.id}-${exerciseIndex}`}
                  >
                    <strong>
                      {
                        exercise.name
                      }
                    </strong>

                    <div className="set-log-header">
                      <span>Set</span>
                      <span>Reps</span>
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
                            placeholder="135"
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
                >
                  Submit Workout
                </button>
              </div>
            </div>
          )}
        </div>
      </section>
    </>
  )
}

export default WorkoutPlan