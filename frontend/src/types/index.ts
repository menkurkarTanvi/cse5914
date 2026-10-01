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
  name: string
  sets: string
}