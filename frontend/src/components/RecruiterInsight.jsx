import IntelligencePulse from './IntelligencePulse'

export default function RecruiterInsight({ insight, githubBullets }) {
  if (!insight) return null

  return (
    <>
      <div className="recruiter-card">
        <div className="recruiter-card-eyebrow">
          <span className="material-icons-round" style={{ fontSize: '14px' }}>record_voice_over</span>
          Recruiter Intelligence
          <IntelligencePulse label="Live" />
        </div>
        <p className="recruiter-card-text">{insight}</p>
      </div>

      {githubBullets && githubBullets.length > 0 && (
        <div className="panel" style={{ marginTop: '16px' }}>
          <div className="panel-label">GitHub Project Bullets</div>
          <div className="panel-title" style={{ fontSize: '1rem', marginBottom: '16px' }}>
            Integrated GitHub Achievements
          </div>
          {githubBullets.map((b, i) => (
            <div key={i} className="bullet-item after-item">
              <span className="bullet-marker" style={{ color: 'var(--emerald)' }}>✦</span>
              {b}
            </div>
          ))}
        </div>
      )}
    </>
  )
}
