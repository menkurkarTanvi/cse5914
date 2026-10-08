import PageHeader from '../components/PageHeader'
import StatCard from '../components/StatCard'

function Nutrition() {
  return (
    <>
      <PageHeader
        title="Nutrition"
        subtitle="Simple daily targets that support your current fitness goal."
      />

      <section className="stats-grid">
        <StatCard label="Calories" value="2,650 kcal" />
        <StatCard label="Protein" value="165 g" />
        <StatCard label="Carbs" value="320 g" />
        <StatCard label="Fat" value="75 g" />
      </section>

      <section className="panel nutrition-panel">
        <h2>Today's targets</h2>

        <p>
          Your daily nutrition targets are based on your current fitness goal,
          activity level, and training plan.
        </p>
      </section>
    </>
  )
}

export default Nutrition