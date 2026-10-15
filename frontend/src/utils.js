const pad = (n) => String(n).padStart(2, '0')

export function fmt(seconds) {
  const s = Math.max(0, Math.floor(seconds || 0))
  const h = Math.floor(s / 3600)
  const m = Math.floor((s % 3600) / 60)
  return h ? `${h}:${pad(m)}:${pad(s % 60)}` : `${m}:${pad(s % 60)}`
}

function stamp(seconds, sep) {
  const ms = Math.round((seconds % 1) * 1000)
  const s = Math.floor(seconds)
  return `${pad(Math.floor(s / 3600))}:${pad(Math.floor((s % 3600) / 60))}:${pad(s % 60)}${sep}${String(ms).padStart(3, '0')}`
}

export const toSRT = (t) =>
  t.map((l, i) => `${i + 1}\n${stamp(l.start, ',')} --> ${stamp(l.end ?? l.start + 3, ',')}\n${l.text}\n`).join('\n')

export const toVTT = (t) =>
  'WEBVTT\n\n' + t.map((l) => `${stamp(l.start, '.')} --> ${stamp(l.end ?? l.start + 3, '.')}\n${l.text}\n`).join('\n')

export function download(name, text, type = 'text/plain') {
  const url = URL.createObjectURL(new Blob([text], { type }))
  const a = document.createElement('a')
  a.href = url
  a.download = name
  a.click()
  URL.revokeObjectURL(url)
}

// Chapters flagged is_micro by the backend are hidden from lists/navigation.
export const visibleChapters = (chapters) => {
  const v = (chapters || []).filter((c) => !c.is_micro)
  return v.length ? v : chapters || []
}

// Used when the backend has no /notes endpoint (or it fails): a plain outline built
// from data the chapter pipeline already returns. No AI-written text.
export function fallbackNotes(chapters) {
  const vis = visibleChapters(chapters)
  const counts = {}
  vis.forEach((c) => (c.keywords || []).forEach((k) => (counts[k] = (counts[k] || 0) + 1)))
  const topics = Object.entries(counts).sort((a, b) => b[1] - a[1]).slice(0, 8).map(([k]) => k)
  return {
    summary: '',
    topics,
    action_items: [],
    key_points: vis.map((c) => ({
      chapter_index: c.index,
      start: c.start,
      end: c.end,
      title: c.title,
      summary: '',
      points: c.text ? (c.text.match(/[^.!?]+[.!?]/g) || []).slice(0, 2).map((s) => s.trim()) : [],
      keywords: c.keywords || [],
      sentiment: c.sentiment,
    })),
  }
}

export function notesToMarkdown(fileName, notes) {
  const out = [`# Notes: ${fileName || 'Recording'}`, '']
  if (notes.summary) out.push('## Summary', '', notes.summary, '')
  if (notes.topics?.length) out.push('**Topics:** ' + notes.topics.join(', '), '')
  if (notes.key_points?.length) {
    out.push('## Key points', '')
    notes.key_points.forEach((k) => {
      out.push(`### [${fmt(k.start)}] ${k.title}`, '')
      if (k.summary) out.push(k.summary, '')
      ;(k.points || []).forEach((p) => out.push(`- ${p}`))
      out.push('')
    })
  }
  if (notes.action_items?.length) {
    out.push('## Action items', '')
    notes.action_items.forEach((a) => out.push(`- [ ] ${a.text} (${fmt(a.start)})`))
  }
  return out.join('\n')
}
