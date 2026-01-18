import { useState, useEffect } from 'react'
import './App.css'
import DownloadForm from './components/DownloadForm'
import ProgressDisplay from './components/ProgressDisplay'
import SummaryDisplay from './components/SummaryDisplay'

export default function App() {
  const [isDownloading, setIsDownloading] = useState(false)
  const [progress, setProgress] = useState(null)
  const [summary, setSummary] = useState(null)
  const [error, setError] = useState(null)
  const [stage, setStage] = useState(null)

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
      let response

      if (input.type === 'url') {
        response = await fetch('/api/download', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ url: input.value })
        })
      } else {
        const formData = new FormData()
        formData.append('htmlFile', input.value)

        response = await fetch('/api/download', {
          method: 'POST',
          body: formData
        })
      }

      if (!response.ok) {
        throw new Error('Failed to start download')
      }

      const reader = response.body.getReader()
      const decoder = new TextDecoder()
      let buffer = ''

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
            console.log('[RECEIVED]', data)

            if (data.type === 'stage') {
              setStage({
                stage: data.stage,
                message: data.message
              })
              console.log('[STAGE]', data.stage, data.message)
            } else if (data.type === 'progress') {
              setProgress(data.data)
            } else if (data.type === 'summary') {
              setSummary(data.data)
            } else if (data.type === 'error') {
              console.error('[ERROR RECEIVED]', data)
              setError({
                message: data.message,
                details: data.details,
                stage: data.stage,
                exitCode: data.exitCode
              })
              setIsDownloading(false)
            }
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

  return (
    <div className="app">
      <div className="container">
        <header className="header">
          <h1>Beatport Playlist Downloader</h1>
          <p className="subtitle">Download music from Beatport playlists to your computer</p>
        </header>

        <main className="main">
          {!isDownloading && !progress && !summary && !error && (
            <DownloadForm onDownload={handleDownload} disabled={isDownloading} />
          )}

          {(isDownloading || progress) && !error && (
            <ProgressDisplay progress={progress} isLoading={isDownloading} stage={stage} />
          )}

          {summary && !error && (
            <SummaryDisplay summary={summary} onReset={resetToHome} />
          )}

          {error && (
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
