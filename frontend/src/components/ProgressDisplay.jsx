import { useEffect, useState } from 'react'
import './ProgressDisplay.css'

export default function ProgressDisplay({ progress, isLoading }) {
  const [logs, setLogs] = useState([])

  useEffect(() => {
    if (progress) {
      setLogs(prev => {
        const newLogs = [...prev]
        newLogs.push(progress)
        return newLogs.slice(-50)
      })
    }
  }, [progress])

  const currentTrack = progress?.track || {}
  const total = progress?.total || 0
  const current = progress?.current || 0
  const percentage = total > 0 ? Math.round((current / total) * 100) : 0

  return (
    <div className="progress-container">
      <div className="progress-header">
        <h2>Downloading Playlist</h2>
        {isLoading && <span className="loading-badge">In Progress</span>}
      </div>

      <div className="track-info">
        {currentTrack.artist && currentTrack.track && (
          <>
            <p className="current-track">
              <strong>{currentTrack.artist}</strong> - {currentTrack.track}
            </p>
            {currentTrack.status === 'downloading' && (
              <p className="track-status">Downloading...</p>
            )}
            {currentTrack.status === 'exists' && (
              <p className="track-status exists">Already exists, skipping</p>
            )}
            {currentTrack.status === 'failed' && (
              <p className="track-status failed">Failed to download</p>
            )}
          </>
        )}
      </div>

      <div className="progress-bar-container">
        <div className="progress-stats">
          <span className="stat-label">Overall Progress</span>
          <span className="stat-value">{current} / {total}</span>
        </div>
        <div className="progress-bar">
          <div
            className="progress-fill"
            style={{ width: `${percentage}%` }}
          ></div>
        </div>
        <div className="progress-percentage">{percentage}%</div>
      </div>

      <div className="logs-container">
        <h3>Activity Log</h3>
        <div className="logs">
          {logs.map((log, idx) => (
            <div key={idx} className="log-entry">
              <span className="log-icon">
                {log.status === 'downloading' && '⬇'}
                {log.status === 'exists' && '✓'}
                {log.status === 'failed' && '✗'}
              </span>
              <span className="log-message">
                {log.artist && log.track ? (
                  <>{log.artist} - {log.track}</>
                ) : (
                  log.message
                )}
              </span>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}
