import { useState } from 'react'
import { getBaseUrl, setBaseUrl, DEFAULT_BASE_URL } from '../api'

export default function Settings({ theme, onSetTheme }) {
  const [url, setUrl] = useState(getBaseUrl())
  const [saved, setSaved] = useState(false)

  const save = (e) => {
    e.preventDefault()
    setBaseUrl(url)
    setSaved(true)
    setTimeout(() => setSaved(false), 2000)
  }

  return (
    <section className="page narrow">
      <h2>Settings</h2>
      <div className="card form-card">
        <h3>Appearance</h3>
        <div className="seg" role="group" aria-label="Theme">
          {['light', 'dark'].map((t) => (
            <button key={t} className={theme === t ? 'seg-btn active' : 'seg-btn'} onClick={() => onSetTheme(t)}>
              {t === 'light' ? 'Light' : 'Dark'}
            </button>
          ))}
        </div>
      </div>
      <form className="card form-card" onSubmit={save}>
        <h3>Backend</h3>
        <label htmlFor="backend" className="muted small">Backend URL</label>
        <input id="backend" className="input" value={url} onChange={(e) => setUrl(e.target.value)} placeholder={DEFAULT_BASE_URL} />
        <div className="form-row">
          <button className="btn btn-primary" type="submit">Save changes</button>
          {saved && <span className="saved">Saved</span>}
        </div>
      </form>
    </section>
  )
}
