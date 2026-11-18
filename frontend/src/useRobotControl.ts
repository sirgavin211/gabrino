// useRobotControl
//
// Owns the WebSocket connection to the Gabrino server, routes
// keyboard input into movement commands per the firmware contract:
//
//   {"type":"movement","direction":"forward|reverse|left|right|brake"}
//
// Semantics:
// - WASD map to forward/reverse/left/right on keydown
// - On keyup, recompute the current "active" key. If any key still
//   held -> send that direction. If none -> send "brake".
// - "Latest press wins" means the most recently pressed key whose
//   keyup has not yet fired is the active direction. We track
//   insertion order via Map (insertion-order preserved), and replace
//   the entry on re-press so the latest press jumps to the back.
// - Key auto-repeats from the OS are filtered (event.repeat) — we only
//   react to the initial press edge.
// - One WS message per press event and per release event. Direction
//   changes only; nothing is sent while the key is held still.

import { useEffect, useRef, useState } from 'react'

export type Direction = 'forward' | 'reverse' | 'left' | 'right' | 'brake'

export type ConnectionStatus = 'connecting' | 'live' | 'offline'

// Serial-monitor log line. `kind` drives color: out = we sent, in = server
// sent, sys = connection/system event.
export type LogKind = 'in' | 'out' | 'sys'
export interface LogEntry {
  id: number
  ts: number
  kind: LogKind
  text: string
}

const MAX_LOGS = 250

const KEY_TO_DIRECTION: Record<string, Direction> = {
  w: 'forward',
  a: 'left',
  s: 'reverse',
  d: 'right',
}

const WS_PORT = 8765
const BASE_RETRY_MS = 500
const MAX_RETRY_MS = 5000

const SPEED_MIN = 0
const SPEED_MAX = 10
const SPEED_DEFAULT = 5

function endpoint(token: string): string {
  const host = window.location.hostname || 'localhost'
  return `ws://${host}:${WS_PORT}?token=${encodeURIComponent(token)}`
}

export interface UseRobotControl {
  status: ConnectionStatus
  direction: Direction
  lastCommand: Direction | null
  logs: LogEntry[]
  sendCommand: (text: string) => void
  speed: number
  incSpeed: () => void
  decSpeed: () => void
}

export interface UseRobotControlOptions {
  token: string
  onAuthFail?: () => void
}

