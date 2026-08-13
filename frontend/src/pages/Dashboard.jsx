import { useState } from 'react'
import Sidebar from '../components/Sidebar'
import UploadPanel from '../components/UploadPanel'
import ATSScoreCard from '../components/ATSScoreCard'
import ResumeOptimizer from '../components/ResumeOptimizer'
import SkillGapPanel from '../components/SkillGapPanel'
import ProjectSuggestions from '../components/ProjectSuggestions'
import RecruiterInsight from '../components/RecruiterInsight'
import { analyzeResume } from '../hooks/useAnalyze'

const LOADING_STEPS = [
  { icon: 'description',  text: 'Parsing resume document...' },
  { icon: 'work',         text: 'Extracting job requirements...' },
  { icon: 'hub',          text: 'Fetching GitHub data via GitIngest...' },
  { icon: 'auto_awesome', text: 'Running Gemini 2.5 Flash analysis...' },
  { icon: 'analytics',    text: 'Calculating ATS score...' },
  { icon: 'edit_note',    text: 'Rewriting resume bullets...' },
]

const TABS = [
  { id: 'ats',        label: 'ATS Score',      icon: 'analytics' },
  { id: 'comparison', label: 'Comparison',     icon: 'compare' },
  { id: 'gaps',       label: 'Skill Gaps',     icon: 'psychology' },
  { id: 'projects',   label: 'Projects',       icon: 'architecture' },
  { id: 'feedback',   label: 'Feedback',       icon: 'forum' },
]

export default function Dashboard() {
  const [results, setResults]     = useState(null)
  const [isLoading, setIsLoading] = useState(false)
  const [error, setError]         = useState(null)
  const [activeTab, setActiveTab] = useState('ats')

  const handleSubmit = async (formData) => {
    setIsLoading(true)
    setError(null)
    setResults(null)
    try {
      const data = await analyzeResume(formData)
      if (data.error) throw new Error(data.error)
      setResults(data)
      setActiveTab('ats')
    } catch (err) {
      setError(err.message)
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <div className="app-layout">
      <Sidebar activeTab={activeTab} setActiveTab={setActiveTab} />
      <main className="main-content">
        {/* Page Header */}
        <div className="page-header">
          <div className="page-header-eyebrow">Precision Optimization</div>
          <h1 className="page-title">AI Resume Intelligence Engine</h1>
          <p className="page-subtitle">
            Optimize your resume using AI, ATS insights, and GitHub intelligence to stand out in the modern tech landscape.
          </p>
        </div>

      {/* Upload Panel — always visible at top */}
      <div style={{ padding: '32px 64px 0' }}>
        <UploadPanel onSubmit={handleSubmit} isLoading={isLoading} />
      </div>

      {/* Error */}
      {error && (
        <div style={{
          margin: '16px 64px',
          padding: '16px 20px',
          background: 'rgba(186,26,26,0.08)',
          borderRadius: 'var(--r-lg)',
          color: 'var(--error)',
          fontSize: '0.875rem',
          display: 'flex',
          gap: '8px',
          alignItems: 'center'
        }}>
          <span className="material-icons-round" style={{ fontSize: '18px' }}>error_outline</span>
          {error}
        </div>
      )}

      {/* Loading */}
      {isLoading && (
        <div className="loading-overlay">
          <div className="loading-spinner" />
          <div className="loading-steps">
            {LOADING_STEPS.map((step, i) => (
              <div key={i} className="loading-step" style={{ animationDelay: `${i * 0.4}s` }}>
                <span className="material-icons-round" style={{ fontSize: '16px', color: 'var(--emerald)' }}>{step.icon}</span>
                {step.text}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty State */}
      {!isLoading && !results && !error && (
        <div className="intro-state">
          <span className="material-icons-round intro-icon">auto_awesome</span>
          <div className="intro-title">Ready to optimize your career</div>
          <p className="intro-sub">
            Upload your resume and paste a job description above. Our AI will analyze, score, and rewrite your profile to maximize ATS match and recruiter impact.
          </p>
        </div>
      )}

      {/* Results */}
      {results && !isLoading && (
        <>
          {/* Tab Navigation */}
          <div className="tab-nav" style={{ padding: '0 64px', background: 'var(--surface-white)', borderBottom: '1px solid rgba(198,198,205,0.2)' }}>
            {TABS.map(tab => (
              <button
                key={tab.id}
                className={`tab-btn ${activeTab === tab.id ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
              >
                <span className="material-icons-round" style={{ fontSize: '16px' }}>{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </div>

          {/* Tab Content */}
          <div style={{ padding: '32px 64px 64px' }}>

            {/* ATS Score Tab */}
            {activeTab === 'ats' && (
              <div style={{ display: 'grid', gridTemplateColumns: '280px 1fr', gap: '24px', alignItems: 'start' }}>
                <ATSScoreCard
                  score={results.ats_score ?? 0}
                  strengths={results.top_strengths}
                />
                <RecruiterInsight
                  insight={results.recruiter_insight}
                  githubBullets={results.github_integration}
                />
              </div>
            )}

            {/* Comparison Tab */}
            {activeTab === 'comparison' && (
              <div style={{ display: 'flex', flexDirection: 'column', gap: '24px' }}>
                <ResumeOptimizer
                  originalBullets={results.original_bullets}
                  optimizedBullets={results.optimized_bullets}
                  improvements={results.key_improvements}
                />
                {results.optimized_resume && (
                  <div className="panel">
                    <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '16px' }}>
                      <div>
                        <div className="panel-label">Full Optimized Resume</div>
                        <div className="panel-title" style={{ marginBottom: 0 }}>ATS-Ready Version</div>
                      </div>
                      <button
                        className="btn btn-secondary"
                        onClick={() => {
                          const blob = new Blob([results.optimized_resume], { type: 'text/plain' })
                          const url = URL.createObjectURL(blob)
                          const a = document.createElement('a')
                          a.href = url
                          a.download = 'optimized_resume.txt'
                          a.click()
                        }}
                      >
                        <span className="material-icons-round" style={{ fontSize: '16px' }}>download</span>
                        Download
                      </button>
                    </div>
                    <div className="optimized-resume">{results.optimized_resume}</div>
                  </div>
                )}
              </div>
            )}

            {/* Skill Gaps Tab */}
            {activeTab === 'gaps' && (
              <SkillGapPanel skillGaps={results.skill_gaps} />
            )}

            {/* Projects Tab */}
            {activeTab === 'projects' && (
              <ProjectSuggestions projects={results.project_suggestions} />
            )}

            {/* Feedback Tab */}
            {activeTab === 'feedback' && (
              <div className="panel">
                <div className="panel-label">Recruiter Feedback</div>
                <div className="panel-title">Full Analysis Summary</div>
                <div style={{ marginTop: '16px', display: 'flex', flexDirection: 'column', gap: '16px' }}>
                  {results.key_improvements && results.key_improvements.map((imp, i) => (
                    <div key={i} className="improvement-item">
                      <span className="material-icons-round improvement-check">check_circle</span>
                      {imp}
                    </div>
                  ))}
                </div>
                {results.recruiter_insight && (
                  <div style={{ marginTop: '24px' }}>
                    <div className="recruiter-card">
                      <div className="recruiter-card-eyebrow">
                        <span className="material-icons-round" style={{ fontSize: '14px' }}>record_voice_over</span>
                        Recruiter Insight
                      </div>
                      <p className="recruiter-card-text">{results.recruiter_insight}</p>
                    </div>
                  </div>
                )}
              </div>
            )}
          </div>
        </>
      )}
      </main>
    </div>
  )
}

