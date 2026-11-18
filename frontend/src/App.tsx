import { useAuth } from './useAuth'
import Login from './Login'
import RobotConsole from './RobotConsole'
import './App.css'

function App() {
  const { state, token, username, error, pending, login, logout } = useAuth()

  // Brief validation window while an existing token is checked.
  if (state === 'checking') {
    return (
      <div className="login-screen">
        <div className="login-card">
          <div className="login-brand">
            <span className="brand-mark" aria-hidden="true" />
            <h1>Gabrino</h1>
          </div>
          <p className="login-sub mono">Restoring session…</p>
        </div>
      </div>
    )
  }

  // Gate: no valid session -> login screen. Always sign in first.
  if (state !== 'authed' || !token) {
    return <Login onSubmit={login} error={error} pending={pending} />
  }

  return <RobotConsole token={token} username={username} onLogout={logout} />
}

export default App
