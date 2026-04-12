export default function SkillGapPanel({ skillGaps }) {
  if (!skillGaps || skillGaps.length === 0) {
    return (
      <div className="panel">
        <div className="panel-label">Skill Gap Analysis</div>
        <div className="text-muted text-sm" style={{ marginTop: '8px' }}>No skill gaps identified.</div>
      </div>
    )
  }

  const HIGH   = skillGaps.filter(s => s.severity === 'high')
  const MEDIUM = skillGaps.filter(s => s.severity === 'medium')
  const LOW    = skillGaps.filter(s => s.severity === 'low')

  return (
    <div className="panel">
      <div className="panel-label">Step 6 — Gaps</div>
      <div className="panel-title">Skill Gap Analysis</div>

      {HIGH.length > 0 && (
        <div style={{ marginBottom: '16px' }}>
          <div style={{ fontSize: '0.72rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--error)', marginBottom: '8px' }}>
            🔴 Critical
          </div>
          <div className="skill-gaps-grid">
            {HIGH.map((s, i) => (
              <div key={i} className="skill-pill high" title={s.description}>
                <span className="skill-pill-dot" />
                {s.skill}
              </div>
            ))}
          </div>
        </div>
      )}

      {MEDIUM.length > 0 && (
        <div style={{ marginBottom: '16px' }}>
          <div style={{ fontSize: '0.72rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--warning)', marginBottom: '8px' }}>
            🟡 Moderate
          </div>
          <div className="skill-gaps-grid">
            {MEDIUM.map((s, i) => (
              <div key={i} className="skill-pill medium" title={s.description}>
                <span className="skill-pill-dot" />
                {s.skill}
              </div>
            ))}
          </div>
        </div>
      )}

      {LOW.length > 0 && (
        <div>
          <div style={{ fontSize: '0.72rem', fontWeight: 600, textTransform: 'uppercase', letterSpacing: '0.08em', color: 'var(--on-surface-variant)', marginBottom: '8px' }}>
            🟢 Minor
          </div>
          <div className="skill-gaps-grid">
            {LOW.map((s, i) => (
              <div key={i} className="skill-pill low" title={s.description}>
                <span className="skill-pill-dot" />
                {s.skill}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
