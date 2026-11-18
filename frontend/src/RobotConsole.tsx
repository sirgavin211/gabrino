import { useState } from 'react'
import { useRobotControl, type Direction, type ConnectionStatus } from './useRobotControl'
import SerialMonitor from './SerialMonitor'
import { MicIcon, MicOffIcon, SpeakerIcon, SpeakerOffIcon } from './icons'

const STATUS_LABEL: Record<ConnectionStatus, string> = {
  connecting: 'Connecting',
  live: 'Live',
  offline: 'Offline',
}

const KEYCAPS: Array<{ key: string; dir: Direction }> = [
  { key: 'W', dir: 'forward' },
  { key: 'A', dir: 'left' },
  { key: 'S', dir: 'reverse' },
  { key: 'D', dir: 'right' },
]

interface RobotConsoleProps {
  token: string
  username: string | null
  onLogout: () => void
}

export default function RobotConsole({ token, username, onLogout }: RobotConsoleProps) {
  const { status, direction, lastCommand, logs, sendCommand, speed, incSpeed, decSpeed } =
    useRobotControl({
      token,
      onAuthFail: onLogout,
    })

  // Local audio intent — simulated toggles (no wire effect yet).
  const [micOn, setMicOn] = useState(false)
  const [speakerOn, setSpeakerOn] = useState(true)

  return (
    <div className="app">
      <header className="topbar">
        <div className="brand">
          <span className="brand-mark" aria-hidden="true" />
          <h1>Gabrino</h1>
          <span className="brand-sub mono">v7 · desktop robot</span>
        </div>

        <div className="topbar-right">
          <div className={`status-pill status-${status}`} role="status" aria-live="polite">
            <span className="status-dot" aria-hidden="true" />
            <span className="mono">{STATUS_LABEL[status]}</span>
            {lastCommand && (
              <>
                <span className="status-divider" aria-hidden="true" />
                <span className="mono dim">{lastCommand}</span>
              </>
            )}
          </div>

          {username && <span className="user-chip mono">{username}</span>}
          <button type="button" className="logout-btn mono" onClick={onLogout}>
            Sign out
          </button>
        </div>
      </header>

      <div className="workspace">
        {/* Left: camera feed, pinned toward the top. */}
        <section className="col-left">
          <div className="camera-feed">
            <div className="camera-frame">
              <div className="ph-grid" aria-hidden="true" />
              <div className="ph-label mono">CAMERA FEED</div>
              <div className="ph-sub mono">awaiting stream · SVGA 800×600</div>

              {direction !== 'brake' && (
                <div className={`dir-badge dir-${direction}`}>
                  <span className="mono">{direction.toUpperCase()}</span>
                </div>
              )}
            </div>
          </div>
        </section>

        {/* Right: control panel. */}
        <aside className="col-right">
          <div className="panel">
            <div className="panel-head">
              <span className="panel-title mono">Control Panel</span>
            </div>

            {/* Audio toggles. */}
            <div className="audio-row">
              <button
                type="button"
                className={`audio-btn ${micOn ? 'on' : 'off'}`}
                aria-pressed={micOn}
                onClick={() => setMicOn((v) => !v)}
                title={micOn ? 'Mic live — click to mute' : 'Mic muted — click to talk'}
              >
                {micOn ? <MicIcon /> : <MicOffIcon />}
                <span className="audio-label">{micOn ? 'Talking' : 'Muted'}</span>
              </button>

              <button
                type="button"
                className={`audio-btn ${speakerOn ? 'on' : 'off'}`}
                aria-pressed={speakerOn}
                onClick={() => setSpeakerOn((v) => !v)}
                title={speakerOn ? 'Audio on — click to mute output' : 'Audio muted — click to hear'}
              >
                {speakerOn ? <SpeakerIcon /> : <SpeakerOffIcon />}
                <span className="audio-label">{speakerOn ? 'Sound On' : 'Sound Off'}</span>
              </button>
            </div>

            {/* Serial monitor. */}
            <SerialMonitor logs={logs} onSend={sendCommand} />
          </div>
        </aside>
      </div>

      <footer className="hint-rail">
        <div className="hint-cluster">
          <span className="hint-label">Move</span>
          <div className="keypad">
            {KEYCAPS.map((k) => (
              <kbd
                key={k.key}
                className={`keycap ${direction === k.dir ? 'keycap-active' : ''}`}
              >
                {k.key}
              </kbd>
            ))}
          </div>
        </div>

        <div className="hint-cluster">
          <span className="hint-label">Stop</span>
          <kbd className={`keycap keycap-wide ${direction === 'brake' ? 'keycap-active' : ''}`}>
            release keys
          </kbd>
        </div>

        <div className="hint-cluster">
          <span className="hint-label">Speed</span>
          <div className="speed-control">
            <button
              type="button"
              className="speed-btn"
              onClick={decSpeed}
              disabled={speed <= 0}
              aria-label="Decrease speed"
            >
              −
            </button>
            <span className="speed-value mono">{speed}</span>
            <button
              type="button"
              className="speed-btn"
              onClick={incSpeed}
              disabled={speed >= 10}
              aria-label="Increase speed"
            >
              +
            </button>
          </div>
        </div>

        <div className="hint-cluster hint-meta">
          <span className="mono dim">ws://{window.location.hostname || 'localhost'}:8765</span>
          <span className="status-divider" aria-hidden="true" />
          <span className="mono dim">latest:</span>
          <span className="mono">{lastCommand ?? '—'}</span>
        </div>
      </footer>
    </div>
  )
}
