import "./Dashboard.css";
import NavBar from '../NavBar/NavBar';

interface StatCardProps {
  label: string;
  value: string;
}

function StatCard({ label, value }: StatCardProps) {
  return (
    <div className="stat-card">
      <span className="stat-label">{label}</span>
      <span className="stat-value">{value}</span>
    </div>
  );
}

interface Exercise {
  name: string;
  sets: string;
}

const todayExercises: Exercise[] = [
  { name: "Barbell Bench Press", sets: "3 × 8–10" },
  { name: "Incline Dumbbell Press", sets: "3 × 8–10" },
  { name: "Shoulder Press", sets: "3 × 10" },
  { name: "Lateral Raises", sets: "3 × 12–15" },
];

const coachPrompts: string[] = [
  "I only have 30 minutes",
  "Swap an exercise",
  "I feel sore today",
];

export default function Dashboard() {
  return (
    <div className="app-shell">
      <NavBar />

      <main className="dashboard">
        <header className="dashboard-header">
          <h1>Dashboard</h1>
          <p>Your daily plan, nutrition targets, and AI coaching in one place.</p>
        </header>

        <section className="stat-grid">
          <StatCard label="Calorie Target" value="2,650 kcal" />
          <StatCard label="Protein" value="165 g" />
          <StatCard label="Current Streak" value="5 days" />
          <StatCard label="Weight" value="154 lb" />
        </section>

        <section className="dashboard-grid">
          <div className="panel workout-panel">
            <div className="panel-header">
              <h2>Today — Push Day</h2>
              <p>60 min • Chest, shoulders, triceps</p>
            </div>

            <ul className="exercise-list">
              {todayExercises.map((exercise) => (
                <li className="exercise-row" key={exercise.name}>
                  <div>
                    <p className="exercise-name">{exercise.name}</p>
                    <p className="exercise-sets">{exercise.sets}</p>
                  </div>
                  <button type="button" className="view-link">
                    View
                  </button>
                </li>
              ))}
            </ul>
          </div>

          <div className="panel coach-panel">
            <h2>AI Coach</h2>
            <p>
              Adapt your workout if your schedule, equipment, or energy
              changes.
            </p>

            <button type="button" className="ask-coach-btn">
              Ask AI Coach
            </button>

            <div className="coach-prompts">
              {coachPrompts.map((prompt) => (
                <button type="button" className="coach-prompt" key={prompt}>
                  {prompt}
                </button>
              ))}
            </div>
          </div>
        </section>
      </main>
    </div>
  );
}