// Inline SVG icons — no external assets (CSP-safe). Stroke inherits
// currentColor so button state drives the color.

const base = {
  width: 22,
  height: 22,
  viewBox: '0 0 24 24',
  fill: 'none',
  stroke: 'currentColor',
  strokeWidth: 1.8,
  strokeLinecap: 'round' as const,
  strokeLinejoin: 'round' as const,
}

export function MicIcon() {
  return (
    <svg {...base} aria-hidden="true">
      <rect x="9" y="2" width="6" height="12" rx="3" />
      <path d="M5 10a7 7 0 0 0 14 0" />
      <line x1="12" y1="17" x2="12" y2="22" />
      <line x1="8" y1="22" x2="16" y2="22" />
    </svg>
  )
}

export function MicOffIcon() {
  return (
    <svg {...base} aria-hidden="true">
      <path d="M9 5a3 3 0 0 1 6 0v4" />
      <path d="M15 12.4A3 3 0 0 1 9 11V9" />
      <path d="M5 10a7 7 0 0 0 10.9 5.8M19 10a7 7 0 0 1-.6 2.8" />
      <line x1="12" y1="17" x2="12" y2="22" />
      <line x1="8" y1="22" x2="16" y2="22" />
      <line x1="3" y1="2" x2="21" y2="22" />
    </svg>
  )
}

export function SpeakerIcon() {
  return (
    <svg {...base} aria-hidden="true">
      <path d="M4 9v6h4l5 4V5L8 9H4z" />
      <path d="M16.5 8.5a5 5 0 0 1 0 7" />
      <path d="M19 6a8 8 0 0 1 0 12" />
    </svg>
  )
}

export function SpeakerOffIcon() {
  return (
    <svg {...base} aria-hidden="true">
      <path d="M4 9v6h4l5 4V5L8 9H4z" />
      <line x1="16" y1="9" x2="21" y2="14" />
      <line x1="21" y1="9" x2="16" y2="14" />
    </svg>
  )
}
