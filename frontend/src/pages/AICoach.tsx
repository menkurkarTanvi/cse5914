import PageHeader from '../components/PageHeader'
import type { Exercise } from '../types'

type Props = {
  exercises: Exercise[]
  message: string
  setMessage: (message: string) => void
  chatReply: string
  sendMessage: () => void
}

function AICoach({
  exercises,
  message,
  setMessage,
  chatReply,
  sendMessage,
}: Props) {
  return (
    <>
      <PageHeader
        title="AI Coach"
        subtitle="Ask questions, swap exercises, and adapt your plan."
      />

      <section className="coach-grid">
        <div className="panel coach-context">
          <h2>Current workout</h2>

          <p className="gold-text">
            Monday — Push
          </p>

          <div className="compact-list">
            {exercises.map((exercise) => (
              <span key={exercise.name}>
                {exercise.name}
              </span>
            ))}
          </div>

          <h3>Quick actions</h3>

          <button
            className="outline-button"
            onClick={() =>
              setMessage('Swap an exercise')
            }
          >
            Swap an exercise
          </button>

          <button
            className="quick-button"
            onClick={() =>
              setMessage('Shorten my workout')
            }
          >
            Shorten workout
          </button>

          <button
            className="quick-button"
            onClick={() =>
              setMessage('Adjust difficulty')
            }
          >
            Adjust difficulty
          </button>
        </div>

        <div className="panel chat-panel">
          <div className="chat-history">
            <div className="user-message">
              I don't have a barbell today. What can I do instead?
            </div>

            <div className="ai-message">
              <strong>
                Try dumbbell bench press as the closest substitute.
              </strong>

              <span>
                Keep the same 3 sets and use 8–12 reps with a controlled tempo.
              </span>
            </div>

            {chatReply && (
              <div className="ai-message secondary">
                {chatReply}
              </div>
            )}
          </div>

          <div className="chat-input-row">
            <input
              value={message}
              onChange={(event) =>
                setMessage(event.target.value)
              }
              onKeyDown={(event) => {
                if (event.key === 'Enter') {
                  sendMessage()
                }
              }}
              placeholder="Ask FitStack anything about your plan..."
            />

            <button
              className="gold-button"
              onClick={sendMessage}
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