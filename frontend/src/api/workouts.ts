const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

export type ApiWorkoutExercise = {
  id: string // WorkoutPlanExercise id
  exercise_id: string
  name: string
  exercise_order: number
  sets_planned: number
  reps_min: number
  reps_max: number
  target_rpe_min: number | null
  target_rpe_max: number | null
  rest_seconds: number
  planned_weight: number | null
  weight_unit: string
}

export type ApiWorkout = {
  workout_id: string
  day_of_week: string
  description: string | null
  week_number: number
  scheduled_date: string
  status: 'scheduled' | 'completed' | 'incompleted'
  exercises: ApiWorkoutExercise[]
}

export type ApiProgram = {
  program_id: string
  goal: string
  status: string
  start_date: string
  end_date: string
}

export type WorkoutPlanResponse = {
  program: ApiProgram | null
  workouts: ApiWorkout[]
  session_info?: string | null // only present if you add it on the backend
  message: string | null
}

export async function fetchWorkoutPlan(): Promise<WorkoutPlanResponse> {
  // TODO: replace with however the rest of your app authenticates
  // (existing api client, axios instance, cookies, etc.).
  const token = localStorage.getItem('token')

  const response = await fetch(`${API_URL}/workouts/workoutPlan`, {
    headers: {
      'Content-Type': 'application/json',
      ...(token ? { Authorization: `Bearer ${token}` } : {}),
    },
  })

  if (!response.ok) {
    throw new Error(`Could not load your workout plan (${response.status}).`)
  }

  return response.json()
}