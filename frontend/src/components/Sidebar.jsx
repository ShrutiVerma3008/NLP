import { useLocation, useNavigate } from 'react-router-dom'

const NAV_ITEMS = [
  { icon: 'analytics',        label: 'ATS Score',   id: 'ats' },
  { icon: 'compare',          label: 'Comparison',  id: 'comparison' },
  { icon: 'psychology',       label: 'Skill Gaps',  id: 'gaps' },
  { icon: 'architecture',     label: 'Projects',    id: 'projects' },
  { icon: 'forum',            label: 'Feedback',    id: 'feedback' },
]

const BOTTOM_ITEMS = [
  { icon: 'help_outline',     label: 'Support',     id: 'support' },
  { icon: 'logout',           label: 'Sign Out',    id: 'signout' },
]

export default function Sidebar({ activeTab, setActiveTab }) {
  return (
    <aside className="sidebar">
      {/* Brand */}
      <div className="sidebar-brand">
        <div className="sidebar-brand-icon">
          <span className="material-icons-round" style={{ fontSize: '18px' }}>auto_awesome</span>
        </div>
        <div>
          <div className="sidebar-brand-text">AI RIS</div>
          <div className="sidebar-brand-sub">Intelligence Engine</div>
        </div>
      </div>

      {/* Primary Nav */}
      <nav className="sidebar-nav">
        <div className="sidebar-section-label">Analysis</div>
        {NAV_ITEMS.map(item => (
          <button
            key={item.id}
            className={`sidebar-item ${activeTab === item.id ? 'active' : ''}`}
            onClick={() => setActiveTab && setActiveTab(item.id)}
            style={{ background: 'none', border: 'none', width: '100%', textAlign: 'left' }}
          >
            <span className="material-icons-round sidebar-icon">{item.icon}</span>
            {item.label}
          </button>
        ))}
      </nav>

      {/* Bottom */}
      <div className="sidebar-bottom">
        {BOTTOM_ITEMS.map(item => (
          <button
            key={item.id}
            className="sidebar-item"
            style={{ background: 'none', border: 'none', width: '100%', textAlign: 'left' }}
          >
            <span className="material-icons-round sidebar-icon">{item.icon}</span>
            {item.label}
          </button>
        ))}
      </div>
    </aside>
  )
}
