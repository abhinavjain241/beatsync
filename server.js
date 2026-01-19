import express from 'express'
import cors from 'cors'
import { spawn, exec } from 'child_process'
import { promisify } from 'util'
import path from 'path'
import { fileURLToPath } from 'url'
import dotenv from 'dotenv'
import multer from 'multer'
import fs from 'fs/promises'
import { tmpdir } from 'os'

const execPromise = promisify(exec)

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

  console.log('\n========================================')
  console.log('NEW DOWNLOAD REQUEST')
  console.log('========================================')
  console.log('URL:', url || 'none')
  console.log('HTML File:', htmlFile ? htmlFile.originalname : 'none')
  console.log('Timestamp:', new Date().toISOString())

  if (!url && !htmlFile) {
    console.error('ERROR: No URL or HTML file provided')
    return res.status(400).json({ error: 'URL or HTML file is required' })
  }

  const downloadId = Date.now().toString()
  console.log('Download ID:', downloadId)

  res.setHeader('Content-Type', 'application/x-ndjson')
  res.setHeader('Transfer-Encoding', 'chunked')
  res.setHeader('Cache-Control', 'no-cache')

  let jsonFilePath = null
  let htmlFilePath = htmlFile ? htmlFile.path : null

  function sendProgress(data) {
    console.log('[PROGRESS]', JSON.stringify(data, null, 2))
    res.write(JSON.stringify(data) + '\n')
  }

  try {
    if (url) {
      console.log('\n--- STAGE 1: URL EXTRACTION ---')
      console.log('Starting URL extraction process...')
      sendProgress({ type: 'stage', stage: 'extraction', message: 'Extracting playlist from URL...' })
      sendProgress({ type: 'progress', data: { message: 'Extracting playlist from URL...', current: 0, total: 0 } })

      const urlToJsonScript = path.join(__dirname, 'url_to_json.py')
      jsonFilePath = path.join(tmpdir(), `beatport-${Date.now()}.json`)

      console.log('Script path:', urlToJsonScript)
      console.log('Output JSON path:', jsonFilePath)
      console.log('Spawning python3 process...')

      const extractProcess = spawn('python3', [urlToJsonScript, url, '-o', jsonFilePath], {
        cwd: __dirname,
        stdio: ['ignore', 'pipe', 'pipe']
      })

      let extractError = ''
      let extractOutput = ''

      extractProcess.stdout.on('data', (data) => {
        const output = data.toString()
        extractOutput += output
        console.log('[URL_EXTRACT_STDOUT]', output.trim())
      })

      extractProcess.stderr.on('data', (data) => {
        const error = data.toString()
        extractError += error
        console.error('[URL_EXTRACT_STDERR]', error.trim())
      })

      const extractExitCode = await new Promise((resolve) => {
        extractProcess.on('close', (code) => {
          console.log('URL extraction process closed with code:', code)
          resolve(code)
        })
      })

      if (extractExitCode !== 0) {
        console.error('ERROR: URL extraction failed!')
        console.error('Exit code:', extractExitCode)
        console.error('Error output:', extractError)
        sendProgress({
          type: 'error',
          stage: 'extraction',
          message: `Failed to extract playlist from URL (exit code ${extractExitCode})`,
          details: extractError || 'No error details available'
        })
        res.end()
        if (jsonFilePath) await fs.unlink(jsonFilePath).catch(() => {})
        return
      }

      console.log('URL extraction successful!')
      console.log('JSON file created at:', jsonFilePath)
      sendProgress({ type: 'stage', stage: 'download_prep', message: 'Playlist extracted successfully. Starting downloads...' })
      sendProgress({ type: 'progress', data: { message: 'Playlist extracted successfully. Starting downloads...', current: 0, total: 0 } })
    }

    console.log('\n--- STAGE 2: DOWNLOAD PROCESS ---')
    const downloaderScript = path.join(__dirname, 'beatport_downloader.py')
    let downloaderArgs = []

    if (jsonFilePath) {
      downloaderArgs = ['--json-file', jsonFilePath, '--yes']
      console.log('Using JSON file:', jsonFilePath)
    } else if (htmlFilePath) {
      // Convert HTML to JSON first
      sendProgress({ type: 'stage', stage: 'html_conversion', message: 'Converting HTML to JSON format...' })
      console.log('Converting HTML file to JSON...')

      const convertScript = path.join(__dirname, 'url_to_json.py')
      const convertedJsonPath = path.join(tmpdir(), `converted-${Date.now()}.json`)

      // Read HTML file and use url_to_json extraction logic
      const htmlContent = await fs.readFile(htmlFilePath, 'utf-8')
      const htmlTempPath = path.join(tmpdir(), `temp-${Date.now()}.html`)
      await fs.writeFile(htmlTempPath, htmlContent)

      // Use a simpler Python script to extract from local HTML
      const extractScript = `
import sys
import json
sys.path.insert(0, '${__dirname}')
from url_to_json import extract_script_json, build_playlist_data

with open('${htmlTempPath}', 'r', encoding='utf-8') as f:
    html = f.read()

playlist = build_playlist_data(html)
print(json.dumps(playlist, indent=2, ensure_ascii=False))
`

      const extractPath = path.join(tmpdir(), `extract-${Date.now()}.py`)
      await fs.writeFile(extractPath, extractScript)

      try {
        const { stdout } = await execPromise(`python3 "${extractPath}"`)

        // Check if extraction was successful
        let extractedData = []
        try {
          extractedData = JSON.parse(stdout)
        } catch (e) {
          console.error('Failed to parse extraction output:', e)
        }

        if (!extractedData || extractedData.length === 0) {
          console.error('HTML file contains no track data')
          sendProgress({
            type: 'error',
            stage: 'html_conversion',
            message: 'HTML file does not contain track data. Saved HTML files from Beatport don\'t preserve playlist information.',
            details: 'To download tracks, please use one of these methods instead:\n\n' +
                    '1. Enter the Beatport playlist URL directly (recommended)\n' +
                    '2. Use the url_to_json.py script to convert the live URL to JSON first:\n' +
                    '   python3 url_to_json.py <beatport-url>\n' +
                    '3. Upload the generated JSON file instead of HTML\n\n' +
                    'Note: Saved HTML files only contain the page structure, not the dynamically loaded track data.'
          })
          res.end()
          await fs.unlink(htmlFilePath).catch(() => {})
          await fs.unlink(htmlTempPath).catch(() => {})
          await fs.unlink(extractPath).catch(() => {})
          await fs.unlink(convertedJsonPath).catch(() => {})
          return
        }

        await fs.writeFile(convertedJsonPath, stdout)
        console.log(`HTML converted to JSON successfully - ${extractedData.length} tracks found`)

        // Clean up temp files
        await fs.unlink(htmlTempPath).catch(() => {})
        await fs.unlink(extractPath).catch(() => {})

        // Use the converted JSON file
        jsonFilePath = convertedJsonPath
        downloaderArgs = ['--json-file', convertedJsonPath, '--yes']
        console.log('Using converted JSON file:', convertedJsonPath)
      } catch (conversionError) {
        console.error('HTML conversion failed:', conversionError)
        sendProgress({
          type: 'error',
          stage: 'html_conversion',
          message: 'Failed to extract playlist data from HTML file.',
          details: conversionError.message
        })
        res.end()
        await fs.unlink(htmlFilePath).catch(() => {})
        await fs.unlink(htmlTempPath).catch(() => {})
        await fs.unlink(extractPath).catch(() => {})
        return
      }
    }

    console.log('Downloader script:', downloaderScript)
    console.log('Downloader args:', downloaderArgs)
    console.log('Spawning downloader process...')

    sendProgress({ type: 'stage', stage: 'downloading', message: 'Starting track download process...' })

    const pythonProcess = spawn('python3', [downloaderScript, ...downloaderArgs], {
      cwd: __dirname,
      stdio: ['ignore', 'pipe', 'pipe']
    })

    console.log('Downloader process spawned with PID:', pythonProcess.pid)
    ongoingDownloads.set(downloadId, pythonProcess)

  let buffer = ''
  let current = 0
  let total = 0
  let trackCount = 0
  let failedTracks = []

  let downloadFolder = ''
  let downloadedTracks = []
  let failedTracksList = []
  let skippedTracks = []
  let summaryData = null

  pythonProcess.stdout.on('data', (data) => {
    const output = data.toString()
    // Only log raw output for debugging - comment this out to avoid duplicate logs
    // console.log('[DOWNLOADER_STDOUT]', output.trim())
    buffer += output

    const lines = buffer.split('\n')
    buffer = lines.pop()

    for (const line of lines) {
      if (!line.trim()) continue

      const lowerLine = line.toLowerCase()
      // Only log meaningful lines, not every single line
      const isStructuredMessage = line.includes('[TRACK_START]') || line.includes('[TRACK_RESULT]') ||
        line.includes('[DOWNLOAD_FOLDER]') || line.includes('[DOWNLOADED_TRACKS]') ||
        line.includes('[FAILED_TRACKS]') || line.includes('[SKIPPED_TRACKS]')

      if (isStructuredMessage || lowerLine.includes('processing') || lowerLine.includes('downloading') ||
          lowerLine.includes('error') || lowerLine.includes('failed')) {
        console.log('[PROGRESS]', line)
      }

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
          // Extract total from the [X/Y] format if we haven't set it yet
          if (total === 0) {
            total = parseInt(match[2])
          }
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
        // Extract track name from failure message
        // Format: "✗ Failed: Artist - Track Name"
        const failMatch = line.match(/✗\s*(?:failed|error)[:\s]*(.+)/i)
        if (failMatch) {
          const trackName = failMatch[1].trim()
          failedTracks.push(trackName)
        }

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

      // Parse structured track start message
      if (line.startsWith('[TRACK_START]')) {
        const parts = line.substring('[TRACK_START]'.length).trim().split(' | ')
        if (parts.length >= 3) {
          const [progress, artist, track] = parts
          const [curr, tot] = progress.split('/')
          current = parseInt(curr)
          total = parseInt(tot)

          sendProgress({
            type: 'progress',
            data: {
              total,
              current,
              track: { artist, track, status: 'processing' },
              message: `Processing: ${artist} - ${track}`
            }
          })
        }
      }

      // Parse structured track result message
      if (line.startsWith('[TRACK_RESULT]')) {
        const parts = line.substring('[TRACK_RESULT]'.length).trim().split(' | ')
        if (parts.length >= 3) {
          const [status, artist, track] = parts
          sendProgress({
            type: 'progress',
            data: {
              total,
              current,
              track: { artist, track, status: status.toLowerCase() },
              message: `${status}: ${artist} - ${track}`
            }
          })
        }
      }

      // Parse download folder
      if (line.startsWith('[DOWNLOAD_FOLDER]')) {
        downloadFolder = line.substring('[DOWNLOAD_FOLDER]'.length).trim()
      }

      // Parse downloaded tracks list
      if (line.startsWith('[DOWNLOADED_TRACKS]')) {
        try {
          downloadedTracks = JSON.parse(line.substring('[DOWNLOADED_TRACKS]'.length).trim())
        } catch (e) {
          console.error('Failed to parse downloaded tracks:', e)
        }
      }

      // Parse failed tracks list
      if (line.startsWith('[FAILED_TRACKS]')) {
        try {
          failedTracksList = JSON.parse(line.substring('[FAILED_TRACKS]'.length).trim())
        } catch (e) {
          console.error('Failed to parse failed tracks:', e)
        }
      }

      // Parse skipped tracks list
      if (line.startsWith('[SKIPPED_TRACKS]')) {
        try {
          skippedTracks = JSON.parse(line.substring('[SKIPPED_TRACKS]'.length).trim())
        } catch (e) {
          console.error('Failed to parse skipped tracks:', e)
        }

        // After parsing all structured data, send the complete summary
        if (summaryData) {
          summaryData.downloadFolder = downloadFolder
          summaryData.downloadedTracks = downloadedTracks
          summaryData.failedTracks = failedTracksList
          summaryData.skippedTracks = skippedTracks

          sendProgress({
            type: 'summary',
            data: summaryData
          })
          console.log('Sent complete summary with structured data')
        }
      }

      if (
        lowerLine.includes('total tracks:') ||
        lowerLine.includes('downloaded:') ||
        lowerLine.includes('already existed:') ||
        lowerLine.includes('failed:')
      ) {
        // Parse summary but don't send yet - wait for structured data
        const data = parseDownloadSummary(buffer, lines, failedTracks)
        if (data) {
          summaryData = data
        }
      }
    }
  })

  pythonProcess.stderr.on('data', (data) => {
    const error = data.toString().trim()
    if (error) {
      console.error('[DOWNLOADER_STDERR]', error)
      sendProgress({
        type: 'error',
        stage: 'downloading',
        message: error,
        details: error
      })
    }
  })

  pythonProcess.on('close', async (code) => {
    console.log('\n--- PROCESS COMPLETE ---')
    console.log('Downloader process closed with code:', code)
    console.log('Download ID:', downloadId)

    ongoingDownloads.delete(downloadId)

    // Send summary if we have it and it hasn't been sent yet
    if (summaryData && code === 0) {
      summaryData.downloadFolder = downloadFolder
      summaryData.downloadedTracks = downloadedTracks
      summaryData.failedTracks = failedTracksList
      summaryData.skippedTracks = skippedTracks

      sendProgress({
        type: 'summary',
        data: summaryData
      })
      console.log('Sent final summary on process close')
    }

    if (code !== 0) {
      console.error('ERROR: Process failed with exit code:', code)
      sendProgress({
        type: 'error',
        stage: 'process_exit',
        message: `Download process failed (exit code ${code})`,
        details: `The download process exited unexpectedly. This usually means there was an error fetching or processing the tracks. Check the activity log for more details.`,
        exitCode: code
      })
    } else {
      console.log('SUCCESS: Process completed successfully')
    }

    console.log('Cleaning up temporary files...')
    if (jsonFilePath) {
      await fs.unlink(jsonFilePath).catch((err) => {
        console.error('Failed to delete JSON file:', err)
      })
    }
    if (htmlFilePath) {
      await fs.unlink(htmlFilePath).catch((err) => {
        console.error('Failed to delete HTML file:', err)
      })
    }

    console.log('Request complete')
    console.log('========================================\n')
    res.end()
  })
  } catch (error) {
    console.error('\n!!! EXCEPTION CAUGHT !!!')
    console.error('Error:', error)
    console.error('Stack:', error.stack)

    sendProgress({
      type: 'error',
      stage: 'exception',
      message: error.message || 'An unexpected error occurred',
      details: error.stack || error.toString()
    })

    console.log('Cleaning up after exception...')
    if (jsonFilePath) {
      await fs.unlink(jsonFilePath).catch((err) => {
        console.error('Failed to delete JSON file:', err)
      })
    }
    if (htmlFilePath) {
      await fs.unlink(htmlFilePath).catch((err) => {
        console.error('Failed to delete HTML file:', err)
      })
    }

    console.log('========================================\n')
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

function parseDownloadSummary(fullBuffer, lines, failedTracks = []) {
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
      failed: failedMatch ? parseInt(failedMatch[1]) : 0,
      failedTracks: failedTracks
    }
  }

  return null
}
