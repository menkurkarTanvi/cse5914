import type {
  AlternativeExercise,
  Exercise,
} from '../types'

export const initialExercises: Exercise[] = [
  {
    id: 'barbell-bench-press',
    name: 'Barbell Bench Press',
    sets: '3 × 8–10',
  },
  {
    id: 'incline-dumbbell-press',
    name: 'Incline Dumbbell Press',
    sets: '3 × 8–10',
  },
  {
    id: 'shoulder-press',
    name: 'Shoulder Press',
    sets: '3 × 10',
  },
  {
    id: 'lateral-raises',
    name: 'Lateral Raises',
    sets: '3 × 12–15',
  },
]

export const mockAlternatives: Record<
  string,
  AlternativeExercise[]
> = {
  'barbell-bench-press': [
    {
      exerciseId: 'dumbbell-bench-press',
      name: 'Dumbbell Bench Press',
      primaryMuscles: ['Chest'],
      equipmentRequired: ['Dumbbell'],
      reason:
        'Same horizontal push pattern with similar chest emphasis.',
    },
    {
      exerciseId: 'machine-chest-press',
      name: 'Machine Chest Press',
      primaryMuscles: ['Chest'],
      equipmentRequired: ['Machine'],
      reason:
        'Stable pressing alternative that targets the same primary muscle group.',
    },
  ],

  'incline-dumbbell-press': [
    {
      exerciseId: 'incline-machine-press',
      name: 'Incline Machine Press',
      primaryMuscles: ['Upper Chest'],
      equipmentRequired: ['Machine'],
      reason:
        'Keeps the incline pressing movement while using a more stable setup.',
    },
    {
      exerciseId: 'incline-push-up',
      name: 'Incline Push-Up',
      primaryMuscles: ['Chest'],
      equipmentRequired: ['Bench'],
      reason:
        'Bodyweight alternative that keeps a similar upper-body push pattern.',
    },
  ],

  'shoulder-press': [
    {
      exerciseId: 'arnold-press',
      name: 'Arnold Press',
      primaryMuscles: ['Shoulders'],
      equipmentRequired: ['Dumbbell'],
      reason:
        'Dumbbell overhead press variation with similar shoulder emphasis.',
    },
  ],

  'lateral-raises': [
    {
      exerciseId: 'cable-lateral-raise',
      name: 'Cable Lateral Raise',
      primaryMuscles: ['Shoulders'],
      equipmentRequired: ['Cable'],
      reason:
        'Targets the lateral deltoid with constant cable tension.',
    },
  ],
}