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

function loadChat(): SavedChat {
  try {
    const saved = sessionStorage.getItem(STORAGE_KEY)
    return saved ? JSON.parse(saved) : EMPTY_CHAT
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
  const [sending, setSending] = useState(false)
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

    setSending(true)
    setError(null)
    // Show the message right away. Swap options belong to the previous reply,
    // so hide them while waiting.
    setChat((current) => ({
      ...current,
      turns: [...current.turns, { role: 'user', content: message }],
      options: [],
    }))

    try {
      const response = await chatWithCoach({
        message,
        history,
        pendingAction: chat.pendingAction,
      })

      setChat((current) => ({
        turns: [
          ...current.turns,
          {
            role: 'assistant',
            content: response.reply,
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
      // Undo the optimistic message, so history never holds a user turn
      // without a reply. The pending action is kept, so the user can retry.
      setChat((current) => ({
        ...current,
        turns: current.turns.slice(0, -1),
        options: chat.options,
      }))
      setError(err instanceof Error ? err.message : 'The AI coach could not answer.')
      return false
    } finally {
      setSending(false)
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
    sending,
    error,
    send,
    reset,
    canEditLast,
    editLast,
  }
}
