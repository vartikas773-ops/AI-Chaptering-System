import { useState, useEffect } from 'react'
import { listJobs, deleteJob } from '../api'

const LABEL = { done: 'Ready', error: 'Failed' }

export default function Library({ onOpen, onGoHome }) {
  const [jobs, setJobs] = useState(null)
  const [err, setErr] = useState('')

  const load = () => listJobs().then(setJobs).catch(() => setErr('Could not load recordings. Check Settings → Backend URL.'))
  useEffect(() => { load() }, [])

  const remove = async (id) => {
    if (!window.confirm('Delete this recording and its files?')) return
    await deleteJob(id)
    load()
  }

  const idOf = (j) => j.id || j.job_id
  const ready = jobs?.filter((j) => j.status === 'done').length ?? 0

  return (
    <section className="page">
      <div className="page-head">
        <h2>Library</h2>
        <button className="btn btn-primary" onClick={onGoHome}>New recording</button>
      </div>

      {jobs && (
        <div className="stats">
          <div className="card stat"><strong>{jobs.length}</strong><span className="muted">Recordings</span></div>
          <div className="card stat"><strong>{ready}</strong><span className="muted">Ready to read</span></div>
        </div>
      )}
      {err && <p className="error">{err}</p>}
      {jobs && jobs.length === 0 && (
        <div className="card empty">
          <p><strong>Nothing here yet</strong></p>
          <p className="muted">Add a recording and it will appear here with its chapters and notes.</p>
        </div>
      )}
      <ul className="lib-list">
        {jobs?.map((j) => (
          <li key={idOf(j)} className="card lib-item">
            <div className="lib-row">
              <div className="lib-title">
                <strong>{j.title || j.source_ref || 'Untitled'}</strong>
                <span className="muted small">
                  {[j.source_type, j.created_at && new Date(j.created_at).toLocaleString()].filter(Boolean).join(' · ')}
                </span>
              </div>
              <span className={`mood ${j.status === 'done' ? 'positive' : j.status === 'error' ? 'negative' : 'neutral'}`}>
                {LABEL[j.status] || 'Processing'}
              </span>
              <button className="btn btn-secondary btn-sm" onClick={() => onOpen(idOf(j))}>Open</button>
              <button className="btn btn-danger btn-sm" onClick={() => remove(idOf(j))}>Delete</button>
            </div>
          </li>
        ))}
      </ul>
    </section>
  )
}
