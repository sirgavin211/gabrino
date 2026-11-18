// Login screen — shown until the user has a valid session.

import { useState } from 'react'

interface LoginProps {
  onSubmit: (username: string, password: string) => void
  error: string | null
  pending: boolean
}

export default function Login({ onSubmit, error, pending }: LoginProps) {
  const [username, setUsername] = useState('')
  const [password, setPassword] = useState('')

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!username || !password || pending) return
    onSubmit(username, password)
  }

  return (
    <div className="login-screen">
      <form className="login-card" onSubmit={submit}>
        <div className="login-brand">
          <span className="brand-mark" aria-hidden="true" />
          <h1>Gabrino</h1>
        </div>
        <p className="login-sub mono">Sign in to control the robot</p>

        <label className="login-field">
          <span className="login-label mono">Username</span>
          <input
            className="login-input mono"
            type="text"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            autoComplete="username"
            autoFocus
            spellCheck={false}
          />
        </label>

        <label className="login-field">
          <span className="login-label mono">Password</span>
          <input
            className="login-input mono"
            type="password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            autoComplete="current-password"
          />
        </label>

        {error && <div className="login-error mono">{error}</div>}

        <button className="login-submit" type="submit" disabled={pending}>
          {pending ? 'Signing in…' : 'Sign In'}
        </button>
      </form>
    </div>
  )
}
