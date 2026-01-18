import { useEffect, useState } from 'react'
import './ProgressDisplay.css'

export default function ProgressDisplay({ progress, isLoading, stage }) {
  const [logs, setLogs] = useState([])

  useEffect(() => {
    if (progress) {
      setLogs(prev => {
        const newLogs = [...prev]
        newLogs.push({
          ...progress,
          timestamp: new Date().toLocaleTimeString()
        })
        return newLogs.slice(-100)
      })
    }
  }, [progress])

  const currentTrack = progress?.track || {}
  const total = progress?.total || 0
  const current = progress?.current || 0
  const percentage = total > 0 ? Math.round((current / total) * 100) : 0

  const getStageLabel = (stageData) => {
    if (!stageData) return 'Initializing...'
    switch (stageData.stage) {
      case 'extraction':
        return 'Extracting playlist data'
      case 'download_prep':
        return 'Preparing downloads'
      case 'downloading':
        return 'Downloading tracks'
      default:
        return stageData.message || 'Processing...'
    }
  }

  return (
    <div className="progress-container">
      <div className="progress-header">
        <h2>Downloading Playlist</h2>
        {isLoading && <span className="loading-badge">In Progress</span>}
      </div>

      {stage && (
        <div className="stage-indicator">
          <div className="stage-icon">
            {stage.stage === 'extraction' && '🔍'}
            {stage.stage === 'download_prep' && '⚙️'}
            {stage.stage === 'downloading' && '⬇️'}
            {!stage.stage && '🔄'}
          </div>
          <div className="stage-text">
            <div className="stage-label">{getStageLabel(stage)}</div>
            <div className="stage-message">{stage.message}</div>
          </div>
        </div>
      )}

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
          {logs.length === 0 && (
            <div className="log-entry log-empty">
              <span className="log-message">Waiting for activity...</span>
            </div>
          )}
          {logs.map((log, idx) => (
            <div key={idx} className={`log-entry ${log.track?.status || ''}`}>
              <span className="log-timestamp">{log.timestamp}</span>
              <span className="log-icon">
                {log.track?.status === 'processing' && '🔄'}
                {log.track?.status === 'downloading' && '⬇️'}
                {log.track?.status === 'completed' && '✓'}
                {log.track?.status === 'exists' && '↩️'}
                {log.track?.status === 'failed' && '✗'}
                {!log.track?.status && '•'}
              </span>
              <span className="log-message">
                {log.track?.artist && log.track?.track ? (
                  <><strong>{log.track.artist}</strong> - {log.track.track}</>
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
