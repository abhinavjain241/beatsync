import './SummaryDisplay.css'

export default function SummaryDisplay({ summary, onReset }) {
  const {
    total = 0,
    downloaded = 0,
    skipped = 0,
    failed = 0,
    failedTracks = [],
    downloadedTracks = [],
    skippedTracks = [],
    downloadFolder = ''
  } = summary || {}

  const successCount = downloaded + skipped
  const successRate = total > 0 ? Math.round((successCount / total) * 100) : 0

  // Combine downloaded and skipped tracks for display
  const allSuccessfulTracks = [
    ...downloadedTracks.map(t => ({ ...t, status: 'downloaded' })),
    ...skippedTracks.map(t => ({ ...t, status: 'skipped' }))
  ]

  return (
    <div className="summary-container">
      <div className="summary-header">
        <h2>Download Complete</h2>
        <div className={`summary-badge ${successRate === 100 ? 'success' : successRate >= 80 ? 'good' : 'warning'}`}>
          {successRate}% Complete
        </div>
      </div>

      <div className="stats-grid">
        <div className="stat-card total">
          <div className="stat-value">{total}</div>
          <div className="stat-label">Total Tracks</div>
        </div>

        <div className="stat-card downloaded">
          <div className="stat-value">{downloaded}</div>
          <div className="stat-label">Downloaded</div>
        </div>

        <div className="stat-card skipped">
          <div className="stat-value">{skipped}</div>
          <div className="stat-label">Already Existed</div>
        </div>

        <div className="stat-card failed">
          <div className="stat-value">{failed}</div>
          <div className="stat-label">Failed</div>
        </div>
      </div>

      <div className="summary-message">
        {successRate === 100 ? (
          <p>✓ All tracks downloaded successfully!</p>
        ) : successRate >= 80 ? (
          <p>✓ Most tracks downloaded successfully. {failed} track(s) failed.</p>
        ) : (
          <p>⚠ Download completed with some failures. Please check the results.</p>
        )}
      </div>

      {downloadFolder && (
        <div className="download-folder-section">
          <h3>Download Location</h3>
          <div className="download-folder-path">
            <span className="folder-icon">📁</span>
            <code className="folder-path">{downloadFolder}</code>
          </div>
        </div>
      )}

      <div className="tracks-lists">
        {allSuccessfulTracks.length > 0 && (
          <div className="successful-tracks-section">
            <h3>Downloaded Tracks ({allSuccessfulTracks.length})</h3>
            <div className="tracks-list">
              {allSuccessfulTracks.map((track, index) => (
                <div key={index} className={`track-item ${track.status}`}>
                  <span className="track-icon">{track.status === 'downloaded' ? '✓' : '⊙'}</span>
                  <div className="track-info">
                    <span className="track-name">{track.artist} - {track.track}</span>
                    {track.status === 'skipped' && (
                      <span className="track-status-badge">Already existed</span>
                    )}
                  </div>
                </div>
              ))}
            </div>
          </div>
        )}

        {failedTracks && failedTracks.length > 0 && (
          <div className="failed-tracks-section">
            <h3>Failed Tracks ({failedTracks.length})</h3>
            <div className="tracks-list">
              {failedTracks.map((track, index) => {
                // Handle both string format (old) and object format (new)
                const trackName = typeof track === 'string'
                  ? track
                  : `${track.artist} - ${track.track}`

                return (
                  <div key={index} className="track-item failed">
                    <span className="track-icon">✗</span>
                    <span className="track-name">{trackName}</span>
                  </div>
                )
              })}
            </div>
          </div>
        )}
      </div>

      <div className="summary-actions">
        <button onClick={onReset} className="button button-primary">
          Download Another Playlist
        </button>
      </div>
    </div>
  )
}
