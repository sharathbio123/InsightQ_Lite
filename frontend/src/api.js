const API_BASE = process.env.REACT_APP_API_BASE || '/api'

async function request(path, options = {}) {
  const res = await fetch(`${API_BASE}${path}`, options)
  const payload = await res.json().catch(() => ({}))

  if (!res.ok) {
    throw new Error(payload.error || `Request failed with status ${res.status}`)
  }

  return payload
}

export async function uploadFiles(files) {
  const fd = new FormData()
  for (let i = 0; i < files.length; i++) fd.append('files', files[i])
  return request('/upload', { method: 'POST', body: fd })
}

export async function buildPipeline() {
  return request('/build', { method: 'POST' })
}

export async function chat(payload) {
  return request('/chat', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  })
}

export { API_BASE }
