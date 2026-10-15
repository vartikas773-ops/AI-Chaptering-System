const FAQ = [
  ['Which files can I upload?', '.mp3, .wav, .m4a, .mp4, .mov and .mkv, up to 500 MB.'],
  ['Why does processing take a while?', 'Transcription runs on the backend machine, so long recordings can take several minutes on a CPU.'],
  ['How are the AI notes made?', 'They are generated on the backend from the transcript: a summary per chapter, the most representative sentences as key points, and action items detected from phrases like “we need to” or “make sure”.'],
  ['Why are some chapters missing?', 'Very short chapters are hidden from lists and previous/next navigation. They are still in the data.'],
  ['Is my audio kept?', 'Recordings, transcripts and notes are stored on the backend until you delete them from the Library.'],
]

export default function About() {
  return (
    <section className="page narrow">
      <h2>Help</h2>
      <p className="muted">TopicTrail splits recordings into topic chapters and writes notes you can search and export.</p>
      <div className="faq">
        {FAQ.map(([q, a]) => (
          <details key={q} className="card faq-item">
            <summary>{q}</summary>
            <p>{a}</p>
          </details>
        ))}
      </div>
      <div className="card">
        <h3>Keyboard shortcuts</h3>
        <p className="muted"><kbd>Space</kbd> play or pause · <kbd>←</kbd> <kbd>→</kbd> skip 5 seconds</p>
      </div>
    </section>
  )
}
