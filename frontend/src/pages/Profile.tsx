import PageHeader from '../components/PageHeader'
import type { Page } from '../types'

type Props = {
  setPage: (page: Page) => void
}

function Profile({ setPage }: Props) {
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
              <input defaultValue="26" />
            </label>

            <label>
              Weight
              <input defaultValue="154" />
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
              Workout days per week
              <select defaultValue="4 days">
                <option>3 days</option>
                <option>4 days</option>
                <option>5 days</option>
                <option>6 days</option>
              </select>
            </label>

            <label>
              Typical session length
              <select defaultValue="60 minutes">
                <option>30 minutes</option>
                <option>45 minutes</option>
                <option>60 minutes</option>
                <option>90 minutes</option>
              </select>
            </label>

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