import { useState } from 'react'
import { fmt } from '../utils'

export default function ChapterList({ chapters, currentTime, onSeek }) {
  const [q, setQ] = useState('')
  const needle = q.trim().toLowerCase()
  const list = needle
    ? chapters.filter((c) => (c.title + ' ' + (c.keywords || []).join(' ')).toLowerCase().includes(needle))
    : chapters

  return (
    <div className="panel-body">
      <input className="input" type="search" placeholder="Search chapters by topic" value={q} onChange={(e) => setQ(e.target.value)} />
      <ul className="chapters">
        {list.length === 0 && <li className="muted">No chapters match “{q}”.</li>}
        {list.map((c) => {
          const active = currentTime >= c.start && currentTime < c.end
          return (
            <li key={c.start}>
              <button className={active ? 'chapter active' : 'chapter'} onClick={() => onSeek(c.start)}>
                <span className="ts">{fmt(c.start)}</span>
                <span className="chapter-main">
                  <strong>{c.title}</strong>
                  {c.keywords?.length > 0 && <span className="muted small">{c.keywords.slice(0, 4).join(', ')}</span>}
                </span>
              </button>
            </li>
          )
        })}
      </ul>
    </div>
  )
}
