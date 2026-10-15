// All backend calls live here. Routes match backend/app/main.py.
import axios from 'axios'

const KEY = 'topictrail_backend_url'
export const DEFAULT_BASE_URL = 'http://127.0.0.1:8000'

export const getBaseUrl = () => localStorage.getItem(KEY) || DEFAULT_BASE_URL
export const setBaseUrl = (url) => localStorage.setItem(KEY, url.trim() || DEFAULT_BASE_URL)
const http = () => axios.create({ baseURL: getBaseUrl() })

// ---- create jobs (each returns job_id) --------------------------------------
export async function createUploadJob(file) {
  const form = new FormData()
  form.append('file', file)
  return (await http().post('/api/jobs/upload', form)).data.job_id
}
export async function createYoutubeJob(url) {
  return (await http().post('/api/jobs/youtube', { url })).data.job_id
}
export async function createSpotifyJob(episodeId) {
  return (await http().post('/api/jobs/spotify', { episode_id: episodeId })).data.job_id
}
export async function searchSpotify(query, limit = 8) {
  return (await http().post('/api/spotify/search', { query, limit })).data.results || []
}

// ---- read / list / delete ---------------------------------------------------
export const getJob = async (id) => (await http().get(`/api/jobs/${id}`)).data
export const listJobs = async () => (await http().get('/api/jobs')).data.jobs || []
export const deleteJob = async (id) => (await http().delete(`/api/jobs/${id}`)).data

// Turns whatever db.get_job returns into one predictable shape. It tolerates the
// result being nested under `result` (object or JSON string) or flattened onto the job.
export function normalizeJob(job) {
  let res = job.result
  if (typeof res === 'string') {
    try { res = JSON.parse(res) } catch { res = null }
  }
  if (!res && Array.isArray(job.chapters)) res = job
  const done = !!res && Array.isArray(res.chapters)
  const media = res?.media_url
  return {
    id: job.id || job.job_id,
    status: job.status,
    progress: job.progress || 0,
    error: job.error,
    title: res?.title || job.title || job.source_ref,
    done,
    result: done
      ? {
          chapters: res.chapters,
          transcript: res.transcript || [],
          notes: res.notes || null,
          mediaUrl: media ? (media.startsWith('http') ? media : getBaseUrl() + media) : null,
        }
      : null,
  }
}
