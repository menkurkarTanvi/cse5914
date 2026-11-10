import { useState } from 'react'
import PageHeader from '../components/PageHeader'
import StatCard from '../components/StatCard'

const weeklyActivity = [
  { day: 'Mon', minutes: 55, completed: true },
  { day: 'Tue', minutes: 45, completed: true },
  { day: 'Wed', minutes: 0, completed: false },
  { day: 'Thu', minutes: 60, completed: true },
  { day: 'Fri', minutes: 0, completed: false },
  { day: 'Sat', minutes: 50, completed: true },
  { day: 'Sun', minutes: 0, completed: false },
]

const exerciseHistory = {
  'Dumbbell Bench Press': [
    { date: 'Oct 12', weight: 20, reps: 10 },
    { date: 'Oct 19', weight: 25, reps: 10 },
    { date: 'Oct 26', weight: 25, reps: 12 },
    { date: 'Nov 2', weight: 30, reps: 10 },
    { date: 'Nov 9', weight: 30, reps: 12 },
  ],
  'Shoulder Press': [
    { date: 'Oct 12', weight: 15, reps: 10 },
    { date: 'Oct 19', weight: 15, reps: 12 },
    { date: 'Oct 26', weight: 20, reps: 10 },
    { date: 'Nov 2', weight: 20, reps: 10 },
    { date: 'Nov 9', weight: 25, reps: 8 },
  ],
  'Bicep Curl': [
    { date: 'Oct 12', weight: 10, reps: 12 },
    { date: 'Oct 19', weight: 10, reps: 12 },
    { date: 'Oct 26', weight: 12, reps: 10 },
    { date: 'Nov 2', weight: 15, reps: 10 },
    { date: 'Nov 9', weight: 15, reps: 12 },
  ],
}

type ExerciseName = keyof typeof exerciseHistory

