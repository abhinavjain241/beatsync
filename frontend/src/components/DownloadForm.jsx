import { useState } from 'react'
import './DownloadForm.css'

export default function DownloadForm({ onDownload, disabled }) {
  const [url, setUrl] = useState('')
  const [htmlFile, setHtmlFile] = useState(null)
  const [inputType, setInputType] = useState('url')
  const [isLoading, setIsLoading] = useState(false)
  const [fileType, setFileType] = useState('html')

  const handleSubmit = async (e) => {
    e.preventDefault()

    if (inputType === 'url' && !url.trim()) return
    if (inputType === 'file' && !htmlFile) return

    setIsLoading(true)
    try {
      if (inputType === 'url') {
        await onDownload({ type: 'url', value: url })
      } else {
        await onDownload({ type: 'file', value: htmlFile })
      }
    } finally {
      setIsLoading(false)
    }
  }

  const handleFileChange = (e) => {
    const file = e.target.files[0]
    if (file) {
      setHtmlFile(file)
      // Auto-detect file type
      if (file.name.endsWith('.json')) {
        setFileType('json')
      } else {
        setFileType('html')
      }
    }
  }

  const isBeatportUrl = url.includes('beatport.com')
  const isSpotifyUrl = url.includes('open.spotify.com/playlist')
  const isValidUrl = isBeatportUrl || isSpotifyUrl
  const canSubmit = inputType === 'url' ? (url.trim() && isValidUrl) : htmlFile !== null

  return (
    <form onSubmit={handleSubmit} className="download-form">
      <div className="form-group">
        <label className="label">Input Type</label>
        <div className="input-type-selector">
          <button
            type="button"
            className={`input-type-button ${inputType === 'url' ? 'active' : ''}`}
            onClick={() => setInputType('url')}
            disabled={disabled || isLoading}
          >
            URL
          </button>
          <button
            type="button"
            className={`input-type-button ${inputType === 'file' ? 'active' : ''}`}
            onClick={() => setInputType('file')}
            disabled={disabled || isLoading}
          >
            JSON File
          </button>
        </div>
      </div>

      {inputType === 'url' ? (
        <div className="form-group">
          <label htmlFor="url" className="label">Playlist URL</label>
          <input
            id="url"
            type="text"
            value={url}
            onChange={(e) => setUrl(e.target.value)}
            placeholder="https://www.beatport.com/chart/… or https://open.spotify.com/playlist/…"
            disabled={disabled || isLoading}
            className="input"
          />
          {url && !isValidUrl && (
            <p className="input-hint warning">Please enter a valid Beatport or Spotify playlist URL</p>
          )}
        </div>
      ) : (
        <div className="form-group">
          <label htmlFor="htmlFile" className="label">Beatport Playlist File (JSON or HTML)</label>
          <input
            id="htmlFile"
            type="file"
            accept=".json,.html,.htm"
            onChange={handleFileChange}
            disabled={disabled || isLoading}
            className="input file-input"
          />
          {htmlFile && (
            <>
              <p className="input-hint">Selected: {htmlFile.name}</p>
              {fileType === 'html' && (
                <p className="input-hint warning">
                  Note: Saved HTML files often don't contain track data. If this fails, use the Beatport URL instead or convert to JSON using url_to_json.py first.
                </p>
              )}
            </>
          )}
        </div>
      )}

      <button
        type="submit"
        disabled={disabled || isLoading || !canSubmit}
        className="button button-primary"
      >
        {isLoading ? (
          <>
            <span className="spinner"></span>
            {inputType === 'url' ? 'Fetching playlist...' : 'Processing file...'}
          </>
        ) : (
          'Download Playlist'
        )}
      </button>

      <div className="form-info">
        <p>
          {inputType === 'url'
            ? 'Enter a Beatport or Spotify playlist URL and we\'ll automatically download all tracks.'
            : 'Upload a JSON file containing playlist data. Use url_to_json.py to convert Beatport URLs to JSON format.'}
        </p>
        <ul>
          <li>Searches for each track on SoundCloud and YouTube</li>
          <li>Downloads the longer version (extended mixes preferred)</li>
          <li>Saves files with complete metadata and album art</li>
          <li>Automatically skips already downloaded tracks</li>
        </ul>
      </div>
    </form>
  )
}
