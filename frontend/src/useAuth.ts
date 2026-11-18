// useAuth
//
// Owns the login session: token in localStorage, login/logout, and a
// startup check against /me so a stale token doesn't show a broken app.
// The token is handed to useRobotControl to open the control WebSocket.

import { useCallback, useEffect, useState } from 'react'

const TOKEN_KEY = 'gabrino_token'
const USER_KEY = 'gabrino_user'
const HTTP_PORT = 5000

export type AuthState = 'checking' | 'anonymous' | 'authed'

function apiBase(): string {
  const host = window.location.hostname || 'localhost'
  return `http://${host}:${HTTP_PORT}`
}

export interface UseAuth {
  state: AuthState
  token: string | null
  username: string | null
  error: string | null
  pending: boolean
  login: (username: string, password: string) => Promise<void>
  logout: () => void
}

export function useAuth(): UseAuth {
  const [token, setToken] = useState<string | null>(() => localStorage.getItem(TOKEN_KEY))
  const [username, setUsername] = useState<string | null>(() => localStorage.getItem(USER_KEY))
  const [state, setState] = useState<AuthState>(() =>
    localStorage.getItem(TOKEN_KEY) ? 'checking' : 'anonymous',
  )
  const [error, setError] = useState<string | null>(null)
  const [pending, setPending] = useState(false)

  const logout = useCallback(() => {
    localStorage.removeItem(TOKEN_KEY)
    localStorage.removeItem(USER_KEY)
    setToken(null)
    setUsername(null)
    setState('anonymous')
  }, [])

  // Validate an existing token once on mount.
  useEffect(() => {
    const existing = localStorage.getItem(TOKEN_KEY)
    if (!existing) return
    let cancelled = false
    ;(async () => {
      try {
        const res = await fetch(`${apiBase()}/me`, {
          headers: { Authorization: `Bearer ${existing}` },
        })
        if (cancelled) return
        if (res.ok) {
          const body = await res.json()
          setUsername(body.username ?? null)
          setState('authed')
        } else {
          logout()
        }
      } catch {
        // Server unreachable — keep the token, let the app try the WS and
        // fall back to the login screen only on an explicit auth rejection.
        if (!cancelled) setState('authed')
      }
    })()
    return () => {
      cancelled = true
    }
  }, [logout])

  const login = useCallback(async (user: string, password: string) => {
    setPending(true)
    setError(null)
    try {
      const res = await fetch(`${apiBase()}/login`, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ username: user, password }),
      })
      if (!res.ok) {
        setError(res.status === 401 ? 'Invalid username or password' : `Login failed (${res.status})`)
        return
      }
      const body = await res.json()
      localStorage.setItem(TOKEN_KEY, body.token)
      localStorage.setItem(USER_KEY, body.username)
      setToken(body.token)
      setUsername(body.username)
      setState('authed')
    } catch {
      setError('Cannot reach server')
    } finally {
      setPending(false)
    }
  }, [])

  return { state, token, username, error, pending, login, logout }
}
