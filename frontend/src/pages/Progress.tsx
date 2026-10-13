import PageHeader from '../components/PageHeader'
import StatCard from '../components/StatCard'

function Progress() {
  return (
    <>
      <PageHeader
        title="Progress & Insights"
        subtitle="Track your results and see how your training changes over time."
      />

      <section className="stats-grid">
        <StatCard label="Workouts" value="12" />
        <StatCard label="Avg calories" value="2,450" />
        <StatCard
          label="Strength trend"
          value="+6.8%"
        />
        <StatCard
          label="Body weight"
          value="154 lb"
        />
      </section>

      <section className="panel chart-card">
        <h2>Weight Trend</h2>

        <p>Last 6 weeks</p>

        <div className="fake-chart">
          <div className="grid-line line-1" />
          <div className="grid-line line-2" />
          <div className="grid-line line-3" />

          <svg
            viewBox="0 0 600 220"
            preserveAspectRatio="none"
          >
            <polyline
              points="30,45 130,80 230,105 330,135 430,150 560,175"
              fill="none"
              stroke="currentColor"
              strokeWidth="6"
              strokeLinecap="round"
              strokeLinejoin="round"
            />
          </svg>
        </div>

        <p className="insight">
          AI insight: weight is trending gradually while workout consistency is improving.
        </p>
      </section>
    </>
  )
}

export default Progress