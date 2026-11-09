import { useEffect, useState } from 'react'

import {
  chatWithCoach,
  type ChatTurn,
  type SwapOption,
} from '../api/coach'

export type CoachChatTurn = ChatTurn & {
  // Set on the coach's reply that changed today's workout.
  planChanged?: boolean
}

type CoachFollowUp = {
  pendingAction: string | null
  options: SwapOption[]
}

type SavedChat = CoachFollowUp & {
  turns: CoachChatTurn[]
  // The pending action and options from before the last exchange, so the
  // user can edit their last message and resend it.
  previous?: CoachFollowUp | null
}

// Kept in sessionStorage so the chat survives switching pages. Cleared on
// login and logout so one user never sees another's conversation.
const STORAGE_KEY = 'coachChat'

const EMPTY_CHAT: SavedChat = {
  turns: [],
  pendingAction: null,
  options: [],
  previous: null,
}

// Shown when the coach sends back no text (e.g. Gemini blocked its answer).
// The server rejects empty history turns, so a blank reply must never be kept.
const EMPTY_REPLY = "Sorry, I couldn't answer that. Could you rephrase it?"

function loadChat(): SavedChat {
  try {
    const saved = JSON.parse(sessionStorage.getItem(STORAGE_KEY) ?? 'null')
    // Anything unexpected (an older format, a manual edit) starts a new chat
    // instead of crashing the page.
    if (
      !Array.isArray(saved?.turns) ||
      !Array.isArray(saved?.options) ||
      !(typeof saved.pendingAction === 'string' || saved.pendingAction === null)
    ) {
      return EMPTY_CHAT
    }
    return saved
  } catch {
    return EMPTY_CHAT
  }
}

export function clearCoachChat() {
  try {
    sessionStorage.removeItem(STORAGE_KEY)
  } catch {
    // Storage unavailable; nothing to clear.
  }
}

export function useCoachChat({ onPlanChanged }: { onPlanChanged: () => void }) {
  const [chat, setChat] = useState<SavedChat>(loadChat)
  // The message waiting for a reply. Kept out of the saved chat, so leaving
  // the page mid-request never saves a message without its reply.
  const [inFlight, setInFlight] = useState<string | null>(null)
  const sending = inFlight !== null
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    try {
      sessionStorage.setItem(STORAGE_KEY, JSON.stringify(chat))
    } catch {
      // Storage unavailable; the chat still works for this visit.
    }
  }, [chat])

  // Sends one message. Returns false if it failed, so the caller can put the
  // text back in the input.
  async function send(text: string): Promise<boolean> {
    const message = text.trim()
    if (!message || sending) {
      return false
    }

    const history = chat.turns.map(({ role, content }) => ({ role, content }))

    setInFlight(message)
    setError(null)

    try {
      const response = await chatWithCoach({
        message,
        history,
        pendingAction: chat.pendingAction,
      })

      // The message and its reply are saved together, only once the reply
      // has arrived.
      setChat((current) => ({
        turns: [
          ...current.turns,
          { role: 'user', content: message },
          {
            role: 'assistant',
            content: response.reply.trim() || EMPTY_REPLY,
            planChanged: response.plan_changed,
          },
        ],
        pendingAction: response.pending_action,
        options: response.options,
        previous: {
          pendingAction: chat.pendingAction,
          options: chat.options,
        },
      }))

      if (response.plan_changed) {
        onPlanChanged()
      }

      return true
    } catch (err) {
      // Nothing was saved, and the pending action and options are unchanged,
      // so the user can simply retry.
      setError(err instanceof Error ? err.message : 'The AI coach could not answer.')
      return false
    } finally {
      setInFlight(null)
    }
  }

  function reset() {
    setChat(EMPTY_CHAT)
    setError(null)
  }

  // Only the last message can be edited, and not once its reply changed the
  // workout: that change is already saved, and editing can't undo it.
  const lastReply = chat.turns[chat.turns.length - 1]
  const canEditLast = Boolean(
    !sending &&
    chat.previous &&
    lastReply?.role === 'assistant' &&
    !lastReply.planChanged,
  )

  // Removes the last message and its reply and restores what the coach was
  // waiting for before it. Returns the message text to put back in the input.
  function editLast(): string | null {
    if (!canEditLast || !chat.previous) {
      return null
    }

    const text = chat.turns[chat.turns.length - 2].content
    setChat({
      turns: chat.turns.slice(0, -2),
      ...chat.previous,
      // One level only: the exchange before this one can't be edited.
      previous: null,
    })
    setError(null)
    return text
  }

  return {
    turns: chat.turns,
    options: chat.options,
    inFlight,
    sending,
    error,
    send,
    reset,
    canEditLast,
    editLast,
  }
}
