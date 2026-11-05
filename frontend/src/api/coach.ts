const API_URL = import.meta.env.VITE_API_URL ?? 'http://localhost:8000'

// The server rejects more than 50 history turns (schemas/coach.py).
const MAX_HISTORY_TURNS = 50

export type ChatTurn = {
  role: 'user' | 'assistant'
  content: string
}

export type SwapOption = {
  number: number
  exercise_id: string
  name: string
  equipment_required: string[]
  reason: string
}

export type CoachIntent =
  | 'exercise_question'
  | 'swap_exercise'
  | 'shorten_workout'
  | 'adjust_difficulty'
  | 'confirm'
  | 'decline'
  | 'other'

export type CoachChatResponse = {
  reply: string
  intent: CoachIntent
  // True when the coach is waiting for an answer: swap options, a yes/no
  // proposal, or a question about missing details.
  needs_follow_up: boolean
  options: SwapOption[]
  // Opaque; send it back unchanged with the next message.
  pending_action: string | null
  // True when today's workout changed; refetch the plan.
  plan_changed: boolean
}

export class CoachError extends Error {
  status: number

  constructor(message: string, status: number) {
    super(message)
    this.name = 'CoachError'
    this.status = status
  }
}

// Same as in workouts.ts. Could move to a shared api/client.ts.
function authHeaders(): HeadersInit {
  const token = localStorage.getItem('token')

  return {
    'Content-Type': 'application/json',
    ...(token
      ? { Authorization: `Bearer ${token}` }
      : {}),
  }
}

async function errorMessage(response: Response): Promise<string> {
  if (response.status === 401) {
    return 'Your session expired. Please log in again.'
  }

  try {
    const body = await response.json()
    // 503s carry a message written for the user; 422s carry a list.
    if (typeof body.detail === 'string') {
      return body.detail
    }
  } catch {
    // Not JSON, e.g. a bare 500 page.
  }

  return `The AI coach couldn't answer (${response.status}). Please try again.`
}

export async function chatWithCoach({
  message,
  history,
  pendingAction,
}: {
  message: string
  history: ChatTurn[]
  pendingAction: string | null
}): Promise<CoachChatResponse> {
  const response = await fetch(`${API_URL}/coach/chat`, {
    method: 'POST',
    headers: authHeaders(),
    body: JSON.stringify({
      message,
      history: history.slice(-MAX_HISTORY_TURNS),
      pending_action: pendingAction,
    }),
  })

  if (!response.ok) {
    throw new CoachError(await errorMessage(response), response.status)
  }

  return response.json()
}
