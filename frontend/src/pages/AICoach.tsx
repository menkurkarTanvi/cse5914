import { useCallback, useEffect, useLayoutEffect, useRef, useState, type ReactNode } from 'react'

import PageHeader from '../components/PageHeader'
import { fetchWorkoutPlan, type ApiWorkout } from '../api/workouts'
import { useCoachChat } from '../hooks/useCoachChat'

const QUICK_ACTIONS = [
  { label: 'Swap an exercise', message: 'Swap an exercise' },
  { label: 'Shorten workout', message: 'Shorten my workout' },
  { label: 'Adjust difficulty', message: "Adjust today's difficulty" },
]

// The same workout the coach works on (agent/nodes/context.py): one in
// progress, otherwise the next scheduled one from today on.
function currentWorkout(workouts: ApiWorkout[]): ApiWorkout | null {
  const inProgress = workouts.find((workout) => workout.status === 'in_progress')
  if (inProgress) {
    return inProgress
  }

  const now = new Date()
  const today = [
    now.getFullYear(),
    String(now.getMonth() + 1).padStart(2, '0'),
    String(now.getDate()).padStart(2, '0'),
  ].join('-')

  return (
    workouts
      .filter((workout) => workout.status === 'scheduled' && workout.scheduled_date >= today)
      .sort((a, b) => a.scheduled_date.localeCompare(b.scheduled_date))[0] ?? null
  )
}

// Replies use a little Markdown: **bold** and "* " bullets.
function renderReply(text: string): ReactNode {
  return text
    .split('\n')
    .filter((line) => line.trim())
    .map((line, lineIndex) => {
      const content = line.replace(/^\s*\*\s+/, '• ')
      const parts = content.split(/\*\*(.+?)\*\*/g)

      return (
        <span key={lineIndex}>
          {parts.map((part, partIndex) =>
            partIndex % 2 === 1
              ? <strong key={partIndex}>{part}</strong>
              : part,
          )}
        </span>
      )
    })
}

