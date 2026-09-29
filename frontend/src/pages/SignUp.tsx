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

  function handleSubmit(
    event: FormEvent<HTMLFormElement>,
  ) {
    event.preventDefault()

    if (password !== confirmPassword) {
      alert('Passwords do not match')
      return
    }

    console.log({
      name,
      email,
      password,
    })

    setPage('login')
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
                setConfirmPassword(event.target.value)
              }
              required
            />
          </label>

          <button
            className="gold-button full"
            type="submit"
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