import { useState } from 'react'
import type { FormEvent } from 'react'
import type { Page } from '../types'

type Props = {
  setPage: (page: Page) => void
}

function SignUp({ setPage }: Props) {
  const [name, setName] = useState('')
  const [email, setEmail] = useState('')
  const [password, setPassword] = useState('')
  const [confirmPassword, setConfirmPassword] =
    useState('')
  const [error, setError] = useState('')

  async function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()
    setError('')

    if (password !== confirmPassword) {
      setError('Passwords do not match.')
      return
    }

    try {
      const response = await fetch(
        'http://localhost:8000/users/register',
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
        setError(
          data.detail ||
            'Sign up failed. Please try again.',
        )
        return
      }

      setPage('login')
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

        <h1>Create account</h1>

        <p>
          Create your account and start building your plan.
        </p>

        <form onSubmit={handleSubmit}>
          <label>
            Name
            <input
              value={name}
              onChange={(event) =>
                setName(event.target.value)
              }
              required
            />
          </label>

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

          <label>
            Confirm password
            <input
              type="password"
              value={confirmPassword}
              onChange={(event) =>
                setConfirmPassword(
                  event.target.value,
                )
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
            type="submit"
            className="gold-button full"
          >
            Sign Up
          </button>
        </form>

        <button
          className="text-button auth-link"
          onClick={() => setPage('login')}
        >
          Already have an account? Login
        </button>
      </div>
    </div>
  )
}

export default SignUp