function Progress() {
  const [selectedExercise, setSelectedExercise] =
    useState<ExerciseName>('Dumbbell Bench Press')

  const history = exerciseHistory[selectedExercise]

  const maxMinutes = Math.max(
    ...weeklyActivity.map((day) => day.minutes),
    1,
  )

  const maxWeight = Math.max(
    ...history.map((entry) => entry.weight),
  )

  const minWeight = Math.min(
    ...history.map((entry) => entry.weight),
  )

  const chartPoints = history
    .map((entry, index) => {
      const x = 40 + index * 125
      const y =
        180 -
        ((entry.weight - minWeight) /
          Math.max(maxWeight - minWeight, 1)) *
          130

      return `${x},${y}`
    })
    .join(' ')

  return (
    <>
      <PageHeader
        title="Progress & Insights"
        subtitle="Track your results and see how your training changes over time."
      />

      {/* workout summary */}
      <section className="stats-grid">
        <StatCard label="Workouts completed" value="12" />
        <StatCard label="Workout streak" value="5 days" />
        <StatCard label="Total workout time" value="12 hrs" />
        <StatCard label="Weekly goal" value="4 / 4" />
      </section>

      {/* weekly consistency */}
      <section className="progress-grid">
        <div className="panel">
          <h2>Weekly Workout Activity</h2>
          <p>Your workout activity this week.</p>

          <div className="weekly-chart">
            {weeklyActivity.map((day) => (
              <div
                className="weekly-chart-column"
                key={day.day}
              >
                <span className="weekly-minutes">
                  {day.minutes > 0 ? `${day.minutes}m` : ''}
                </span>

                <div className="weekly-bar-container">
                  <div
                    className={`weekly-bar ${
                      day.completed ? 'completed' : ''
                    }`}
                    style={{
                      height: `${(day.minutes / maxMinutes) * 100}%`,
                    }}
                  />
                </div>

                <span className="weekly-day">{day.day}</span>
              </div>
            ))}
          </div>

          <p className="insight">
            You completed 4 workouts this week!
          </p>
        </div>

        <div className="panel">
          <h2>Consistency</h2>
          <p>Your weekly workout schedule.</p>

          <div className="consistency-streak">
            <strong>5 Day Streak</strong>
            <span>Keep showing up!</span>
          </div>

          <div className="consistency-calendar">
            {weeklyActivity.map((day) => (
              <div
                className="consistency-day"
                key={day.day}
              >
                <span>{day.day}</span>

                <div
                  className={`consistency-circle ${
                    day.completed ? 'completed' : ''
                  }`}
                >
                  {day.completed ? '✓' : '–'}
                </div>
              </div>
            ))}
          </div>

          <div className="weekly-goal">
            <div className="goal-heading">
              <span>Weekly Goal</span>
              <strong>4 / 4 workouts</strong>
            </div>

            <div className="goal-progress">
              <div
                className="goal-progress-fill"
                style={{ width: '100%' }}
              />
            </div>

            <small>
              Great job! You reached your weekly workout goal.
            </small>
          </div>
        </div>
      </section>

      {/* exercise progress */}
      <section className="panel exercise-performance">
        <div className="performance-header">
          <div>
            <h2>Exercise Performance</h2>
            <p>Track your strength improvements over time.</p>
          </div>

          <select
            value={selectedExercise}
            onChange={(event) =>
              setSelectedExercise(
                event.target.value as ExerciseName,
              )
            }
            aria-label="Select exercise"
          >
            {Object.keys(exerciseHistory).map((exercise) => (
              <option key={exercise} value={exercise}>
                {exercise}
              </option>
            ))}
          </select>
        </div>

        <div className="performance-summary">
          <div>
            <span>Current Weight</span>
            <strong>
              {history[history.length - 1].weight} lb
            </strong>
          </div>

          <div>
            <span>Current Reps</span>
            <strong>
              {history[history.length - 1].reps}
            </strong>
          </div>

          <div>
            <span>Weight Increase</span>
            <strong className="positive">
              +{history[history.length - 1].weight -
                history[0].weight} lb
            </strong>
          </div>
        </div>

        <h3 className="chart-subtitle">
          Weight Lifted Over Time
        </h3>

        <div className="fake-chart performance-chart">
          <div className="grid-line line-1" />
          <div className="grid-line line-2" />
          <div className="grid-line line-3" />

          <svg
            viewBox="0 0 600 220"
            preserveAspectRatio="none"
            role="img"
            aria-label={`Weight history for ${selectedExercise}`}
          >
            <polyline
              points={chartPoints}
              fill="none"
              stroke="currentColor"
              strokeWidth="5"
              strokeLinecap="round"
              strokeLinejoin="round"
            />

            {history.map((entry, index) => {
              const x = 40 + index * 125
              const y =
                180 -
                ((entry.weight - minWeight) /
                  Math.max(maxWeight - minWeight, 1)) *
                  130

              return (
                <circle
                  key={entry.date}
                  cx={x}
                  cy={y}
                  r="6"
                  fill="#f2b827"
                />
              )
            })}
          </svg>
        </div>

        <div className="performance-dates">
          {history.map((entry) => (
            <span key={entry.date}>{entry.date}</span>
          ))}
        </div>

        <h3 className="chart-subtitle">
          Workout History
        </h3>

        <div className="performance-table">
          <div className="performance-table-row table-heading">
            <span>Date</span>
            <span>Weight</span>
            <span>Reps</span>
          </div>

          {history.map((entry) => (
            <div
              className="performance-table-row"
              key={entry.date}
            >
              <span>{entry.date}</span>
              <span>{entry.weight} lb</span>
              <span>{entry.reps}</span>
            </div>
          ))}
        </div>
      </section>

      {/* achievements */}
      <section className="panel achievements-panel">
        <h2>Milestone Achievements</h2>
        <p>Celebrate your fitness accomplishments.</p>

        <div className="achievement-grid">
          <div className="achievement-card">
            <span className="achievement-icon">10</span>
            <strong>First 10 Workouts</strong>
            <small>Completed 10 workouts</small>
            <span className="achievement-earned">
              Earned
            </span>
          </div>

          <div className="achievement-card">
            <span className="achievement-icon">7</span>
            <strong>Consistency Champion</strong>
            <small>Maintain a 7-day streak</small>
            <span className="achievement-locked">
              In Progress
            </span>
          </div>

          <div className="achievement-card">
            <span className="achievement-icon">+</span>
            <strong>Getting Stronger</strong>
            <small>Increase exercise weight</small>
            <span className="achievement-earned">
              Earned
            </span>
          </div>
        </div>
      </section>
    </>
  )
}

export default Progress