function AICoach({
  draft,
  onDraftUsed,
}: {
  // A message to start with in the text box, e.g. from a dashboard shortcut.
  draft: string
  onDraftUsed: () => void
}) {
  const [workout, setWorkout] = useState<ApiWorkout | null>(null)
  const [workoutStatus, setWorkoutStatus] = useState<'loading' | 'ready' | 'error'>('loading')
  const [message, setMessage] = useState(draft)
  const chatEndRef = useRef<HTMLDivElement>(null)
  const inputRef = useRef<HTMLTextAreaElement>(null)

  // Grow the text box with its content; CSS max-height caps it, after which
  // it scrolls.
  useLayoutEffect(() => {
    const input = inputRef.current
    if (!input) {
      return
    }
    input.style.height = 'auto'
    const borders = input.offsetHeight - input.clientHeight
    input.style.height = `${input.scrollHeight + borders}px`
  }, [message])

  // Use the draft once: focus the box with the cursor at the end, then clear
  // it so the next visit to this page starts empty.
  useEffect(() => {
    if (!draft) {
      return
    }
    const input = inputRef.current
    if (input) {
      input.focus()
      input.setSelectionRange(draft.length, draft.length)
    }
    onDraftUsed()
  }, [draft, onDraftUsed])

  const loadWorkout = useCallback(() => {
    fetchWorkoutPlan()
      .then((response) => {
        setWorkout(currentWorkout(response.workouts))
        setWorkoutStatus('ready')
      })
      .catch(() => setWorkoutStatus('error'))
  }, [])

  useEffect(() => {
    loadWorkout()
  }, [loadWorkout])

  const { turns, options, sending, error, send, reset, canEditLast, editLast } = useCoachChat({
    onPlanChanged: loadWorkout,
  })

  useEffect(() => {
    // Skip the empty chat, so opening the page doesn't jump to the bottom.
    if (turns.length > 0 || error) {
      chatEndRef.current?.scrollIntoView({ behavior: 'smooth', block: 'end' })
    }
  }, [turns, sending, error])

  function editLastMessage() {
    const text = editLast()
    if (text !== null) {
      setMessage(text)
      inputRef.current?.focus()
    }
  }

  async function sendTyped() {
    const text = message
    setMessage('')
    if (!(await send(text))) {
      setMessage(text)
    }
  }

  return (
    <>
      <PageHeader
        title="AI Coach"
        subtitle="Ask questions, swap exercises, and adapt your plan."
      />

      <section className="coach-grid">
        <div className="panel coach-context">
          <h2>Current workout</h2>

          {workoutStatus === 'loading' && <p>Loading your workout...</p>}

          {workoutStatus === 'error' && <p>Could not load your workout.</p>}

          {workoutStatus === 'ready' && !workout && (
            <p>No upcoming workout in your plan.</p>
          )}

          {workout && (
            <>
              <p className="gold-text">
                {workout.day_of_week}
                {workout.description ? ` — ${workout.description}` : ''}
              </p>

              <div className="compact-list">
                {workout.exercises.map((exercise) => (
                  <span key={exercise.id}>
                    {exercise.name} · {exercise.sets_planned} × {exercise.reps_min}–{exercise.reps_max}
                  </span>
                ))}
              </div>
            </>
          )}

          <h3>Quick actions</h3>

          {QUICK_ACTIONS.map((action, index) => (
            <button
              key={action.label}
              className={index === 0 ? 'outline-button' : 'quick-button'}
              disabled={sending}
              onClick={() => send(action.message)}
            >
              {action.label}
            </button>
          ))}

          {turns.length > 0 && (
            <button
              className="quick-button"
              disabled={sending}
              onClick={reset}
            >
              Start a new chat
            </button>
          )}
        </div>

        <div className="panel chat-panel">
          <div className="chat-history">
            {turns.length === 0 && (
              <div className="ai-message secondary">
                <span>
                  Ask me about today's workout, or tell me what you need: swap
                  an exercise, fit it into less time, or make it easier or harder.
                </span>
              </div>
            )}

            {turns.map((turn, index) =>
              turn.role === 'user'
                ? (
                  <div key={index} className="user-message">
                    {turn.content}
                    {canEditLast && index === turns.length - 2 && (
                      <button className="chat-edit" onClick={editLastMessage}>
                        Edit
                      </button>
                    )}
                  </div>
                )
                : (
                  <div key={index} className="ai-message">
                    {renderReply(turn.content)}
                    {turn.planChanged && (
                      <span className="chat-note">Workout updated</span>
                    )}
                  </div>
                ),
            )}

            {options.length > 0 && !sending && (
              <div className="swap-options">
                {options.map((option) => (
                  <button
                    key={option.number}
                    className="outline-button"
                    onClick={() => send(String(option.number))}
                  >
                    <strong>{option.number}. {option.name}</strong>
                    <span>{option.reason}</span>
                  </button>
                ))}
              </div>
            )}

            {sending && <div className="ai-message"><span>Thinking...</span></div>}

            {error && <div className="chat-error">{error}</div>}

            <div ref={chatEndRef} />
          </div>

          <div className="chat-input-row">
            <textarea
              ref={inputRef}
              rows={1}
              value={message}
              disabled={sending}
              maxLength={1000}
              onChange={(event) =>
                setMessage(event.target.value)
              }
              onKeyDown={(event) => {
                // Enter sends; Shift+Enter starts a new line. Skip while an
                // input method (e.g. for Chinese or Japanese) is composing.
                if (event.key === 'Enter' && !event.shiftKey && !event.nativeEvent.isComposing) {
                  event.preventDefault()
                  sendTyped()
                }
              }}
              placeholder="Ask FitStack anything about your plan..."
            />

            <button
              className="gold-button"
              disabled={sending || !message.trim()}
              onClick={sendTyped}
            >
              Send
            </button>
          </div>
        </div>
      </section>
    </>
  )
}

export default AICoach
