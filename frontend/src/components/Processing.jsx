const STAGES = {
  downloading: 'Fetching the recording',
  preprocessing: 'Preparing the audio',
  transcribing: 'Transcribing',
  segmenting: 'Finding topic changes',
  titling: 'Titling chapters',
  notes: 'Writing AI notes',
}

export default function Processing({ progress, stage, title }) {
  return (
    <section className="center-stack" aria-live="polite">
      <h2>{STAGES[stage] || 'Starting'}…</h2>
      {title && <p className="muted">{title}</p>}
      <div className="progress" role="progressbar" aria-valuenow={progress} aria-valuemin={0} aria-valuemax={100}>
        <div style={{ width: `${progress}%` }} />
      </div>
      <p className="muted small">Long recordings can take several minutes. Please wait till we process your request.</p>
    </section>
  )
}