export function useRobotControl({ token, onAuthFail }: UseRobotControlOptions): UseRobotControl {
  const [status, setStatus] = useState<ConnectionStatus>('connecting')
  const [direction, setDirection] = useState<Direction>('brake')
  const [lastCommand, setLastCommand] = useState<Direction | null>(null)
  const [logs, setLogs] = useState<LogEntry[]>([])
  const logIdRef = useRef(0)
  const [speed, setSpeed] = useState(SPEED_DEFAULT)
  const speedRef = useRef(SPEED_DEFAULT)

  // Keep token + auth-fail callback in refs so the once-installed socket
  // handlers always read current values.
  const tokenRef = useRef(token)
  tokenRef.current = token
  const onAuthFailRef = useRef(onAuthFail)
  onAuthFailRef.current = onAuthFail

  // Append a serial-monitor line, capped to MAX_LOGS.
  const pushLog = (kind: LogKind, text: string) => {
    setLogs((prev) => {
      const next = [...prev, { id: logIdRef.current++, ts: Date.now(), kind, text }]
      return next.length > MAX_LOGS ? next.slice(-MAX_LOGS) : next
    })
  }

  // Mutable refs for socket + scheduler + ephemeral state.
  // Held keys are tracked here so keyboard handlers can read/write without
  // triggering renders.
  const wsRef = useRef<WebSocket | null>(null)
  const retryRef = useRef<number>(BASE_RETRY_MS)
  const reconnectTimerRef = useRef<number | null>(null)
  const heldRef = useRef<Map<string, Direction>>(new Map())
  const lastSentRef = useRef<Direction>('brake')

  // Imperative send — closes over current socket. Skips no-op sends so we
  // don't spam the wire during rapid key flutters that resolve to the same
  // direction.
  const send = (next: Direction) => {
    setDirection(next)
    setLastCommand(next)
    lastSentRef.current = next
    const ws = wsRef.current
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'movement', direction: next }))
    }
  }

  // Send an arbitrary command string from the serial monitor input.
  const sendCommand = (text: string) => {
    const trimmed = text.trim()
    if (!trimmed) return
    const ws = wsRef.current
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(trimmed)
      pushLog('out', trimmed)
    } else {
      pushLog('sys', 'not connected — command dropped')
    }
  }

  // Push the current speed level (0-10) to the robot.
  const sendSpeed = (level: number) => {
    const clamped = Math.max(SPEED_MIN, Math.min(SPEED_MAX, level))
    speedRef.current = clamped
    setSpeed(clamped)
    const ws = wsRef.current
    if (ws && ws.readyState === WebSocket.OPEN) {
      ws.send(JSON.stringify({ type: 'speed', level: clamped }))
    }
  }
  const incSpeed = () => sendSpeed(speedRef.current + 1)
  const decSpeed = () => sendSpeed(speedRef.current - 1)

  // Compute the currently active direction (latest held key) or 'brake'.
  const resolveActive = (): Direction => {
    const held = heldRef.current
    if (held.size === 0) return 'brake'
    let active: Direction = 'brake'
    for (const dir of held.values()) active = dir
    return active
  }

  // Try to (re)open the socket. Resets retry on success.
  const openSocket = () => {
    if (
      wsRef.current &&
      (wsRef.current.readyState === WebSocket.OPEN ||
        wsRef.current.readyState === WebSocket.CONNECTING)
    ) {
      return
    }

    setStatus('connecting')
    let socket: WebSocket
    try {
      socket = new WebSocket(endpoint(tokenRef.current))
    } catch {
      scheduleReconnect()
      return
    }
    wsRef.current = socket

    socket.addEventListener('open', () => {
      retryRef.current = BASE_RETRY_MS
      setStatus('live')
      pushLog('sys', `connected ws://${window.location.hostname || 'localhost'}:${WS_PORT}`)
      // Re-broadcast current direction + speed in case the server missed prior events.
      send(resolveActive())
      sendSpeed(speedRef.current)
    })

    socket.addEventListener('close', (event) => {
      setStatus('offline')
      wsRef.current = null
      // 4001 = server rejected our token. Stop retrying and sign out.
      if (event.code === 4001) {
        pushLog('sys', 'unauthorized — signing out')
        onAuthFailRef.current?.()
        return
      }
      pushLog('sys', 'disconnected — retrying')
      scheduleReconnect()
    })

    socket.addEventListener('error', () => {
      // 'close' will fire after this; let reconnect logic live there.
    })

    socket.addEventListener('message', (event) => {
      // Log text frames only; binary audio chunks would flood the monitor.
      if (typeof event.data !== 'string') return
      // Skip movement frames the server relays back — not useful in the log.
      try {
        if (JSON.parse(event.data)?.type === 'movement') return
      } catch {
        // non-JSON — fall through and log it
      }
      pushLog('in', event.data)
    })
  }

  const scheduleReconnect = () => {
    if (reconnectTimerRef.current != null) return
    const delay = retryRef.current
    retryRef.current = Math.min(MAX_RETRY_MS, delay * 2)
    reconnectTimerRef.current = window.setTimeout(() => {
      reconnectTimerRef.current = null
      openSocket()
    }, delay)
  }

  // Connect on mount, tear down on unmount.
  useEffect(() => {
    openSocket()
    return () => {
      if (reconnectTimerRef.current != null) {
        window.clearTimeout(reconnectTimerRef.current)
        reconnectTimerRef.current = null
      }
      const ws = wsRef.current
      if (ws) {
        ws.close()
        wsRef.current = null
      }
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  // Keyboard listener — installed once. Reads/writes refs so stale closures
  // are not possible. The active direction is recomputed from heldRef.current
  // and only broadcast if it differs from lastSentRef.current.
  useEffect(() => {
    const normalizeKey = (key: string): string => key.toLowerCase()

    // True when focus is in a text field (e.g. the serial monitor input) so
    // typing "wasd" doesn't drive the robot.
    const isTyping = (target: EventTarget | null): boolean => {
      const el = target as HTMLElement | null
      if (!el) return false
      const tag = el.tagName
      return tag === 'INPUT' || tag === 'TEXTAREA' || el.isContentEditable
    }

    const onKeyDown = (event: KeyboardEvent) => {
      if (event.repeat) return
      if (isTyping(event.target)) return
      const key = normalizeKey(event.key)
      // Speed nudge: '+'/'=' up, '-'/'_' down. One step per press.
      if (key === '+' || key === '=') {
        incSpeed()
        return
      }
      if (key === '-' || key === '_') {
        decSpeed()
        return
      }
      const dir = KEY_TO_DIRECTION[key]
      if (!dir) return
      const held = heldRef.current
      // Re-insertion moves the key to the back so it is the latest press.
      held.delete(key)
      held.set(key, dir)
      const active = resolveActive()
      if (active !== lastSentRef.current) send(active)
    }

    const onKeyUp = (event: KeyboardEvent) => {
      const key = normalizeKey(event.key)
      const held = heldRef.current
      if (!held.has(key)) return
      held.delete(key)
      const active = resolveActive()
      if (active !== lastSentRef.current) send(active)
    }

    window.addEventListener('keydown', onKeyDown)
    window.addEventListener('keyup', onKeyUp)
    return () => {
      window.removeEventListener('keydown', onKeyDown)
      window.removeEventListener('keyup', onKeyUp)
    }
    // eslint-disable-next-line react-hooks/exhaustive-deps
  }, [])

  return { status, direction, lastCommand, logs, sendCommand, speed, incSpeed, decSpeed }
}
