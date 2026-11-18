// SerialMonitor
//
// Arduino IDE Serial Monitor look-alike: a scrolling, auto-following log
// pane on top of a command input row. Enter or "Send" submits.

import { useEffect, useRef, useState } from 'react'
import type { LogEntry } from './useRobotControl'

const KIND_PREFIX: Record<LogEntry['kind'], string> = {
  out: '>>',
  in: '<<',
  sys: '::',
}

function stamp(ts: number): string {
  const d = new Date(Math.ceil(ts / 1000) * 1000) // round up to whole second
  const p = (n: number) => String(n).padStart(2, '0')
  return `${p(d.getHours())}:${p(d.getMinutes())}:${p(d.getSeconds())}`
}

interface SerialMonitorProps {
  logs: LogEntry[]
  onSend: (text: string) => void
}

export default function SerialMonitor({ logs, onSend }: SerialMonitorProps) {
  const [input, setInput] = useState('')
  const [autoscroll, setAutoscroll] = useState(true)
  const viewRef = useRef<HTMLDivElement>(null)

  // Follow the tail while autoscroll is on.
  useEffect(() => {
    if (autoscroll && viewRef.current) {
      viewRef.current.scrollTop = viewRef.current.scrollHeight
    }
  }, [logs, autoscroll])

  const submit = (e: React.FormEvent) => {
    e.preventDefault()
    if (!input.trim()) return
    onSend(input)
    setInput('')
  }

  return (
    <div className="serial">
      <div className="serial-head">
        <span className="serial-title mono">Serial Monitor</span>
        <label className="serial-toggle mono">
          <input
            type="checkbox"
            checked={autoscroll}
            onChange={(e) => setAutoscroll(e.target.checked)}
          />
          Autoscroll
        </label>
      </div>

      <div className="serial-view" ref={viewRef}>
        {logs.length === 0 && (
          <div className="serial-line serial-empty mono">— waiting for data —</div>
        )}
        {logs.map((l) => (
          <div key={l.id} className={`serial-line serial-${l.kind} mono`}>
            <span className="serial-ts">{stamp(l.ts)}</span>
            <span className="serial-arrow">{KIND_PREFIX[l.kind]}</span>
            <span className="serial-text">{l.text}</span>
          </div>
        ))}
      </div>

      <form className="serial-input-row" onSubmit={submit}>
        <input
          className="serial-input mono"
          type="text"
          value={input}
          onChange={(e) => setInput(e.target.value)}
          placeholder="Type command, press Enter"
          spellCheck={false}
          autoComplete="off"
        />
        <button className="serial-send" type="submit">
          Send
        </button>
      </form>
    </div>
  )
}
