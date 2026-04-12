export default function ProjectSuggestions({ projects }) {
  if (!projects || projects.length === 0) return null

  return (
    <div className="panel">
      <div className="panel-label">Step 5 — Recommendations</div>
      <div className="panel-title">Project Suggestions</div>
      <div style={{ fontSize: '0.82rem', color: 'var(--on-surface-variant)', marginBottom: '20px' }}>
        Build these projects to close your skill gaps and strengthen your GitHub profile.
      </div>

      <div className="project-cards">
        {projects.map((proj, i) => (
          <div key={i} className="project-card">
            <div className="project-card-title">
              {i + 1}. {proj.title}
            </div>
            <div className="project-card-desc">{proj.description}</div>
            <div className="project-card-why">
              <span className="material-icons-round" style={{ fontSize: '12px', verticalAlign: 'middle', marginRight: '4px' }}>
                lightbulb
              </span>
              {proj.why_it_helps}
            </div>
            {proj.tech_stack && proj.tech_stack.length > 0 && (
              <div className="tech-tags">
                {proj.tech_stack.map((t, j) => (
                  <span key={j} className="tech-tag">{t}</span>
                ))}
              </div>
            )}
          </div>
        ))}
      </div>
    </div>
  )
}
