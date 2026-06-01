import { useState } from 'react'
import './DownloadForm.css'

const MODES = [
  { id: 'beatport', label: 'Beatport' },
  { id: 'tracklist-to-spotify', label: 'Tracklist → Spotify' },
  { id: 'spotify-to-download', label: 'Spotify → Download' },
]

export default function DownloadForm({ onDownload, disabled }) {
  const [mode, setMode] = useState('beatport')

  // Beatport mode
  const [url, setUrl] = useState('')
  const [htmlFile, setHtmlFile] = useState(null)
  const [inputType, setInputType] = useState('url')
  const [fileType, setFileType] = useState('html')

  // Tracklist → Spotify mode
  const [tracklist, setTracklist] = useState('')
  const [playlistName, setPlaylistName] = useState('')

  // Spotify → Download mode
  const [spotifyUrl, setSpotifyUrl] = useState('')

  const [isLoading, setIsLoading] = useState(false)

  const handleFileChange = (e) => {
    const file = e.target.files[0]
    if (file) {
      setHtmlFile(file)
      setFileType(file.name.endsWith('.json') ? 'json' : 'html')
    }
  }

  const isValidBeatportUrl = url.includes('beatport.com')
  const isValidSpotifyUrl = spotifyUrl.includes('open.spotify.com/playlist/') || spotifyUrl.startsWith('spotify:playlist:')

  const canSubmit = (() => {
    if (mode === 'beatport') {
      return inputType === 'url' ? (url.trim() && isValidBeatportUrl) : htmlFile !== null
    }
    if (mode === 'tracklist-to-spotify') return tracklist.trim().length > 0 && playlistName.trim().length > 0
    if (mode === 'spotify-to-download') return isValidSpotifyUrl
    return false
  })()

  const handleSubmit = async (e) => {
    e.preventDefault()
    if (!canSubmit) return

    setIsLoading(true)
    try {
      if (mode === 'beatport') {
        if (inputType === 'url') await onDownload({ mode, type: 'url', value: url })
        else await onDownload({ mode, type: 'file', value: htmlFile })
      } else if (mode === 'tracklist-to-spotify') {
        await onDownload({ mode, tracklist, name: playlistName })
      } else if (mode === 'spotify-to-download') {
        await onDownload({ mode, playlistUrl: spotifyUrl })
      }
    } finally {
      setIsLoading(false)
    }
  }

  return (
    <form onSubmit={handleSubmit} className="download-form">
      <div className="form-group">
        <label className="label">Mode</label>
        <div className="input-type-selector">
          {MODES.map((m) => (
            <button
              key={m.id}
              type="button"
              className={`input-type-button ${mode === m.id ? 'active' : ''}`}
              onClick={() => setMode(m.id)}
              disabled={disabled || isLoading}
            >
              {m.label}
            </button>
          ))}
        </div>
      </div>

      {mode === 'beatport' && (
        <>
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
              {url && !isValidBeatportUrl && (
                <p className="input-hint warning">Please enter a valid Beatport URL</p>
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
        </>
      )}

      {mode === 'tracklist-to-spotify' && (
        <>
          <div className="form-group">
            <label htmlFor="playlistName" className="label">Spotify Playlist Name</label>
            <input
              id="playlistName"
              type="text"
              value={playlistName}
              onChange={(e) => setPlaylistName(e.target.value)}
              placeholder="My Set"
              disabled={disabled || isLoading}
              className="input"
            />
          </div>
          <div className="form-group">
            <label htmlFor="tracklist" className="label">Tracklist</label>
            <textarea
              id="tracklist"
              value={tracklist}
              onChange={(e) => setTracklist(e.target.value)}
              placeholder={'Paste a tracklist here, e.g.\n1. Artist - Title\n2. Artist - Title\n4:50 Artist - Title (Mix)\n...'}
              rows={12}
              disabled={disabled || isLoading}
              className="input"
              style={{ fontFamily: 'monospace', resize: 'vertical' }}
            />
            <p className="input-hint">Numbered lines, timestamped lines, and slash-joined pairs are all supported. "ID" and "(unreleased)" lines are skipped.</p>
          </div>
        </>
      )}

      {mode === 'spotify-to-download' && (
        <div className="form-group">
          <label htmlFor="spotifyUrl" className="label">Spotify Playlist URL</label>
          <input
            id="spotifyUrl"
            type="text"
            value={spotifyUrl}
            onChange={(e) => setSpotifyUrl(e.target.value)}
            placeholder="https://open.spotify.com/playlist/..."
            disabled={disabled || isLoading}
            className="input"
          />
          {spotifyUrl && !isValidSpotifyUrl && (
            <p className="input-hint warning">Please enter a valid Spotify playlist URL</p>
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
            Working...
          </>
        ) : (
          mode === 'tracklist-to-spotify' ? 'Create Spotify Playlist' :
          mode === 'spotify-to-download' ? 'Download Playlist' :
          'Download Playlist'
        )}
      </button>
    </form>
  )
}
