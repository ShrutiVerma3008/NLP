import { useState, useRef } from 'react'

export default function UploadPanel({ onSubmit, isLoading }) {
  const [file, setFile] = useState(null)
  const [resumeText, setResumeText] = useState('')
  const [jobDescription, setJobDescription] = useState('')
  const [githubUsername, setGithubUsername] = useState('')
  const [dragging, setDragging] = useState(false)
  const [inputMode, setInputMode] = useState('file') // 'file' | 'text'
  const fileRef = useRef()

  const handleFile = (f) => {
    if (!f) return
    const ext = f.name.split('.').pop().toLowerCase()
    if (!['pdf', 'docx'].includes(ext)) {
      alert('Please upload a PDF or DOCX file.')
      return
    }
    setFile(f)
    setInputMode('file')
  }

  const handleDrop = (e) => {
    e.preventDefault()
    setDragging(false)
    const f = e.dataTransfer.files[0]
    handleFile(f)
  }

  const handleSubmit = (e) => {
    e.preventDefault()
    if (!jobDescription.trim()) {
      alert('Please enter a job description.')
      return
    }
    if (inputMode === 'file' && !file) {
      alert('Please upload a resume file or switch to text mode.')
      return
    }
    if (inputMode === 'text' && !resumeText.trim()) {
      alert('Please paste your resume text.')
      return
    }

    const formData = new FormData()
    if (inputMode === 'file') {
      formData.append('resume_file', file)
    } else {
      formData.append('resume_text', resumeText)
    }
    formData.append('job_description', jobDescription)
    if (githubUsername.trim()) {
      formData.append('github_username', githubUsername.trim())
    }
    onSubmit(formData)
  }

  return (
    <div className="panel full-span">
      <div className="panel-label">Step 1</div>
      <div className="panel-title">Upload Your Profile</div>

      <form onSubmit={handleSubmit}>
        {/* Mode Toggle */}
        <div className="mode-toggle-group" style={{ display: 'flex', gap: '8px', marginBottom: '16px' }}>
          <button
            type="button"
            className={`btn btn-secondary`}
            style={inputMode === 'file' ? { background: 'var(--emerald-subtle)', color: 'var(--emerald)' } : {}}
            onClick={() => setInputMode('file')}
          >
            <span className="material-icons-round" style={{ fontSize: '16px' }}>upload_file</span>
            Upload File
          </button>
          <button
            type="button"
            className="btn btn-secondary"
            style={inputMode === 'text' ? { background: 'var(--emerald-subtle)', color: 'var(--emerald)' } : {}}
            onClick={() => setInputMode('text')}
          >
            <span className="material-icons-round" style={{ fontSize: '16px' }}>text_snippet</span>
            Paste Text
          </button>
        </div>

        <div className="upload-grid" style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: '24px' }}>
          {/* Left column: Resume */}
          <div>
            <div className="form-group">
              <label className="form-label">Resume — PDF or DOCX</label>
              {inputMode === 'file' ? (
                <>
                  <div
                    className={`drop-zone ${dragging ? 'dragging' : ''}`}
                    onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
                    onDragLeave={() => setDragging(false)}
                    onDrop={handleDrop}
                    onClick={() => fileRef.current.click()}
                  >
                    <span className="material-icons-round drop-zone-icon">cloud_upload</span>
                    <div className="drop-zone-label">Drag & drop or click to browse</div>
                    <div className="drop-zone-sub">PDF, DOCX — up to 10MB</div>
                    <input
                      ref={fileRef}
                      type="file"
                      accept=".pdf,.docx"
                      onChange={(e) => handleFile(e.target.files[0])}
                      style={{ display: 'none' }}
                    />
                  </div>
                  {file && (
                    <div className="file-chip" style={{ marginTop: '12px' }}>
                      <span className="material-icons-round" style={{ fontSize: '14px' }}>description</span>
                      {file.name}
                      <button
                        type="button"
                        onClick={() => setFile(null)}
                        style={{ background: 'none', border: 'none', cursor: 'pointer', color: 'inherit', padding: 0, lineHeight: 1 }}
                      >
                        <span className="material-icons-round" style={{ fontSize: '14px' }}>close</span>
                      </button>
                    </div>
                  )}
                </>
              ) : (
                <textarea
                  rows={10}
                  placeholder="Paste your resume text here..."
                  value={resumeText}
                  onChange={(e) => setResumeText(e.target.value)}
                />
              )}
            </div>
          </div>

          {/* Right column: JD + GitHub */}
          <div>
            <div className="form-group">
              <label className="form-label">Job Description</label>
              <textarea
                rows={7}
                placeholder="Paste the full job description here..."
                value={jobDescription}
                onChange={(e) => setJobDescription(e.target.value)}
                required
              />
            </div>

            <div className="form-group">
              <label className="form-label">GitHub Username (optional)</label>
              <input
                type="text"
                placeholder="e.g. torvalds"
                value={githubUsername}
                onChange={(e) => setGithubUsername(e.target.value)}
              />
              <div style={{ fontSize: '0.72rem', color: 'var(--on-surface-variant)', marginTop: '6px' }}>
                We use GitIngest to analyze your public repositories
              </div>
            </div>
          </div>
        </div>

        <button
          type="submit"
          className="btn btn-primary btn-full"
          style={{ marginTop: '8px' }}
          disabled={isLoading}
        >
          {isLoading ? (
            <>
              <div className="loading-spinner" style={{ width: '16px', height: '16px', borderWidth: '2px' }} />
              Analyzing...
            </>
          ) : (
            <>
              <span className="material-icons-round" style={{ fontSize: '18px' }}>auto_awesome</span>
              Optimize My Resume
            </>
          )}
        </button>
      </form>
    </div>
  )
}
