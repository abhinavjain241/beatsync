import { useState } from 'react'
import './DownloadForm.css'

export default function DownloadForm({ onDownload, disabled }) {
  const [url, setUrl] = useState('')
  const [isLoading, setIsLoading] = useState(false)

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!url.trim()) return

    setIsLoading(true)
    try {
      await onDownload(url)
    } finally {
      setIsLoading(false)
    }
  }

  const isValidUrl = url.includes('beatport.com')

  return (
    <form onSubmit={handleSubmit} className="download-form">
      <div className="form-group">
        <label htmlFor="url" className="label">Beatport Playlist URL</label>
        <input
          id="url"
          type="text"
          value={url}
          onChange={(e) => setUrl(e.target.value)}
          placeholder="https://www.beatport.com/chart/..."
          disabled={disabled || isLoading}
          className="input"
        />
        {url && !isValidUrl && (
          <p className="input-hint warning">Please enter a valid Beatport URL</p>
        )}
      </div>

      <button
        type="submit"
        disabled={disabled || isLoading || !url.trim() || !isValidUrl}
        className="button button-primary"
      >
        {isLoading ? (
          <>
            <span className="spinner"></span>
            Starting Download...
          </>
        ) : (
          'Download Playlist'
        )}
      </button>

      <div className="form-info">
        <p>Enter a Beatport playlist URL and we'll download all tracks as MP3 files.</p>
        <ul>
          <li>Searches for each track on SoundCloud</li>
          <li>Saves files as Artist - Track.mp3</li>
          <li>Automatically skips already downloaded tracks</li>
        </ul>
      </div>
    </form>
  )
}
