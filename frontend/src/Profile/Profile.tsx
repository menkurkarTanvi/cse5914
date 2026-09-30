import { useState } from 'react'

type Page =
  | 'dashboard'
  | 'plan'
  | 'progress'
  | 'coach'
  | 'nutrition'
  | 'profile'

type ProfileProps = {
  setPage: (page: Page) => void
}

type FormData = {
  equipment: string[]
  location: string
  availableDays: string[]
  sessionLength: string
  limitations: string[]
  limitationDetails: string
  goals: string[]
  experienceLevel: string
  trainingBlockLength: string
}

const initialFormData: FormData = {
  equipment: [],
  location: '',
  availableDays: [],
  sessionLength: '',
  limitations: [],
  limitationDetails: '',
  goals: [],
  experienceLevel: '',
  trainingBlockLength: '4',
}

function ProfileSetup({ setPage }: ProfileProps) {
  const [formData, setFormData] =
    useState<FormData>(initialFormData)

  const [submitted, setSubmitted] = useState(false)

  function updateField(
    field: keyof FormData,
    value: string | string[],
  ) {
    setFormData((current) => ({
      ...current,
      [field]: value,
    }))
  }

  function toggleArrayValue(
    field:
      | 'equipment'
      | 'availableDays'
      | 'limitations'
      | 'goals',
    value: string,
  ) {
    setFormData((current) => {
      const currentValues = current[field]

      const updatedValues = currentValues.includes(value)
        ? currentValues.filter((item) => item !== value)
        : [...currentValues, value]

      return {
        ...current,
        [field]: updatedValues,
      }
    })
  }

  function handleSubmit(event: React.FormEvent) {
    event.preventDefault()

    console.log('Profile data:', formData)

    setSubmitted(true)

    setPage('dashboard')

    // backend stuff here later
  }

  return (
    <>
      <header className="page-header">
        <h1>Profile Setup</h1>

        <p>
          Personalize your workouts with your goals, schedule, and equipment!
        </p>
      </header>

      <form
        className="profile-grid"
        onSubmit={handleSubmit}
      >
        {/* Equipment & Location */}

        <section className="panel form-panel">
          <h2>Equipment & Location</h2>

          <label>
            Workout location

            <select
              value={formData.location}
              onChange={(event) =>
                updateField(
                  'location',
                  event.target.value,
                )
              }
              required
            >
              <option value="">
                Select location
              </option>

              <option value="gym">Gym</option>
              <option value="home">Home</option>
              <option value="travel">Travel</option>
              <option value="outdoors">Outdoors</option>
            </select>
          </label>

          <h3>Available equipment</h3>

          {[
            ['gym', 'Full gym'],
            ['dumbbells', 'Dumbbells only'],
            ['bodyweight', 'Bodyweight'],
            ['travel', 'Travel equipment'],
          ].map(([value, label]) => (
            <label key={value}>
              <input
                type="checkbox"
                checked={formData.equipment.includes(value)}
                onChange={() =>
                  toggleArrayValue(
                    'equipment',
                    value,
                  )
                }
              />

              {label}
            </label>
          ))}
        </section>

        {/* Schedule */}

        <section className="panel form-panel">
          <h2>Schedule</h2>

          <h3>Days available</h3>

          {[
            'Monday',
            'Tuesday',
            'Wednesday',
            'Thursday',
            'Friday',
            'Saturday',
            'Sunday',
          ].map((day) => (
            <label key={day}>
              <input
                type="checkbox"
                checked={formData.availableDays.includes(day)}
                onChange={() =>
                  toggleArrayValue(
                    'availableDays',
                    day,
                  )
                }
              />

              {day}
            </label>
          ))}

          <label>
            Maximum session length

            <select
              value={formData.sessionLength}
              onChange={(event) =>
                updateField(
                  'sessionLength',
                  event.target.value,
                )
              }
              required
            >
              <option value="">
                Select duration
              </option>

              <option value="15">15 minutes</option>
              <option value="30">30 minutes</option>
              <option value="45">45 minutes</option>
              <option value="60">60 minutes</option>
              <option value="90">90 minutes</option>
            </select>
          </label>
        </section>

        {/* Injuries & Limitations */}

        <section className="panel form-panel">
          <h2>Injuries & Limitations</h2>

          <p>
            Select any limitations that should be considered when generating workouts.
          </p>

          {[
            ['none', 'No limitations'],
            ['knee', 'Knee'],
            ['back', 'Back'],
            ['shoulder', 'Shoulder'],
            ['wrist', 'Wrist'],
            ['other', 'Other'],
          ].map(([value, label]) => (
            <label key={value}>
              <input
                type="checkbox"
                checked={formData.limitations.includes(value)}
                onChange={() =>
                  toggleArrayValue(
                    'limitations',
                    value,
                  )
                }
              />

              {label}
            </label>
          ))}

          <label>
            Additional details

            <textarea
              value={formData.limitationDetails}
              onChange={(event) =>
                updateField(
                  'limitationDetails',
                  event.target.value,
                )
              }
              placeholder="Describe any limitations"
            />
          </label>
        </section>

        {/* Goals */}

        <section className="panel form-panel">
          <h2>Fitness Goals</h2>

          <p>Select one or more goals.</p>

          {[
            ['strength', 'Strength'],
            ['hypertrophy', 'Hypertrophy'],
            ['fat_loss', 'Fat loss'],
            ['endurance', 'Endurance'],
          ].map(([value, label]) => (
            <label key={value}>
              <input
                type="checkbox"
                checked={formData.goals.includes(value)}
                onChange={() =>
                  toggleArrayValue(
                    'goals',
                    value,
                  )
                }
              />

              {label}
            </label>
          ))}
        </section>

        {/* Experience */}

        <section className="panel form-panel">
          <h2>Experience Level</h2>

          {[
            ['beginner', 'Beginner'],
            ['intermediate', 'Intermediate'],
            ['advanced', 'Advanced'],
          ].map(([value, label]) => (
            <label key={value}>
              <input
                type="radio"
                name="experienceLevel"
                value={value}
                checked={
                  formData.experienceLevel === value
                }
                onChange={(event) =>
                  updateField(
                    'experienceLevel',
                    event.target.value,
                  )
                }
                required
              />

              {label}
            </label>
          ))}
        </section>

        {/* Training Block */}

        <section className="panel form-panel">
          <h2>Training Block</h2>

          <label>
            Training block length

            <select
              value={formData.trainingBlockLength}
              onChange={(event) =>
                updateField(
                  'trainingBlockLength',
                  event.target.value,
                )
              }
            >
              <option value="4">
                4 weeks (Default)
              </option>

              <option value="6">6 weeks</option>
              <option value="8">8 weeks</option>
            </select>
          </label>
        </section>

        {/* Submit */}

        <div className="page-actions">
          <button
            className="gold-button"
            type="submit"
          >
            Save Profile
          </button>
        </div>

        {submitted && (
          <p>
            Profile information collected!
            Backend integration is next.
          </p>
        )}
      </form>
    </>
  )
}

export default ProfileSetup