import { useState, useEffect, useMemo } from 'react'
import Player from './Player'
import NotesPanel from './NotesPanel'
import ChapterList from './ChapterList'
import Transcript from './Transcript'
import { download, toSRT, toVTT, visibleChapters, fmt, notesToMarkdown } from '../utils'

export default function Workspace({ result, fileName, theme, onNewFile, active = true }) {
  const [ws, setWs] = useState(null)
  const [time, setTime] = useState(0)
  const [tab, setTab] = useState('notes')

  const chapters = useMemo(() => visibleChapters(result.chapters), [result.chapters])
  const current = chapters.find((c) => time >= c.start && time < c.end)
  const base = (fileName || 'recording').replace(/\.[^.]+$/, '')

  const seek = (t) => {
    if (!ws) return
    ws.setTime(t)
    ws.play()
  }
  const step = (dir) => {
    const idx = current ? chapters.indexOf(current) : -1
    const target = chapters[Math.max(0, Math.min(chapters.length - 1, idx + dir))]
    if (target) seek(target.start)
  }

  // Space = play/pause, ←/→ = ±5s (ignored while typing)
    useEffect(() => {
      if (!ws || !active) return
      const onKey = (e) => {
        if (['INPUT', 'TEXTAREA'].includes(e.target.tagName)) return
        if (e.code === 'Space') { e.preventDefault(); ws.playPause() }
        else if (e.code === 'ArrowRight') ws.setTime(ws.getCurrentTime() + 5)
        else if (e.code === 'ArrowLeft') ws.setTime(Math.max(0, ws.getCurrentTime() - 5))
      }
      window.addEventListener('keydown', onKey)
      return () => window.removeEventListener('keydown', onKey)
    }, [ws, active])

  const hasTranscript = result.transcript?.length > 0
  const exports = [
    ['Notes (.md)', () => download(`${base}-notes.md`, notesToMarkdown(fileName, result.notes || {}), 'text/markdown'), !!result.notes],
    ['Chapters (.txt)', () => download(`${base}-chapters.txt`, chapters.map((c) => `${fmt(c.start)}  ${c.title}`).join('\n')), true],
    ['Transcript (.txt)', () => download(`${base}-transcript.txt`, result.transcript.map((l) => `[${fmt(l.start)}] ${l.text}`).join('\n')), hasTranscript],
    ['Subtitles (.srt)', () => download(`${base}.srt`, toSRT(result.transcript)), hasTranscript],
    ['Subtitles (.vtt)', () => download(`${base}.vtt`, toVTT(result.transcript), 'text/vtt'), hasTranscript],
  ]

  return (
    <section className="workspace">
      <div className="ws-head">
        <div>
          <h2>{fileName || 'Recording'}</h2>
          <p className="muted small">{chapters.length} chapters</p>
        </div>
        <div className="ws-actions">
          <details className="menu">
            <summary className="btn btn-secondary">Export</summary>
            <div className="menu-list">
              {exports.map(([label, fn, ok]) => (
                <button key={label} disabled={!ok} onClick={(e) => { fn(); e.currentTarget.closest('details').open = false }}>
                  {label}
                </button>
              ))}
            </div>
          </details>
          <button className="btn btn-primary" onClick={onNewFile}>New upload</button>
        </div>
      </div>

      <div className="ws-grid">
        <div className="ws-left">
          <Player
            mediaUrl={result.mediaUrl}
            theme={theme}
            currentTime={time}
            onReady={(w) => { setWs(w); w.on('timeupdate', setTime) }}
            onPrev={() => step(-1)}
            onNext={() => step(1)}
          />
          {current && (
            <div className="now-playing">
              <span className="muted small">Now playing</span>
              <strong>{current.title}</strong>
            </div>
          )}
          {hasTranscript && <Transcript transcript={result.transcript} currentTime={time} onSeek={seek} />}
        </div>

        <div className="ws-right card">
          <div className="tabs" role="tablist">
            {[['notes', 'AI Notes'], ['chapters', 'Chapters']].map(([k, l]) => (
              <button key={k} role="tab" aria-selected={tab === k} className={tab === k ? 'tab active' : 'tab'} onClick={() => setTab(k)}>
                {l}
              </button>
            ))}
          </div>
          {tab === 'notes' ? (
            <NotesPanel notes={result.notes} state={result.hasAiNotes === false ? 'fallback' : 'ready'} fileName={fileName} currentTime={time} onSeek={seek} />
          ) : (
            <ChapterList chapters={chapters} currentTime={time} onSeek={seek} />
          )}
        </div>
      </div>
    </section>
  )
}
