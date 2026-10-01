import { useState } from 'react'
import type { FormEvent } from 'react'
import type { Page } from '../types'

type Props = {
  setPage: (page: Page) => void
  onLogin: (token: string) => void
}

function Login({ setPage, onLogin }: Props) {
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [error, setError] = useState('')

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()
    setError('')

    try {
      const response = await fetch(
        'http://localhost:8000/users/login',
        {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({
            email,
            password,
          }),
        },
      )

      const data = await response.json()

      if (!response.ok) {
        setError(data.detail || 'Login failed.')
        return
      }

      onLogin(data.token)
    } catch (error) {
      console.error(error)
      setError(
        'Could not connect to the backend.',
      )
    }
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

          {error && (
            <p className="auth-error">
              {error}
            </p>
          )}

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