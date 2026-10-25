import { useState } from 'react'
import WavesurferPlayer from '@wavesurfer/react'
import { fmt } from '../utils'

const SPEEDS = [1, 1.25, 1.5, 2]

export default function Player({ mediaUrl, theme, currentTime, onReady, onPrev, onNext }) {
  const [ws, setWs] = useState(null)
  const [video, setVideo] = useState(null)
  const [hasVideo, setHasVideo] = useState(false)
  const [playing, setPlaying] = useState(false)
  const [speed, setSpeed] = useState(1)
  const [duration, setDuration] = useState(0)

  if (!mediaUrl) {
    return (
      <div className="card player muted">
        Audio isn't available for this entry. Notes and chapters are still shown; playback is only
        available in the session where the file was uploaded.
      </div>
    )
  }

  const css = getComputedStyle(document.documentElement)
  const ready = (w) => {
    setWs(w)
    setDuration(w.getDuration())
    if (video) setHasVideo(video.videoWidth > 0)
    w.on('play', () => setPlaying(true))
    w.on('pause', () => setPlaying(false))
    w.on('finish', () => setPlaying(false))
    onReady(w)
  }

  const checkVideo = (e) => setHasVideo(e.currentTarget.videoWidth > 0)

  return (
    <div className="card player">
      <video
        ref={setVideo}
        src={mediaUrl}
        playsInline
        preload="metadata"
        onLoadedMetadata={checkVideo}
        onLoadedData={checkVideo}
        onResize={checkVideo}
        onClick={() => ws?.playPause()}
        style={{
          display: hasVideo ? 'block' : 'none',
          width: '100%',
          maxHeight: 360,
          background: '#000',
          borderRadius: 12,
          marginBottom: 12,
          cursor: 'pointer',
        }}
      />
      {video && (
        <WavesurferPlayer
          key={theme}
          media={video}
          height={64}
          barWidth={3}
          barGap={2}
          barRadius={2}
          waveColor={theme === 'dark' ? '#4a5a62' : '#cbbfb4'}
          progressColor={theme === 'dark' ? '#ff7a45' : '#d9400f'}
          cursorWidth={0}
          url={mediaUrl}
          onReady={ready}
        />
      )}
      <div className="player-bar">
        <div className="player-buttons">
          <button className="btn btn-ghost icon-btn" onClick={onPrev} aria-label="Previous chapter" title="Previous chapter">⏮</button>
                      <button className="btn btn-primary play" onClick={() => ws?.playPause()} aria-label={playing ? 'Pause' : 'Play'}>
            {playing ? '❚❚' : '▶'}
          </button>
          <button className="btn btn-ghost icon-btn" onClick={onNext} aria-label="Next chapter" title="Next chapter">⏭</button>
        </div>
        <span className="time">{fmt(currentTime)} / {fmt(duration)}</span>
        <div className="seg" role="group" aria-label="Playback speed">
          {SPEEDS.map((r) => (
            <button
              key={r}
              className={speed === r ? 'seg-btn active' : 'seg-btn'}
              onClick={() => { ws?.setPlaybackRate(r); setSpeed(r) }}
            >
              {r}×
            </button>
          ))}
        </div>
      </div>
    </div>
  )
}
