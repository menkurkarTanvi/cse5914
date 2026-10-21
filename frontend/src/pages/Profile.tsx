import { useEffect, useState } from 'react'

import PageHeader from '../components/PageHeader'

import type { Page } from '../types'

type Props = {
  setPage: (page: Page) => void
}

const API_URL =
  import.meta.env.VITE_API_URL ??
  'http://localhost:8000'

const days = [
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday',
  'Sunday',
] as const

type Day = (typeof days)[number]

type DayAvailability = {
  available: boolean
  minutes: number
}

type LoadedProfile = {
  profile: {
    goal: string
    experience_level: string
    available_equipment: string[]
    limitations: string[]
  }

  availability: {
    day_of_week: Day
    is_available: boolean
    max_duration_minutes:
      | number
      | null
  }[]
}

const equipmentOptions = [
  'Medicine Ball',
  'Exercise Ball',
  'Barbell',
  'Dumbbell',
  'Bench',
  'Cable',
  'E-z Curl Bar',
  'Machine',
  'Kettlebells',
  'Resistance Band',
  'Pull-up Bar',
  'Foam Roll',
  'Bands',
  'Body Only',
  'Other',
]

function Profile({
  setPage,
}: Props) {
  const [goal, setGoal] =
    useState('hypertrophy')

  const [
    experienceLevel,
    setExperienceLevel,
  ] = useState('intermediate')

  const [
    limitations,
    setLimitations,
  ] = useState('')

  const [
    selectedEquipment,
    setSelectedEquipment,
  ] = useState<string[]>([])

  const [saving, setSaving] =
    useState(false)

  const [
    saveError,
    setSaveError,
  ] = useState<string | null>(
    null,
  )

  const [
    availability,
    setAvailability,
  ] = useState<
    Record<
      Day,
      DayAvailability
    >
  >({
    Monday: {
      available: true,
      minutes: 30,
    },

    Tuesday: {
      available: true,
      minutes: 15,
    },

    Wednesday: {
      available: false,
      minutes: 30,
    },

    Thursday: {
      available: true,
      minutes: 60,
    },

    Friday: {
      available: false,
      minutes: 30,
    },

    Saturday: {
      available: false,
      minutes: 45,
    },

    Sunday: {
      available: false,
      minutes: 30,
    },
  })

  useEffect(() => {
    const token =
      localStorage.getItem(
        'token',
      )

    if (!token) {
      return
    }

    fetch(
      `${API_URL}/profiles/profile`,
      {
        headers: {
          Authorization:
            `Bearer ${token}`,
        },
      },
    )
      .then((response) => {
        if (
          response.status === 404
        ) {
          return null
        }

        if (!response.ok) {
          throw new Error(
            `Failed to load profile (${response.status})`,
          )
        }

        return response.json() as Promise<LoadedProfile>
      })
      .then((data) => {
        if (!data) {
          return
        }

        setGoal(
          data.profile.goal,
        )

        setExperienceLevel(
          data.profile
            .experience_level,
        )

        setLimitations(
          data.profile.limitations.join(
            ', ',
          ),
        )

        setSelectedEquipment(
          data.profile
            .available_equipment,
        )

        setAvailability(
          (previous) => {
            const next = {
              ...previous,
            }

            data.availability.forEach(
              (row) => {
                next[
                  row.day_of_week
                ] = {
                  available:
                    row.is_available,

                  minutes:
                    row.max_duration_minutes ??
                    previous[
                      row
                        .day_of_week
                    ].minutes,
                }
              },
            )

            return next
          },
        )
      })
      .catch((error) => {
        console.error(error)
      })
  }, [])

  function updateDay(
    day: Day,
    changes: Partial<DayAvailability>,
  ) {
    setAvailability(
      (previous) => ({
        ...previous,

        [day]: {
          ...previous[day],
          ...changes,
        },
      }),
    )
  }

  function toggleEquipment(
    item: string,
  ) {
    setSelectedEquipment(
      (current) => {
        if (
          current.includes(item)
        ) {
          return current.filter(
            (equipment) =>
              equipment !== item,
          )
        }

        return [
          ...current,
          item,
        ]
      },
    )
  }

  async function saveProfile() {
    const token =
      localStorage.getItem(
        'token',
      )

    if (!token) {
      setSaveError(
        'Please log in again.',
      )
      return
    }

    const hasAvailableDay =
      days.some(
        (day) =>
          availability[day]
            .available,
      )

    if (!hasAvailableDay) {
      setSaveError(
        'Please select at least one available workout day.',
      )
      return
    }

    setSaving(true)
    setSaveError(null)

    const limitationList =
      limitations
        .split(',')
        .map((item) =>
          item.trim(),
        )
        .filter(Boolean)

    const payload = {
      profile: {
        goal,

        experience_level:
          experienceLevel,

        available_equipment:
          selectedEquipment,

        preferred_exercises:
          [],

        disliked_exercises:
          [],

        limitations:
          limitationList,
      },

      availability:
        days.map((day) => ({
          day_of_week: day,

          is_available:
            availability[day]
              .available,

          max_duration_minutes:
            availability[day]
              .available
              ? availability[
                  day
                ].minutes
              : null,
        })),
    }

    try {
      const response =
        await fetch(
          `${API_URL}/profiles/createProfile`,
          {
            method: 'POST',

            headers: {
              'Content-Type':
                'application/json',

              Authorization:
                `Bearer ${token}`,
            },

            body:
              JSON.stringify(
                payload,
              ),
          },
        )

      if (!response.ok) {
        const errorBody =
          await response
            .json()
            .catch(() => null)

        console.error(
          'Profile save failed:',
          errorBody,
        )

        throw new Error(
          `Could not save profile (${response.status}).`,
        )
      }

      await response.json()

      setPage('plan')
    } catch (error) {
      setSaveError(
        error instanceof Error
          ? error.message
          : 'Could not save profile.',
      )
    } finally {
      setSaving(false)
    }
  }

  const availableDays =
    days.filter(
      (day) =>
        availability[day]
          .available,
    )

  const totalMinutes =
    availableDays.reduce(
      (total, day) =>
        total +
        availability[day]
          .minutes,
      0,
    )

  const equipmentChoices =
    Array.from(
      new Set([
        ...equipmentOptions,
        ...selectedEquipment,
      ]),
    )

  return (
    <>
      <PageHeader
        title="Profile Setup"
        subtitle="Tell FitStack about your goals, schedule, and available equipment."
      />

      {saveError && (
        <p className="auth-error">
          {saveError}
        </p>
      )}

      <section className="profile-grid">
        <div className="panel form-panel">
          <h2>
            Personal information
          </h2>

          <div className="form-grid">
            <label>
              Primary goal

              <select
                value={goal}
                onChange={(
                  event,
                ) =>
                  setGoal(
                    event.target
                      .value,
                  )
                }
              >
                <option value="strength">
                  Strength
                </option>

                <option value="hypertrophy">
                  Hypertrophy
                </option>

                <option value="muscular_endurance">
                  Muscular
                  Endurance
                </option>

                <option value="power">
                  Power
                </option>

                <option value="general_fitness">
                  General Fitness
                </option>
              </select>
            </label>

            <label>
              Experience level

              <select
                value={
                  experienceLevel
                }
                onChange={(
                  event,
                ) =>
                  setExperienceLevel(
                    event.target
                      .value,
                  )
                }
              >
                <option value="beginner">
                  Beginner
                </option>

                <option value="intermediate">
                  Intermediate
                </option>

                <option value="advanced">
                  Advanced
                </option>
              </select>
            </label>

            <label>
              Limitations /
              injuries

              <input
                placeholder="None"
                value={
                  limitations
                }
                onChange={(
                  event,
                ) =>
                  setLimitations(
                    event.target
                      .value,
                  )
                }
              />
            </label>
          </div>
        </div>

        <div className="panel form-panel">
          <h2>
            Training preferences
          </h2>

          <div className="form-grid one-column">
            <div
              role="group"
              aria-labelledby="equipment-label"
            >
              <span id="equipment-label">
                Available
                equipment
              </span>

              <div className="availability-list">
                {equipmentChoices.map(
                  (item) => (
                    <label
                      className="availability-day"
                      key={
                        item
                      }
                    >
                      <input
                        type="checkbox"
                        checked={selectedEquipment.includes(
                          item,
                        )}
                        onChange={() =>
                          toggleEquipment(
                            item,
                          )
                        }
                      />

                      <span>
                        {item}
                      </span>
                    </label>
                  ),
                )}
              </div>
            </div>
          </div>

          <h3>
            Weekly workout
            availability
          </h3>

          <p>
            Select the days you
            are available and
            choose how long you
            can work out on each
            day.
          </p>

          <div className="availability-list">
            {days.map((day) => (
              <div
                className="availability-row"
                key={day}
              >
                <label className="availability-day">
                  <input
                    type="checkbox"
                    checked={
                      availability[
                        day
                      ].available
                    }
                    onChange={(
                      event,
                    ) =>
                      updateDay(
                        day,
                        {
                          available:
                            event
                              .target
                              .checked,
                        },
                      )
                    }
                  />

                  <span>
                    {day}
                  </span>
                </label>

                <label className="duration-label">
                  <span className="sr-only">
                    Workout
                    duration on{' '}
                    {day}
                  </span>

                  <select
                    value={
                      availability[
                        day
                      ].minutes
                    }
                    disabled={
                      !availability[
                        day
                      ].available
                    }
                    onChange={(
                      event,
                    ) =>
                      updateDay(
                        day,
                        {
                          minutes:
                            Number(
                              event
                                .target
                                .value,
                            ),
                        },
                      )
                    }
                  >
                    <option
                      value={15}
                    >
                      15 minutes
                    </option>

                    <option
                      value={30}
                    >
                      30 minutes
                    </option>

                    <option
                      value={45}
                    >
                      45 minutes
                    </option>

                    <option
                      value={60}
                    >
                      60 minutes
                    </option>

                    <option
                      value={90}
                    >
                      90 minutes
                    </option>
                  </select>
                </label>
              </div>
            ))}
          </div>

          <div className="availability-summary">
            <p>
              <strong>
                Available days:
              </strong>{' '}
              {
                availableDays.length
              }{' '}
              of 7
            </p>

            <p>
              <strong>
                Total weekly
                time:
              </strong>{' '}
              {totalMinutes}{' '}
              minutes
            </p>
          </div>
        </div>
      </section>

      <div className="page-actions">
        <button
          className="gold-button"
          onClick={
            saveProfile
          }
          disabled={saving}
        >
          {saving
            ? 'Saving...'
            : 'Save Profile'}
        </button>
      </div>
    </>
  )
}

export default Profile