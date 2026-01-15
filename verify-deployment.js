#!/usr/bin/env node
import { existsSync } from 'fs'
import path from 'path'
import { fileURLToPath } from 'url'

const __filename = fileURLToPath(import.meta.url)
const __dirname = path.dirname(__filename)

console.log('Beatport Downloader - Deployment Verification')
console.log('=' .repeat(50))
console.log()

let hasErrors = false

const checks = [
  {
    name: 'Python downloader script',
    path: 'beatport_downloader.py',
    required: true
  },
  {
    name: 'Scraper module',
    path: 'scraper.py',
    required: true
  },
  {
    name: 'Downloader module',
    path: 'downloader.py',
    required: true
  },
  {
    name: 'Node.js server',
    path: 'server.js',
    required: true
  },
  {
    name: 'Frontend dist folder',
    path: 'frontend/dist',
    required: false
  },
  {
    name: 'Frontend index.html',
    path: 'frontend/dist/index.html',
    required: false
  },
  {
    name: 'Requirements.txt',
    path: 'requirements.txt',
    required: true
  },
  {
    name: 'Package.json',
    path: 'package.json',
    required: true
  }
]

console.log('Checking files...')
console.log()

for (const check of checks) {
  const fullPath = path.join(__dirname, check.path)
  const exists = existsSync(fullPath)

  const status = exists ? '✓' : '✗'
  const color = exists ? '\x1b[32m' : '\x1b[31m'
  const reset = '\x1b[0m'

  console.log(`${color}${status}${reset} ${check.name}`)
  console.log(`  ${fullPath}`)

  if (!exists && check.required) {
    hasErrors = true
    console.log(`  ${color}ERROR: Required file missing!${reset}`)
  } else if (!exists && !check.required) {
    console.log(`  \x1b[33mWARNING: Optional file missing${reset}`)
  }

  console.log()
}

console.log('=' .repeat(50))

if (hasErrors) {
  console.log('\x1b[31m✗ Deployment verification failed!\x1b[0m')
  console.log()
  console.log('Required files are missing. Please check your deployment.')
  process.exit(1)
} else {
  console.log('\x1b[32m✓ Deployment verification passed!\x1b[0m')
  console.log()

  if (!existsSync(path.join(__dirname, 'frontend/dist/index.html'))) {
    console.log('\x1b[33mNote: Frontend not built.\x1b[0m')
    console.log('Run: npm run build')
    console.log()
  }

  process.exit(0)
}
