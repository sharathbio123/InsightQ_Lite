import React, { useEffect, useMemo, useRef, useState } from 'react'
import './App.css'
import { buildPipeline, chat, uploadFiles } from './api'

const STORAGE_KEYS = {
  theme: 'insightq-theme',
  history: 'insightq-chat-history',
}

const INITIAL_STATUS = {
  tone: 'idle',
  label: 'Ready to explore',
  message: 'Upload your PDFs and build the local RAG index to begin.',
}

function getStatusTone(status) {
  if (status?.tone === 'success') return 'success'
  if (status?.tone === 'error') return 'error'
  if (status?.tone === 'loading') return 'loading'
  return 'idle'
}

export default function App() {
  const [selectedFiles, setSelectedFiles] = useState([])
  const [uploadedFiles, setUploadedFiles] = useState([])
  const [status, setStatus] = useState(INITIAL_STATUS)
  const [chatHistory, setChatHistory] = useState([])
  const [input, setInput] = useState('')
  const [isUploading, setIsUploading] = useState(false)
  const [isBuilding, setIsBuilding] = useState(false)
  const [isSending, setIsSending] = useState(false)
  const [dragActive, setDragActive] = useState(false)
  const [theme, setTheme] = useState(() => localStorage.getItem(STORAGE_KEYS.theme) || 'dark')
  const chatRef = useRef(null)

  useEffect(() => {
    const storedHistory = localStorage.getItem(STORAGE_KEYS.history)
    if (storedHistory) {
      try {
        setChatHistory(JSON.parse(storedHistory))
      } catch {
        localStorage.removeItem(STORAGE_KEYS.history)
      }
    }
  }, [])

  useEffect(() => {
    if (chatRef.current) {
      chatRef.current.scrollTop = chatRef.current.scrollHeight
    }
  }, [chatHistory, isSending])

  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.theme, theme)
    document.body.setAttribute('data-theme', theme)
  }, [theme])

  useEffect(() => {
    localStorage.setItem(STORAGE_KEYS.history, JSON.stringify(chatHistory))
  }, [chatHistory])

  const statusTone = useMemo(() => getStatusTone(status), [status])

  function handleFileSelection(fileList) {
    const files = Array.from(fileList || [])
    const pdfs = files.filter((file) => file.type === 'application/pdf' || file.name.toLowerCase().endsWith('.pdf'))
    if (pdfs.length !== files.length) {
      setStatus({
        tone: 'error',
        label: 'Only PDFs supported',
        message: 'Please drop only PDF documents into the upload area.',
      })
    }
    setSelectedFiles(pdfs)
  }

  async function handleUpload() {
    if (!selectedFiles.length) {
      setStatus({
        tone: 'error',
        label: 'No files selected',
        message: 'Choose one or more PDFs before uploading.',
      })
      return
    }

    setIsUploading(true)
    setStatus({ tone: 'loading', label: 'Uploading PDFs', message: 'Sending your files to the backend…' })

    try {
      const data = await uploadFiles(selectedFiles)
      setUploadedFiles(data.saved || [])
      setStatus({
        tone: 'success',
        label: 'Upload complete',
        message: `Saved ${data.saved?.length || 0} file${(data.saved?.length || 0) === 1 ? '' : 's'} successfully.`,
      })
    } catch (error) {
      setStatus({
        tone: 'error',
        label: 'Upload failed',
        message: error.message,
      })
    } finally {
      setIsUploading(false)
    }
  }

  async function handleBuild() {
    setIsBuilding(true)
    setStatus({ tone: 'loading', label: 'Building index', message: 'Creating the vector index and preparing the AI pipeline…' })

    try {
      await buildPipeline()
      setStatus({
        tone: 'success',
        label: 'Pipeline ready',
        message: 'The RAG index is ready. You can ask questions now.',
      })
    } catch (error) {
      setStatus({
        tone: 'error',
        label: 'Build failed',
        message: error.message,
      })
    } finally {
      setIsBuilding(false)
    }
  }

  async function handleSend() {
    if (!input.trim()) return

    const trimmedInput = input.trim()
    const nextHistory = [...chatHistory, { role: 'human', content: trimmedInput }]
    setChatHistory(nextHistory)
    setInput('')
    setIsSending(true)
    setStatus({ tone: 'loading', label: 'Querying', message: 'Searching the indexed documents…' })

    try {
      const data = await chat({ input: trimmedInput, chat_history: chatHistory })
      const historyWithReply = [
        ...nextHistory,
        { role: 'ai', content: data.response || 'No response was returned.' },
      ]
      setChatHistory(historyWithReply)
      setStatus({
        tone: 'success',
        label: 'Answer ready',
        message: 'The assistant has responded using the retrieved context.',
      })
    } catch (error) {
      setStatus({
        tone: 'error',
        label: 'Chat failed',
        message: error.message,
      })
    } finally {
      setIsSending(false)
    }
  }

  function handleKeyDown(event) {
    if (event.key === 'Enter' && !event.shiftKey) {
      event.preventDefault()
      handleSend()
    }
  }

  return (
    <div className="app-shell">
      <div className="main-area">
        <header className="hero">
          <div>
            <p className="eyebrow">Local RAG Assistant</p>
            <h1>InsightQ</h1>
            <p>A local document assistant for Researchers. Upload research PDFs, build a local index, and ask questions in a more polished, interactive workspace.</p>
          </div>

          <div className="hero-actions">
            <div className="hero-actions__buttons">
              <button className="secondary-btn" onClick={() => setTheme(theme === 'dark' ? 'light' : 'dark')}>
                {theme === 'dark' ? '☀️ Light mode' : '🌙 Dark mode'}
              </button>
              <button
                className="secondary-btn"
                onClick={() => {
                  setChatHistory([])
                  localStorage.removeItem(STORAGE_KEYS.history)
                  setStatus({ tone: 'success', label: 'History cleared', message: 'Your conversation history has been reset.' })
                }}
              >
                Clear chat
              </button>
            </div>

            <div className="status-card">
              <div className={`status-pill ${statusTone}`}>{status.label}</div>
              <div>{status.message}</div>
            </div>
          </div>
        </header>

        <main className="content-grid">
          <section className="panel">
          <div className="panel-header">
            <h2>Upload & Build</h2>
            <span>{uploadedFiles.length ? `${uploadedFiles.length} file(s) ready` : 'No files yet'}</span>
          </div>

          <div
            className={`dropzone ${dragActive ? 'drag-active' : ''}`}
            onDragOver={(event) => {
              event.preventDefault()
              setDragActive(true)
            }}
            onDragLeave={() => setDragActive(false)}
            onDrop={(event) => {
              event.preventDefault()
              setDragActive(false)
              handleFileSelection(event.dataTransfer.files)
            }}
          >
            <input
              id="pdf-upload"
              type="file"
              accept="application/pdf"
              multiple
              onChange={(event) => handleFileSelection(event.target.files)}
              style={{ display: 'none' }}
            />
            <p>Drag and drop PDFs here</p>
            <label className="upload-btn" htmlFor="pdf-upload">
              Choose PDF files
            </label>
          </div>

          {selectedFiles.length > 0 && (
            <div className="file-list" aria-label="Selected files">
              {selectedFiles.map((file) => (
                <div className="file-pill" key={file.name}>
                  <span>{file.name}</span>
                  <small>{Math.round(file.size / 1024)} KB</small>
                </div>
              ))}
            </div>
          )}

          <div className="actions">
            <button className="primary-btn" onClick={handleUpload} disabled={isUploading || !selectedFiles.length}>
              {isUploading ? 'Uploading…' : 'Upload PDFs'}
            </button>
            <button className="secondary-btn" onClick={handleBuild} disabled={isBuilding}>
              {isBuilding ? 'Building…' : 'Build RAG Index'}
            </button>
          </div>

          <div className="helper-card">
            Tip: build the index after uploading PDFs so the backend can retrieve relevant context for your questions.
          </div>
          </section>

          <section className="panel">
          <div className="panel-header">
            <h2>Conversation</h2>
            <span>{chatHistory.length ? `${chatHistory.length} message(s)` : 'Start asking questions'}</span>
          </div>

          <div className="chat-window" ref={chatRef}>
            {chatHistory.length === 0 ? (
              <div className="chat-empty">
                <h3>No conversation yet</h3>
                <p>Upload your documents, build the index, and ask a question to get started.</p>
              </div>
            ) : (
              chatHistory.map((message, index) => (
                <div key={`${message.role}-${index}`} className={`chat-bubble ${message.role === 'human' ? 'user' : 'ai'}`}>
                  <strong>{message.role === 'human' ? 'You' : 'AI Assistant'}</strong>
                  {message.content}
                </div>
              ))
            )}
          </div>

          <div className="composer">
            <textarea
              value={input}
              onChange={(event) => setInput(event.target.value)}
              onKeyDown={handleKeyDown}
              placeholder="Ask a question about your PDFs..."
              rows={3}
            />
            <button className="send-btn" onClick={handleSend} disabled={isSending || !input.trim()}>
              {isSending ? 'Sending…' : 'Send'}
            </button>
          </div>

          <div className="status-message">{status.message}</div>
        </section>
        </main>
      </div>
    </div>
  )
}