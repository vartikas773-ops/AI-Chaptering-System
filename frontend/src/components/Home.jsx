import { useState } from 'react'
import { createUploadJob, createYoutubeJob, createSpotifyJob, searchSpotify } from '../api'

const MAX_MB = 500
const EXT = ['.mp3', '.wav', '.m4a', '.mp4', '.mov', '.mkv']
const TABS = [['upload', 'Upload'], ['youtube', 'YouTube'], ['spotify', 'Spotify']]

const FEATURES = [
  { title: 'Topic chapters', body: 'We find where the conversation changes subject and give every section a clear title, so you can jump straight to what matters.' },
  { title: 'AI notes', body: 'Get a summary, key points for each chapter and the action items people mentioned, each linked to the moment it was said.' },
  { title: 'Searchable transcript', body: 'Follow the text as it plays, click any line to jump there, and export subtitles as SRT or VTT.' },
]
const STEPS = [
  ['Add a recording', 'Upload a file, paste a YouTube link, or search for a podcast episode.'],
  ['We listen', 'It is transcribed and split wherever the topic shifts.'],
  ['Review and export', 'Read the notes, skim the chapters, then download what you need.'],
]

// Spotify search result field names depend on sources/spotify_listennotes.py, so be lenient.
const sp = (r) => ({
  id: r.id ?? r.episode_id,
  title: r.title ?? r.title_original ?? 'Untitled episode',
  show: r.podcast ?? r.podcast_title ?? r.podcast_title_original ?? r.show ?? '',
  image: r.thumbnail ?? r.image ?? r.thumbnail_url ?? null,
  mins: r.audio_length_sec ? Math.round(r.audio_length_sec / 60) : r.duration_min ?? null,
})

export default function Home({ onCreated }) {
  const [tab, setTab] = useState('upload')
  const [file, setFile] = useState(null)
  const [url, setUrl] = useState('')
  const [query, setQuery] = useState('')
  const [results, setResults] = useState(null)
  const [busy, setBusy] = useState(false)
  const [error, setError] = useState('')
  const [dragging, setDragging] = useState(false)

  const run = async (fn) => {
    setBusy(true); setError('')
    try {
      onCreated(await fn())
    } catch (err) {
      setError(err?.response?.data?.detail || 'Could not reach the backend. Check Settings → Backend URL.')
    } finally {
      setBusy(false)
    }
  }

  const pick = (f) => {
    setError('')
    if (!f) return
    const ext = '.' + f.name.split('.').pop().toLowerCase()
    if (!EXT.includes(ext)) return setError(`${ext} files aren't supported. Use ${EXT.join(', ')}.`)
    if (f.size / 1048576 > MAX_MB) return setError(`This file is over the ${MAX_MB} MB limit.`)
    setFile(f)
  }

  const search = async (e) => {
    e.preventDefault()
    if (!query.trim()) return
    setBusy(true); setError('')
    try {
      setResults((await searchSpotify(query.trim())).map(sp))
    } catch (err) {
      setError(err?.response?.data?.detail || 'Spotify search failed.')
    } finally {
      setBusy(false)
    }
  }

  const size = (b) => (b >= 1048576 ? `${(b / 1048576).toFixed(1)} MB` : `${Math.round(b / 1024)} KB`)

  return (
    <>
      <section className="hero">
        <div className="hero-copy">
          <h1>Turn one recording into chapters, notes and a transcript.</h1>
          <p className="lead">
            Add a podcast, lecture or meeting. TopicTrail splits it by topic, writes the notes, and
            keeps everything linked to the audio.
          </p>
        </div>

        <div className="upload-card">
          <div className="seg wide" role="tablist" aria-label="Source">
            {TABS.map(([k, l]) => (
              <button key={k} role="tab" aria-selected={tab === k} className={tab === k ? 'seg-btn active' : 'seg-btn'} onClick={() => { setTab(k); setError('') }}>{l}</button>
            ))}
          </div>

          {tab === 'upload' && (
            <form onSubmit={(e) => { e.preventDefault(); file && run(() => createUploadJob(file)) }} className="stack">
              <label
                className={dragging ? 'dropzone dragging' : file ? 'dropzone has-file' : 'dropzone'}
                onDragOver={(e) => { e.preventDefault(); setDragging(true) }}
                onDragLeave={() => setDragging(false)}
                onDrop={(e) => { e.preventDefault(); setDragging(false); pick(e.dataTransfer.files?.[0]) }}
              >
                <input type="file" accept={EXT.join(',')} onChange={(e) => pick(e.target.files[0])} />
                <span className="drop-icon" aria-hidden="true">{file ? '♪' : '↑'}</span>
                <strong>{file ? file.name : dragging ? 'Drop to upload' : 'Drop a file or click to browse'}</strong>
                <span className="muted small">{file ? size(file.size) : `${EXT.join(' ')} · up to ${MAX_MB} MB`}</span>
              </label>
              <button className="btn btn-primary btn-lg" disabled={!file || busy}>{busy ? 'Uploading…' : 'Generate chapters and notes'}</button>
            </form>
          )}

          {tab === 'youtube' && (
            <form onSubmit={(e) => { e.preventDefault(); url.trim() && run(() => createYoutubeJob(url.trim())) }} className="stack">
              <label htmlFor="yt" className="muted small">YouTube video link</label>
              <input id="yt" className="input" placeholder="https://www.youtube.com/watch?v=…" value={url} onChange={(e) => setUrl(e.target.value)} />
              <button className="btn btn-primary btn-lg" disabled={!url.trim() || busy}>{busy ? 'Starting…' : 'Generate chapters and notes'}</button>
            </form>
          )}

          {tab === 'spotify' && (
            <div className="stack">
              <form onSubmit={search} className="inline-form">
                <input className="input" aria-label="Search podcast episodes" placeholder="Search for a podcast episode" value={query} onChange={(e) => setQuery(e.target.value)} />
                <button className="btn btn-primary" disabled={!query.trim() || busy}>Search</button>
              </form>
              {results && results.length === 0 && <p className="muted">No episodes found. Try different words.</p>}
              <ul className="sp-results">
                {results?.map((r) => (
                  <li key={r.id}>
                    <button className="sp-item" disabled={busy} onClick={() => run(() => createSpotifyJob(r.id))}>
                      {r.image ? <img src={r.image} alt="" width="44" height="44" /> : <span className="sp-ph" aria-hidden="true">♪</span>}
                      <span className="sp-text">
                        <strong>{r.title}</strong>
                        <span className="muted small">{[r.show, r.mins && `${r.mins} min`].filter(Boolean).join(' · ')}</span>
                      </span>
                    </button>
                  </li>
                ))}
              </ul>
            </div>
          )}

          {error && <p className="error" role="alert">{error}</p>}
        </div>
      </section>

      <section className="features">
        {FEATURES.map((f) => (
          <article key={f.title} className="card feature"><h3>{f.title}</h3><p>{f.body}</p></article>
        ))}
      </section>

      <section className="steps">
        <h2>How it works</h2>
        <ol>
          {STEPS.map(([t, b], i) => (
            <li key={t}><span className="step-num">{i + 1}</span><div><strong>{t}</strong><p>{b}</p></div></li>
          ))}
        </ol>
      </section>
    </>
  )
}
