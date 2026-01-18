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

  const handleDownload = async (input) => {
    setIsDownloading(true)
    setProgress(null)
    setSummary(null)
    setError(null)

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
            if (data.type === 'progress') {
              setProgress(data.data)
            } else if (data.type === 'summary') {
              setSummary(data.data)
            } else if (data.type === 'error') {
              setError(data.message)
            }
          } catch (e) {
            console.log('Parse error:', e)
          }
        }
      }
    } catch (err) {
      setError(err.message || 'An error occurred')
      console.error('Download error:', err)
    } finally {
      setIsDownloading(false)
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
          {!isDownloading && !progress && !summary && (
            <DownloadForm onDownload={handleDownload} disabled={isDownloading} />
          )}

          {(isDownloading || progress) && (
            <ProgressDisplay progress={progress} isLoading={isDownloading} />
          )}

          {summary && (
            <SummaryDisplay summary={summary} onReset={() => {
              setSummary(null)
              setProgress(null)
            }} />
          )}

          {error && (
            <div className="error-banner">
              <div className="error-content">
                <span className="error-icon">⚠</span>
                <p>{error}</p>
                <button onClick={() => setError(null)} className="error-close">×</button>
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
