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
  status: string
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

export type ApiAlternativeExercise = {
  exercise_id: string
  name: string
  primary_muscles: string[]
  equipment_required: string[]
  reason: string
}

export type AlternativesResponse = {
  current: {
    exercise_id: string
    name: string
  }
  alternatives: ApiAlternativeExercise[]
}

export type CompleteWorkoutPayload = {
  exercises: Array<{
    workout_plan_exercise_id: string
    sets: Array<{
      set_number: number
      reps: number
      weight: number | null
      weight_unit: string
      rpe?: number | null
    }>
  }>
  feedback: {
    difficulty: 'too_easy' | 'great' | 'too_hard'
  }
}

function authHeaders(): HeadersInit {
  const token = localStorage.getItem('token')

  return {
    'Content-Type': 'application/json',
    ...(token
      ? { Authorization: `Bearer ${token}` }
      : {}),
  }
}

export async function fetchWorkoutPlan(): Promise<WorkoutPlanResponse> {
  // TODO: replace with however the rest of your app authenticates
  // (existing api client, axios instance, cookies, etc.).
  const response = await fetch(`${API_URL}/workouts/workoutPlan`, {
    headers: authHeaders(),
  })

  if (!response.ok) {
    throw new Error(`Could not load your workout plan (${response.status}).`)
  }

  return response.json()
}

export async function fetchExerciseAlternatives(
  workoutPlanExerciseId: string,
  limit = 5,
): Promise<AlternativesResponse> {
  const response = await fetch(
    `${API_URL}/workouts/exercises/${workoutPlanExerciseId}/alternatives?limit=${limit}`,
    {
      headers: authHeaders(),
    },
  )

  if (!response.ok) {
    throw new Error(
      'Could not load alternative exercises.',
    )
  }

  return response.json()
}

export async function applyExerciseSwap(
  workoutPlanExerciseId: string,
  exerciseId: string,
): Promise<ApiWorkoutExercise> {
  const response = await fetch(
    `${API_URL}/workouts/exercises/${workoutPlanExerciseId}/swap`,
    {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify({
        exercise_id: exerciseId,
        apply_to: 'this_workout',
      }),
    },
  )

  if (!response.ok) {
    throw new Error(
      'Could not swap the exercise.',
    )
  }

  return response.json()
}

export async function completeWorkout(
  workoutId: string,
  payload: CompleteWorkoutPayload,
) {
  const response = await fetch(
    `${API_URL}/workouts/${workoutId}/complete`,
    {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(payload),
    },
  )

  if (!response.ok) {
    throw new Error(
      'Could not save the workout.',
    )
  }

  return response.json()
}

export async function skipWorkout(
  workoutId: string,
  reason?: string,
) {
  const response = await fetch(
    `${API_URL}/workouts/${workoutId}/skip`,
    {
      method: 'POST',
      headers: authHeaders(),
      body: JSON.stringify(
        reason ? { reason } : {},
      ),
    },
  )

  if (!response.ok) {
    throw new Error(
      'Could not mark workout incomplete.',
    )
  }

  return response.json()
}