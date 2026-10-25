import { useState, useEffect } from 'react'
import Navbar from './components/Navbar'
import Home from './components/Home'
import Processing from './components/Processing'
import Workspace from './components/Workspace'
import Library from './components/Library'
import Settings from './components/Settings'
import About from './components/About'
import { getJob, normalizeJob } from './api'
import { fallbackNotes } from './utils'
import { mockResult } from './mockResult'

const DEMO = new URLSearchParams(window.location.search).has('demo')

export default function App() {
  const [page, setPage] = useState('home')
  const [status, setStatus] = useState(DEMO ? 'done' : 'idle') // idle | processing | done | error
  const [jobId, setJobId] = useState(null)
  const [jobStatus, setJobStatus] = useState('')
  const [title, setTitle] = useState(DEMO ? 'demo-episode.mp3' : '')
  const [result, setResult] = useState(DEMO ? mockResult : null)
  const [progress, setProgress] = useState(0)
  const [error, setError] = useState('')
  const [theme, setTheme] = useState(
    () => localStorage.getItem('theme') || (window.matchMedia?.('(prefers-color-scheme: dark)').matches ? 'dark' : 'light'),
  )

  useEffect(() => {
    document.documentElement.setAttribute('data-theme', theme)
    localStorage.setItem('theme', theme)
  }, [theme])

  // Polls GET /api/jobs/{id} until the job is done or failed. Lives at App level so
  // switching pages never interrupts it.
  useEffect(() => {
    if (!jobId) return
    let stop = false
    let timer
    const poll = async () => {
      try {
        const job = normalizeJob(await getJob(jobId))
        if (stop) return
        if (job.title) setTitle(job.title)
        if (job.done) {
          const notes = job.result.notes
          setResult({ ...job.result, notes: notes || fallbackNotes(job.result.chapters), hasAiNotes: !!notes })
          setStatus('done')
          return
        }
        if (job.status === 'error') {
          setError(job.error || 'Processing failed.')
          setStatus('error')
          return
        }
        setJobStatus(job.status)
        setProgress(Math.round((job.progress || 0) * 100))
      } catch (err) {
        if (stop) return
        if (err?.response?.status === 404) {
          setError('This job no longer exists.')
          setStatus('error')
          return
        }
        // network hiccup: keep polling
      }
      timer = setTimeout(poll, 2000)
    }
    poll()
    return () => { stop = true; clearTimeout(timer) }
  }, [jobId])

  const startJob = (id) => {
    setJobId(id); setJobStatus(''); setProgress(0); setError(''); setResult(null)
    setStatus('processing'); setPage('home')
  }
  const reset = () => {
    setStatus('idle'); setJobId(null); setResult(null); setTitle(''); setProgress(0); setError('')
  }

  const [firstLine, ...rest] = error.split('\n')

  return (
    <>
      <Navbar theme={theme} onSetTheme={setTheme} page={page} onNavigate={setPage} />
      <main className="app">
        <div
  aria-hidden={page !== 'home'}
  style={page !== 'home' ? { height: 0, overflow: 'hidden', visibility: 'hidden' } : undefined}
>
  {status === 'idle' && <Home onCreated={startJob} />}
  {status === 'processing' && <Processing progress={progress} stage={jobStatus} title={title} />}
  {status === 'error' && (
    <section className="center-stack">
      <h2>We couldn't process this recording</h2>
      <p className="error">{firstLine}</p>
      {rest.length > 0 && (
        <details className="muted small"><summary>Technical details</summary><pre className="trace">{rest.join('\n')}</pre></details>
      )}
      <button className="btn btn-primary" onClick={reset}>Try another recording</button>
    </section>
  )}
  {status === 'done' && (
    <Workspace result={result} fileName={title} theme={theme} onNewFile={reset} active={page === 'home'} />
  )}
</div>
        {page === 'library' && <Library onOpen={startJob} onGoHome={() => { reset(); setPage('home') }} />}
        {page === 'settings' && <Settings theme={theme} onSetTheme={setTheme} />}
        {page === 'about' && <About />}
      </main>
    </>
  )
}
