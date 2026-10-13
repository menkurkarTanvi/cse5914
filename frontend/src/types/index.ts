export type Page =
  | 'login'
  | 'signup'
  | 'dashboard'
  | 'plan'
  | 'progress'
  | 'coach'
  | 'nutrition'
  | 'profile'

export type Exercise = {
  id: string
  name: string
  sets: string
}

export type AlternativeExercise = {
  exerciseId: string
  name: string
  primaryMuscles: string[]
  equipmentRequired: string[]
  reason: string
}

export type WorkoutFeedback =
  | 'great'
  | 'too_easy'
  | 'too_hard'

export type LoggedSet = {
  reps: string
  weight: string
}