import { useState } from 'react'
import { fmt, download, notesToMarkdown } from '../utils'

const MOOD = { positive: 'Positive', negative: 'Negative', neutral: 'Neutral' }

export default function NotesPanel({ notes, state, fileName, currentTime, onSeek }) {
  const [done, setDone] = useState({})
  const [copied, setCopied] = useState(false)

  if (!notes) {
    return (
      <div className="panel-body center-stack" aria-live="polite">
        <div className="spinner" aria-hidden="true" />
        <p className="muted">Writing your notes…</p>
      </div>
    )
  }

  const md = () => notesToMarkdown(fileName, notes)
  const copy = async () => {
    await navigator.clipboard.writeText(md())
    setCopied(true)
    setTimeout(() => setCopied(false), 1500)
  }

  return (
    <div className="panel-body notes">
      <div className="notes-actions">
        <button className="btn btn-secondary btn-sm" onClick={copy}>{copied ? 'Copied' : 'Copy notes'}</button>
        <button className="btn btn-secondary btn-sm" onClick={() => download('notes.md', md(), 'text/markdown')}>Download .md</button>
      </div>

      {state === 'fallback' && (
        <p className="notice">
          Showing a basic outline. This recording was processed before AI notes were added, so it has no written summary.
        </p>
      )}

      {notes.summary && (
        <section>
          <h3>Summary</h3>
          <p>{notes.summary}</p>
        </section>
      )}

      {notes.topics?.length > 0 && (
        <section>
          <h3>Topics</h3>
          <div className="chips">{notes.topics.map((t) => <span key={t} className="chip">{t}</span>)}</div>
        </section>
      )}

      {notes.key_points?.length > 0 && (
        <section>
          <h3>Key points</h3>
          {notes.key_points.map((k) => {
            const active = currentTime >= k.start && (k.end == null || currentTime < k.end)
            return (
              <article key={k.chapter_index ?? k.start} className={active ? 'kp active' : 'kp'}>
                <button className="ts" onClick={() => onSeek(k.start)} title="Play from here">{fmt(k.start)}</button>
                <div>
                  <h4>
                    {k.title}
                    {k.sentiment && <span className={`mood ${k.sentiment.label}`}>{MOOD[k.sentiment.label]}</span>}
                  </h4>
                  {k.summary && <p>{k.summary}</p>}
                  {k.points?.length > 0 && <ul>{k.points.map((p, i) => <li key={i}>{p}</li>)}</ul>}
                </div>
              </article>
            )
          })}
        </section>
      )}

      <section>
        <h3>Action items</h3>
        {notes.action_items?.length ? (
          <ul className="actions">
            {notes.action_items.map((a, i) => (
              <li key={i} className={done[i] ? 'done' : ''}>
                <label>
                  <input type="checkbox" checked={!!done[i]} onChange={() => setDone((d) => ({ ...d, [i]: !d[i] }))} />
                  <span>{a.text}</span>
                </label>
                <button className="ts" onClick={() => onSeek(a.start)}>{fmt(a.start)}</button>
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted">No action items were mentioned in this recording.</p>
        )}
      </section>
    </div>
  )
}
