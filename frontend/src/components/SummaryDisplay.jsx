import './SummaryDisplay.css'

export default function SummaryDisplay({ summary, onReset }) {
  const {
    total = 0,
    downloaded = 0,
    skipped = 0,
    failed = 0,
    failedTracks = []
  } = summary || {}

  const successCount = downloaded + skipped
  const successRate = total > 0 ? Math.round((successCount / total) * 100) : 0

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

      {failedTracks && failedTracks.length > 0 && (
        <div className="failed-tracks-section">
          <h3>Failed Tracks</h3>
          <div className="failed-tracks-list">
            {failedTracks.map((track, index) => (
              <div key={index} className="failed-track-item">
                <span className="failed-icon">✗</span>
                <span className="failed-track-name">{track}</span>
              </div>
            ))}
          </div>
        </div>
      )}

      <div className="summary-actions">
        <button onClick={onReset} className="button button-primary">
          Download Another Playlist
        </button>
        <a href="/downloads" className="button button-secondary" target="_blank" rel="noopener noreferrer">
          Open Downloads Folder
        </a>
      </div>
    </div>
  )
}
