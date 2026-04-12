export async function analyzeResume(formData) {
  const response = await fetch('/api/analyze', {
    method: 'POST',
    body: formData,
  })

  if (!response.ok) {
    const err = await response.json().catch(() => ({ detail: 'Server error' }))
    throw new Error(err.detail || `HTTP ${response.status}`)
  }

  return response.json()
}
