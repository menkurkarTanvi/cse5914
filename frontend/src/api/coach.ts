import { API_URL, authHeaders } from './client'

// Server limits on history (schemas/coach.py). Breaking either one makes
// every later request fail with 422.
const MAX_HISTORY_TURNS = 50
const MAX_TURN_LENGTH = 4000

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
      history: history
        .map((turn) => ({ ...turn, content: turn.content.trim().slice(0, MAX_TURN_LENGTH) }))
        .filter((turn) => turn.content)
        .slice(-MAX_HISTORY_TURNS),
      pending_action: pendingAction,
    }),
  })

  if (!response.ok) {
    throw new CoachError(await errorMessage(response), response.status)
  }

  return response.json()
}
