const rawBase = import.meta.env.VITE_API_URL || ''
const API_BASE_URL = rawBase.replace(/\/$/, '')

export async function analyzeResume(formData) {
  const response = await fetch(`${API_BASE_URL}/api/analyze`, {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: 'Server error' }))
    throw new Error(err.detail || `HTTP ${response.status}`)
  }

  return response.json()
}

