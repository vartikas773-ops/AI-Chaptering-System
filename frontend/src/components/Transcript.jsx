import { useState, useEffect, useRef } from 'react'
import { fmt } from '../utils'

export default function Transcript({ transcript, currentTime, onSeek }) {
  const [q, setQ] = useState('')
  const box = useRef(null)
  const activeRef = useRef(null)

  const activeIdx = transcript.findIndex(
    (l, i) => currentTime >= l.start && (i === transcript.length - 1 || currentTime < transcript[i + 1].start),
  )

  useEffect(() => {
    const el = activeRef.current
    const c = box.current
    if (el && c && !q) c.scrollTo({ top: el.offsetTop - c.clientHeight / 3, behavior: 'smooth' })
  }, [activeIdx, q])

  const needle = q.trim().toLowerCase()

  return (
    <div className="card transcript">
      <div className="transcript-head">
        <h3>Transcript</h3>
        <input className="input input-sm" type="search" placeholder="Search transcript" value={q} onChange={(e) => setQ(e.target.value)} />
      </div>
      <div className="transcript-scroll" ref={box}>
        {transcript.map((l, i) => {
          if (needle && !l.text.toLowerCase().includes(needle)) return null
          const active = i === activeIdx
          return (
            <button key={i} ref={active ? activeRef : null} className={active ? 'line active' : 'line'} onClick={() => onSeek(l.start)}>
              <span className="ts">{fmt(l.start)}</span>
              <span>{l.text}</span>
            </button>
          )
        })}
      </div>
    </div>
  )
}
