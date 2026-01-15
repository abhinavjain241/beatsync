import express from 'express'
import cors from 'cors'
import { spawn } from 'child_process'
import path from 'path'
import { fileURLToPath } from 'url'
import dotenv from 'dotenv'

dotenv.config()

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const app = express()
const PORT = process.env.PORT || 3000

app.use(cors())
app.use(express.json())
app.use(express.static(path.join(__dirname, 'frontend', 'dist')))

let ongoingDownloads = new Map()

app.post('/api/download', (req, res) => {
  const { url } = req.body

  if (!url) {
    return res.status(400).json({ error: 'URL is required' })
  }

  const downloadId = Date.now().toString()

  res.setHeader('Content-Type', 'application/x-ndjson')
  res.setHeader('Transfer-Encoding', 'chunked')
  res.setHeader('Cache-Control', 'no-cache')

  const pythonScript = path.join(__dirname, 'beatport_downloader.py')

  const pythonProcess = spawn('python3', [pythonScript, url], {
    cwd: __dirname,
    stdio: ['ignore', 'pipe', 'pipe']
  })

  ongoingDownloads.set(downloadId, pythonProcess)

  let buffer = ''
  let current = 0
  let total = 0
  let trackCount = 0

  pythonProcess.stdout.on('data', (data) => {
    const output = data.toString()
    buffer += output

    const lines = buffer.split('\n')
    buffer = lines.pop()

    for (const line of lines) {
      if (!line.trim()) continue

      const lowerLine = line.toLowerCase()

      if (lowerLine.includes('found ') && lowerLine.includes(' track')) {
        const match = line.match(/found (\d+) track/)
        if (match) {
          total = parseInt(match[1])
          sendProgress({
            type: 'progress',
            data: {
              message: `Found ${total} tracks`,
              total,
              current: 0,
              track: {}
            }
          })
        }
      }

      if (lowerLine.includes('[') && lowerLine.includes(']') && lowerLine.includes('processing')) {
        const match = line.match(/\[(\d+)\/(\d+)\]\s+processing:\s+(.+)/i)
        if (match) {
          current = parseInt(match[1])
          const fullName = match[3]
          const parts = fullName.split(' - ')
          const artist = parts[0] || ''
          const track = parts.slice(1).join(' - ') || ''

          sendProgress({
            type: 'progress',
            data: {
              total,
              current,
              track: { artist, track, status: 'processing' },
              message: `Processing ${fullName}`
            }
          })
        }
      }

      if (lowerLine.includes('downloading:')) {
        const match = line.match(/downloading:\s+(.+)/i)
        if (match) {
          const filename = match[1]
          const parts = filename.replace('.mp3', '').split(' - ')
          const artist = parts[0] || ''
          const track = parts.slice(1).join(' - ') || ''

          sendProgress({
            type: 'progress',
            data: {
              total,
              current,
              track: { artist, track, status: 'downloading' },
              message: `Downloading ${filename}`
            }
          })
        }
      }

      if (lowerLine.includes('✓ downloaded:')) {
        const match = line.match(/✓\s+downloaded:\s+(.+)/i)
        if (match) {
          const filename = match[1]
          const parts = filename.replace('.mp3', '').split(' - ')
          const artist = parts[0] || ''
          const track = parts.slice(1).join(' - ') || ''

          sendProgress({
            type: 'progress',
            data: {
              total,
              current,
              track: { artist, track, status: 'completed' },
              message: `Downloaded: ${filename}`
            }
          })
        }
      }

      if (lowerLine.includes('already exists')) {
        sendProgress({
          type: 'progress',
          data: {
            total,
            current,
            track: { status: 'exists' },
            message: 'File already exists, skipping'
          }
        })
      }

      if (lowerLine.includes('✗')) {
        sendProgress({
          type: 'progress',
          data: {
            total,
            current,
            track: { status: 'failed' },
            message: line
          }
        })
      }

      if (
        lowerLine.includes('total tracks:') ||
        lowerLine.includes('downloaded:') ||
        lowerLine.includes('already existed:') ||
        lowerLine.includes('failed:')
      ) {
        const data = parseDownloadSummary(buffer, lines)
        if (data) {
          sendProgress({
            type: 'summary',
            data
          })
        }
      }
    }
  })

  pythonProcess.stderr.on('data', (data) => {
    const error = data.toString().trim()
    if (error) {
      sendProgress({
        type: 'error',
        message: error
      })
    }
  })

  pythonProcess.on('close', (code) => {
    ongoingDownloads.delete(downloadId)

    if (code !== 0) {
      sendProgress({
        type: 'error',
        message: `Process exited with code ${code}`
      })
    }

    res.end()
  })

  function sendProgress(data) {
    res.write(JSON.stringify(data) + '\n')
  }
})

app.get('/api/downloads', (req, res) => {
  res.json({
    active: ongoingDownloads.size,
    total: ongoingDownloads.size
  })
})

app.get('*', (req, res) => {
  res.sendFile(path.join(__dirname, 'frontend', 'dist', 'index.html'))
})

app.listen(PORT, () => {
  console.log(`Server running on http://localhost:${PORT}`)
  console.log(`Frontend: http://localhost:${PORT}`)
})

function parseDownloadSummary(fullBuffer, lines) {
  const allText = fullBuffer + lines.join('\n')

  const totalMatch = allText.match(/total tracks:\s*(\d+)/i)
  const downloadedMatch = allText.match(/downloaded:\s*(\d+)/i)
  const existedMatch = allText.match(/already existed:\s*(\d+)/i)
  const failedMatch = allText.match(/failed:\s*(\d+)/i)

  if (totalMatch) {
    return {
      total: parseInt(totalMatch[1]),
      downloaded: downloadedMatch ? parseInt(downloadedMatch[1]) : 0,
      skipped: existedMatch ? parseInt(existedMatch[1]) : 0,
      failed: failedMatch ? parseInt(failedMatch[1]) : 0
    }
  }

  return null
}
