import { useState, useEffect } from 'react'
import './App.css'
import DownloadForm from './components/DownloadForm'
import ProgressDisplay from './components/ProgressDisplay'
import SummaryDisplay from './components/SummaryDisplay'

function dispatchRequest(input) {
  if (input.mode === 'tracklist-to-spotify') {
    return fetch('/api/tracklist-to-spotify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ tracklist: input.tracklist, name: input.name }),
    })
  }
  if (input.mode === 'spotify-to-download') {
    return fetch('/api/download-from-spotify', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ playlistUrl: input.playlistUrl }),
    })
  }
  // beatport (default)
  if (input.type === 'url') {
    return fetch('/api/download', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ url: input.value }),
    })
  }
  const formData = new FormData()
  formData.append('htmlFile', input.value)
  return fetch('/api/download', { method: 'POST', body: formData })
}

// The Beatport flow sends {type: 'stage'|'progress'|'summary'|'error'} directly.
// The Spotify flows send {type: 'event', tag, payload} and {type: 'log'|'done'};
// we translate those into the same progress/summary shape.
function handleStreamMessage(data, state, { setStage, setProgress, setSummary, setError, setIsDownloading }) {
  if (data.type === 'stage') {
    setStage({ stage: data.stage, message: data.message })
    return
  }
  if (data.type === 'progress') {
    setProgress(data.data)
    return
  }
  if (data.type === 'summary') {
    setSummary(data.data)
    return
  }
  if (data.type === 'error') {
    setError({ message: data.message, details: data.details, stage: data.stage, exitCode: data.exitCode })
    setIsDownloading(false)
    return
  }

  if (data.type === 'event') {
    const { tag, payload } = data
    if (tag === 'STAGE') {
      setStage({ stage: 'working', message: typeof payload === 'string' ? payload : '' })
    } else if (tag === 'TRACK_START') {
      setProgress({
        current: payload.index,
        total: payload.total,
        message: `Searching: ${payload.query}`,
        track: { name: payload.query },
      })
    } else if (tag === 'TRACK_RESULT') {
      state.trackResults.push(payload)
      const matchedLabel = payload.matched_name
        ? `${payload.matched_artists?.join(', ') || ''} – ${payload.matched_name}`
        : payload.filename || payload.query
      setProgress({
        current: payload.index,
        total: state.trackResults[0]?.total ?? payload.index,
        message: `[${payload.status}] ${matchedLabel}`,
        track: { name: matchedLabel, status: payload.status },
      })
    } else if (tag === 'PLAYLIST_CREATED') {
      state.playlist = payload
    } else if (tag === 'DOWNLOAD_FOLDER') {
      state.downloadFolder = payload
    } else if (tag === 'SUMMARY') {
      setSummary({
        ...payload,
        mode: state.mode,
        playlist: state.playlist,
        downloadFolder: state.downloadFolder,
        trackResults: state.trackResults,
      })
    }
    return
  }

  if (data.type === 'done') {
    if (data.exitCode && data.exitCode !== 0 && data.exitCode !== 2) {
      setError({ message: `Process exited with code ${data.exitCode}`, stage: 'subprocess', exitCode: data.exitCode })
      setIsDownloading(false)
    }
    return
  }
  // 'log' messages are ignored in the UI (they're in the server console)
}

export default function App() {
  const [isDownloading, setIsDownloading] = useState(false)
  const [progress, setProgress] = useState(null)
  const [summary, setSummary] = useState(null)
  const [error, setError] = useState(null)
  const [stage, setStage] = useState(null)

  const getCurrentPage = () => {
    if (error) return 'error'
    if (summary) return 'summary'
    if (isDownloading || progress) return 'progress'
    return 'home'
  }

  const resetToHome = () => {
    setIsDownloading(false)
    setProgress(null)
    setSummary(null)
    setError(null)
    setStage(null)
  }

  const handleDownload = async (input) => {
    setIsDownloading(true)
    setProgress(null)
    setSummary(null)
    setError(null)
    setStage(null)

    try {
      const response = await dispatchRequest(input)
      if (!response.ok) throw new Error('Failed to start download')

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''
      const eventState = { trackResults: [], playlist: null, mode: input.mode }

      while (true) {
        const { done, value } = await reader.read()
        if (done) break

        buffer += decoder.decode(value, { stream: true })
        const lines = buffer.split('\n')
        buffer = lines.pop()

        for (const line of lines) {
          if (!line) continue
          try {
            const data = JSON.parse(line)
            handleStreamMessage(data, eventState, { setStage, setProgress, setSummary, setError, setIsDownloading })
          } catch (e) {
            console.error('Parse error:', e, 'Line:', line)
          }
        }
      }
    } catch (err) {
      console.error('Download error:', err)
      setError({
        message: err.message || 'An unexpected error occurred',
        details: err.toString(),
        stage: 'client_error'
      })
      setIsDownloading(false)
    } finally {
      if (!error) {
        setIsDownloading(false)
      }
    }
  }

  const currentPage = getCurrentPage()

  return (
    <div className="app">
      <div className="container">
        <header className="header">
          <h1>Beatport Playlist Downloader</h1>
          <p className="subtitle">Download music from Beatport playlists to your computer</p>

          {currentPage !== 'error' && (
            <div className="page-indicator">
              <div className={`indicator-step ${currentPage === 'home' ? 'active' : currentPage !== 'home' ? 'completed' : ''}`}>
                <div className="step-number">1</div>
                <div className="step-label">Select Source</div>
              </div>
              <div className="indicator-line"></div>
              <div className={`indicator-step ${currentPage === 'progress' ? 'active' : currentPage === 'summary' ? 'completed' : ''}`}>
                <div className="step-number">2</div>
                <div className="step-label">Download</div>
              </div>
              <div className="indicator-line"></div>
              <div className={`indicator-step ${currentPage === 'summary' ? 'active' : ''}`}>
                <div className="step-number">3</div>
                <div className="step-label">Complete</div>
              </div>
            </div>
          )}
        </header>

        <main className="main">
          {currentPage === 'home' && (
            <DownloadForm onDownload={handleDownload} disabled={isDownloading} />
          )}

          {currentPage === 'progress' && (
            <ProgressDisplay progress={progress} isLoading={isDownloading} stage={stage} />
          )}

          {currentPage === 'summary' && (
            <SummaryDisplay summary={summary} onReset={resetToHome} />
          )}

          {currentPage === 'error' && (
            <div className="error-container">
              <div className="error-card">
                <div className="error-header">
                  <span className="error-icon">⚠</span>
                  <h2>Download Failed</h2>
                </div>
                <div className="error-body">
                  <p className="error-message">{typeof error === 'string' ? error : error.message}</p>
                  {error.stage && (
                    <p className="error-stage">
                      <strong>Failed at:</strong> {error.stage.replace(/_/g, ' ')}
                    </p>
                  )}
                  {error.exitCode && (
                    <p className="error-code">
                      <strong>Exit code:</strong> {error.exitCode}
                    </p>
                  )}
                  {error.details && (
                    <details className="error-details">
                      <summary>Technical Details</summary>
                      <pre>{error.details}</pre>
                    </details>
                  )}
                </div>
                <div className="error-actions">
                  <button onClick={resetToHome} className="btn-primary">
                    Back to Home
                  </button>
                </div>
              </div>
            </div>
          )}
        </main>

        <footer className="footer">
          <p>Powered by yt-dlp and SoundCloud</p>
        </footer>
      </div>
    </div>
  )
}
