export default function IntelligencePulse({ label = 'AI Optimized' }) {
  return (
    <span className="intelligence-pulse">
      <span className="pulse-dot" />
      <span className="pulse-label">{label}</span>
    </span>
  )
}
