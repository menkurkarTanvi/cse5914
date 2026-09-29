import { useState } from 'react'
import type { FormEvent } from 'react'
import type { Page } from '../types'

type Props = {
  setPage: (page: Page) => void
  onLogin: () => void
}

function Login({ setPage, onLogin }: Props) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')

  function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    console.log({ email, password })

    onLogin()
  }

  return (
    <div className="auth-page">
      <div className="auth-card">
        <div className="brand-name">
          FitStack
        </div>

        <h1>Welcome back</h1>

        <p>
          Sign in to continue to your fitness plan.
        </p>

        <form onSubmit={handleSubmit}>
          <label>
            Email
            <input
              type="email"
              value={email}
              onChange={(event) =>
                setEmail(event.target.value)
              }
              required
            />
          </label>

          <label>
            Password
            <input
              type="password"
              value={password}
              onChange={(event) =>
                setPassword(event.target.value)
              }
              required
            />
          </label>

          <button
            className="gold-button full"
            type="submit"
          >
            Login
          </button>
        </form>

        <button
          className="text-button auth-link"
          onClick={() => setPage('signup')}
        >
          Don't have an account? Sign up
        </button>
      </div>
    </div>
  )
}

export default Login