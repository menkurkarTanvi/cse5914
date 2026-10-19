import { useEffect, useState } from 'react'
import PageHeader from '../components/PageHeader'
import type { Page } from '../types'

type Props = {
  setPage: (page: Page) => void
}

const days = [
  'Monday',
  'Tuesday',
  'Wednesday',
  'Thursday',
  'Friday',
  'Saturday',
  'Sunday'
] as const

type Day = (typeof days)[number]

type DayAvailability = {
  available: boolean
  minutes: number
}

// Backend address, and the part of the GET /profiles/profile response we use
const API_URL = 'http://localhost:8000'

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
    max_duration_minutes: number | null
  }[]
}

// NEW: equipment choices. Replace these with the names used in your exercises
// table so they match Exercise.equipment_required, for example:
//   SELECT DISTINCT unnest(equipment_required) FROM exercises ORDER BY 1;
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


function Profile({ setPage }: Props) {
  const [availability, setAvailability] = useState<
  Record<Day, DayAvailability>
  >({
    Monday: { available: true, minutes: 30 },
    Tuesday: { available: true, minutes: 15 },
    Wednesday: { available: false, minutes: 30 },
    Thursday: { available: true, minutes: 60 },
    Friday: { available: false, minutes: 30 },
    Saturday: { available: false, minutes: 45 },
    Sunday: { available: false, minutes: 30 },
  })

  // The saved profile, once it has loaded
  const [profile, setProfile] = useState<LoadedProfile['profile'] | null>(null)

  // Load the current user's profile and availability on first render
  useEffect(() => {
    const token = localStorage.getItem('token')

    fetch(`${API_URL}/profiles/profile`, {
      headers: { Authorization: `Bearer ${token}` },
    })
      .then((response) => {
        if (response.status === 404) return null // no profile yet: keep the defaults
        if (!response.ok) {
          throw new Error(`Failed to load profile (${response.status})`)
        }
        return response.json() as Promise<LoadedProfile>
      })
      .then((data) => {
        if (!data) return

        setProfile(data.profile)
        setAvailability((previous) => {
          const next = { ...previous }
          data.availability.forEach((row) => {
            next[row.day_of_week] = {
              available: row.is_available,
              minutes:
                row.max_duration_minutes ?? previous[row.day_of_week].minutes,
            }
          })
          return next
        })
      })
      .catch((error) => console.error(error))
  }, [])

  const updateDay = (
    day:Day,
    changes: Partial<DayAvailability>
  )=> {
    setAvailability((previous) => ({
      ...previous,
      [day]: {
        ...previous[day],
        ...changes,
      },
    }))
  }
  const availableDays = days.filter(
    (day) => availability[day].available
  )

  const totalMinutes = availableDays.reduce(
    (total, day) => total + availability[day].minutes,
    0
  )

  // NEW: the standard choices, plus anything already saved that isn't in the
  // list, so stored equipment never silently disappears from the form
  const equipmentChoices = Array.from(
    new Set([...equipmentOptions, ...(profile?.available_equipment ?? [])])
  )

return (
    <>
      <PageHeader
        title="Profile Setup"
        subtitle="Tell FitStack about your goals, schedule, and available equipment."
      />

      <section className="profile-grid">
        <div className="panel form-panel">
          <h2>Personal information</h2>

          {/* The key remounts these inputs once the profile loads, so their defaultValue applies */}
          <div className="form-grid" key={profile ? 'loaded' : 'empty'}>
            <label>
              Primary goal
              <select defaultValue={profile?.goal ?? 'hypertrophy'}>
                <option value="strength">Strength</option>
                <option value="hypertrophy">Hypertrophy</option>
                <option value="muscular_endurance">Muscular Endurance</option>
                <option value="power">Power</option>
                <option value="general_fitness">General Fitness</option>
              </select>
            </label>

            <label>
              Experience level
              <select defaultValue={profile?.experience_level ?? 'intermediate'}>
                <option value="beginner">Beginner</option>
                <option value="intermediate">Intermediate</option>
                <option value="advanced">Advanced</option>
              </select>
            </label>

            <label>
              Limitations / injuries
              <input
                placeholder="None"
                defaultValue={profile?.limitations.join(', ') ?? ''}
              />
            </label>
          </div>
        </div>

        <div className="panel form-panel">
          <h2>Training preferences</h2>

          <div className="form-grid one-column" key={profile ? 'loaded' : 'empty'}>
            {/* CHANGED: the backend stores a list of equipment, so this is now
                a set of checkboxes instead of a single dropdown */}
            <div role="group" aria-labelledby="equipment-label">
              <span id="equipment-label">Available equipment</span>

              <div className="availability-list">
                {equipmentChoices.map((item) => (
                  <label className="availability-day" key={item}>
                    <input
                      type="checkbox"
                      defaultChecked={
                        profile?.available_equipment.includes(item) ?? false
                      }
                    />
                    <span>{item}</span>
                  </label>
                ))}
              </div>
            </div>
          </div>

          <h3>Weekly workout availability</h3>
          <p>
            Select the days you are available and choose
            how long you can work out on each day.
          </p>

          <div className="availability-list">
            {days.map((day) => (
              <div className="availability-row" key={day}>
                <label className="availability-day">
                  <input
                    type="checkbox"
                    checked={availability[day].available}
                    onChange={(event) =>
                      updateDay(day, {
                        available: event.target.checked,
                      })
                    }
                  />
                  <span>{day}</span>
                </label>

                <label className="duration-label">
                  <span className="sr-only">
                    Workout duration on {day}
                  </span>
                  <select
                    value={availability[day].minutes}
                    disabled={!availability[day].available}
                    onChange={(event) =>
                      updateDay(day, {
                        minutes: Number(event.target.value),
                      })
                    }
                  >
                    <option value={15}>15 minutes</option>
                    <option value={30}>30 minutes</option>
                    <option value={45}>45 minutes</option>
                    <option value={60}>60 minutes</option>
                    <option value={90}>90 minutes</option>
                  </select>
                </label>
              </div>
            ))}
          </div>

          <div className="availability-summary">
            <p>
              <strong>Available days:</strong>{' '}
              {availableDays.length} of 7
            </p>
            <p>
              <strong>Total weekly time:</strong>{' '}
              {totalMinutes} minutes
            </p>
          </div>
        </div>
      </section>

      <div className="page-actions">
        <button
          className="gold-button"
          onClick={() => setPage('plan')}
        >
          Save Profile
        </button>
      </div>
    </>
  )
}

export default Profile
