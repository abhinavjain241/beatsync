import express from 'express'
import cors from 'cors'
import { spawn } from 'child_process'
import path from 'path'
import { fileURLToPath } from 'url'
import dotenv from 'dotenv'
import multer from 'multer'
import fs from 'fs/promises'
import { tmpdir } from 'os'

dotenv.config()

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

const app = express()
const PORT = process.env.PORT || 3000

const upload = multer({
  storage: multer.diskStorage({
    destination: tmpdir(),
    filename: (req, file, cb) => {
      cb(null, `beatport-${Date.now()}-${file.originalname}`)
    }
  })
})

app.use(cors())
app.use(express.json())
app.use(express.static(path.join(__dirname, 'frontend', 'dist')))

let ongoingDownloads = new Map()

app.post('/api/download', upload.single('htmlFile'), async (req, res) => {
  const { url } = req.body
  const htmlFile = req.file

  if (!url && !htmlFile) {
    return res.status(400).json({ error: 'URL or HTML file is required' })
  }

  const downloadId = Date.now().toString()

  res.setHeader('Content-Type', 'application/x-ndjson')
  res.setHeader('Transfer-Encoding', 'chunked')
  res.setHeader('Cache-Control', 'no-cache')

  let jsonFilePath = null
  let htmlFilePath = htmlFile ? htmlFile.path : null

  function sendProgress(data) {
    res.write(JSON.stringify(data) + '\n')
  }

  try {
    if (url) {
      sendProgress({ type: 'progress', data: { message: 'Extracting playlist from URL...', current: 0, total: 0 } })

      const urlToJsonScript = path.join(__dirname, 'url_to_json.py')
      jsonFilePath = path.join(tmpdir(), `beatport-${Date.now()}.json`)

      const extractProcess = spawn('python3', [urlToJsonScript, url, '-o', jsonFilePath], {
        cwd: __dirname,
        stdio: ['ignore', 'pipe', 'pipe']
      })

      let extractError = ''
      extractProcess.stderr.on('data', (data) => {
        extractError += data.toString()
      })

      const extractExitCode = await new Promise((resolve) => {
        extractProcess.on('close', resolve)
      })

      if (extractExitCode !== 0) {
        sendProgress({ type: 'error', message: `Failed to extract playlist: ${extractError}` })
        res.end()
        if (jsonFilePath) await fs.unlink(jsonFilePath).catch(() => {})
        return
      }

      sendProgress({ type: 'progress', data: { message: 'Playlist extracted successfully. Starting downloads...', current: 0, total: 0 } })
    }

    const downloaderScript = path.join(__dirname, 'beatport_downloader.py')
    let downloaderArgs = []

    if (jsonFilePath) {
      downloaderArgs = ['--json-file', jsonFilePath]
    } else if (htmlFilePath) {
      downloaderArgs = ['--local-html', htmlFilePath]
    }

    const pythonProcess = spawn('python3', [downloaderScript, ...downloaderArgs], {
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

  pythonProcess.on('close', async (code) => {
    ongoingDownloads.delete(downloadId)

    if (code !== 0) {
      sendProgress({
        type: 'error',
        message: `Process exited with code ${code}`
      })
    }

    if (jsonFilePath) {
      await fs.unlink(jsonFilePath).catch(() => {})
    }
    if (htmlFilePath) {
      await fs.unlink(htmlFilePath).catch(() => {})
    }

    res.end()
  })
  } catch (error) {
    sendProgress({
      type: 'error',
      message: error.message || 'An error occurred'
    })

    if (jsonFilePath) {
      await fs.unlink(jsonFilePath).catch(() => {})
    }
    if (htmlFilePath) {
      await fs.unlink(htmlFilePath).catch(() => {})
    }

    res.end()
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
