import './SummaryDisplay.css'

export default function SummaryDisplay({ summary, onReset }) {
  const {
    total = 0,
    downloaded = 0,
    skipped = 0,
    failed = 0
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
