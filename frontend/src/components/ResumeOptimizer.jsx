import IntelligencePulse from './IntelligencePulse'

export default function ResumeOptimizer({ originalBullets, optimizedBullets, improvements }) {
  return (
    <div className="panel">
      <div className="panel-label">Step 4 — AI Enhancement</div>
      <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '20px' }}>
        <div className="panel-title" style={{ margin: 0 }}>Bullet Point Rewrite</div>
        <IntelligencePulse label="Live Optimization" />
      </div>

      {/* Before / After */}
      <div className="bullets-comparison">
        {/* Before */}
        <div>
          <div className="bullets-col-label before">
            <span className="material-icons-round" style={{ fontSize: '14px' }}>remove_circle_outline</span>
            Original
          </div>
          {originalBullets && originalBullets.length > 0 ? (
            originalBullets.map((b, i) => (
              <div key={i} className="bullet-item before-item">
                <span className="bullet-marker">—</span>
                {b}
              </div>
            ))
          ) : (
            <div className="text-muted text-sm">No bullets extracted</div>
          )}
        </div>

        {/* After */}
        <div>
          <div className="bullets-col-label after">
            <span className="material-icons-round" style={{ fontSize: '14px' }}>auto_awesome</span>
            AI Optimized
          </div>
          {optimizedBullets && optimizedBullets.length > 0 ? (
            optimizedBullets.map((b, i) => (
              <div key={i} className="bullet-item after-item">
                <span className="bullet-marker" style={{ color: 'var(--emerald)' }}>✦</span>
                {b}
              </div>
            ))
          ) : (
            <div className="text-muted text-sm">No optimized bullets yet</div>
          )}
        </div>
      </div>

      {/* Key Improvements */}
      {improvements && improvements.length > 0 && (
        <div style={{ marginTop: '24px', paddingTop: '20px', borderTop: '1px solid rgba(198,198,205,0.15)' }}>
          <div className="panel-label" style={{ marginBottom: '12px' }}>Key Improvements Made</div>
          <div className="improvements-list">
            {improvements.map((imp, i) => (
              <div key={i} className="improvement-item">
                <span className="material-icons-round improvement-check">check_circle</span>
                {imp}
              </div>
            ))}
          </div>
        </div>
      )}
    </div>
  )
}
