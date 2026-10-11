import { useState } from 'react'
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
              <input type="number" defaultValue="26" min="1" />
            </label>

            <label>
              Weight (lb)
              <input type="number" defaultValue="154" min="1" />
            </label>

            <label>
              Primary goal
              <select defaultValue="Build muscle">
                <option>Build muscle</option>
                <option>Strength</option>
                <option>Fat loss</option>
                <option>Endurance</option>
              </select>
            </label>

            <label>
              Experience level
              <select defaultValue="Intermediate">
                <option>Beginner</option>
                <option>Intermediate</option>
                <option>Advanced</option>
              </select>
            </label>

            <label>
              Activity level
              <select defaultValue="Moderately active">
                <option>Lightly active</option>
                <option>Moderately active</option>
                <option>Very active</option>
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
              Available equipment
              <select defaultValue="Full gym">
                <option>Full gym</option>
                <option>Dumbbells only</option>
                <option>Bodyweight</option>
                <option>Travel / limited</option>
              </select>
            </label>

            <label>
              Preferred training style
              <select defaultValue="Hypertrophy / strength">
                <option>Hypertrophy / strength</option>
                <option>General fitness</option>
                <option>Endurance</option>
              </select>
            </label>
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
          Generate My Plan
        </button>
      </div>
    </>
  )
}

export default Profile