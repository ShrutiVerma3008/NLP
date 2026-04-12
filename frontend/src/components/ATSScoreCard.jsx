import { useEffect, useRef } from 'react'

function getScoreColor(score) {
  if (score >= 75) return 'var(--emerald)'
  if (score >= 50) return 'var(--warning)'
  return 'var(--error)'
}

function getScoreLabel(score) {
  if (score >= 80) return 'Excellent Match'
  if (score >= 65) return 'Strong Match'
  if (score >= 50) return 'Moderate Match'
  return 'Needs Work'
}

export default function ATSScoreCard({ score, strengths }) {
  const fillRef = useRef()
  const R = 65
  const circumference = 2 * Math.PI * R
  const dashOffset = circumference - (score / 100) * circumference
  const color = getScoreColor(score)

  useEffect(() => {
    if (!fillRef.current) return
    // Animate on mount
    fillRef.current.style.strokeDashoffset = circumference
    fillRef.current.style.stroke = color
    const id = requestAnimationFrame(() => {
      fillRef.current.style.strokeDashoffset = dashOffset
    })
    return () => cancelAnimationFrame(id)
  }, [score, dashOffset, circumference, color])

  return (
    <div className="ats-score-card">
      {/* Score Ring */}
      <div className="score-ring-container">
        <svg className="score-ring-svg" viewBox="0 0 160 160">
          <circle className="score-track" cx="80" cy="80" r={R} />
          <circle
            ref={fillRef}
            className="score-fill"
            cx="80" cy="80" r={R}
            strokeDasharray={circumference}
            strokeDashoffset={circumference}
          />
        </svg>
        <div className="score-center">
          <div className="score-number" style={{ color }}>{score}</div>
          <div className="score-label">ATS Score</div>
        </div>
      </div>

      {/* Status */}
      <div style={{ textAlign: 'center' }}>
        <div style={{
          display: 'inline-block',
          background: `${color}15`,
          color,
          padding: '4px 16px',
          borderRadius: 'var(--r-pill)',
          fontSize: '0.78rem',
          fontWeight: 700,
          letterSpacing: '0.05em',
        }}>
          {getScoreLabel(score)}
        </div>
      </div>

      {/* Strengths */}
      {strengths && strengths.length > 0 && (
        <div className="ats-strengths" style={{ width: '100%' }}>
          <div className="panel-label">Top Strengths</div>
          {strengths.map((s, i) => (
            <div key={i} className="strength-item">
              <span className="strength-dot" />
              {s}
            </div>
          ))}
        </div>
      )}
    </div>
  )
}
