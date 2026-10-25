# TopicTrail

Turn one recording into topic chapters, AI notes and a searchable transcript.

Upload a podcast, lecture or meeting, paste a YouTube link, or search for a podcast episode. TopicTrail transcribes it, splits it wherever the topic changes, titles each chapter, and writes notes you can read, search and export, all linked back to the audio.

## Features

- **Three ways in:** file upload, YouTube link, or Spotify-style podcast episode search (via ListenNotes).
- **Topic chapters:** boundaries found by comparing sentence embeddings, with a headline title, keywords and a sentiment label for each chapter.
- **AI Notes:** an overall summary, a summary and key points for each chapter, topics, and action items detected in the speech. Every item links to the moment in the audio.
- **Synced transcript:** follows playback, is searchable, and each line is clickable.
- **Export:** notes (Markdown), chapters and transcript (text), subtitles (SRT, VTT).
- **Library:** every recording is stored on the backend, so you can reopen it later with its audio, or delete it.
- **Light and dark themes.**

Everything runs locally. No recording or transcript is sent to an outside AI service.

## Live App

<img width="1917" height="986" alt="Screenshot 2026-10-15 224407" src="https://github.com/user-attachments/assets/c4d88817-2f2e-4b76-a013-32bef239eb19" />
<img width="1917" height="973" alt="Screenshot 2026-10-26 001515" src="https://github.com/user-attachments/assets/1edc3ae2-fc42-4c1c-8d70-4bb82359096d" />
<img width="1917" height="981" alt="Screenshot 2026-10-26 001555" src="https://github.com/user-attachments/assets/1100a47c-d415-48e9-9760-f82f623a3de1" />


## How it works

```
source ─► preprocessing ─► transcription ─► segmentation ─► chaptering ─► AI notes
(upload /   16 kHz mono,     faster-whisper   SBERT sliding   KeyBERT +      distilBART +
 YouTube /  trimmed,         in 10-minute     window + cosine distilBART +    SBERT key
 Spotify)   normalized       chunks           similarity      TF-IDF + VADER  sentences
```

| Stage | File | What it does |
|---|---|---|
| Preprocess | `pipeline/preprocessing.py` | Loads any audio or video, trims silence, normalizes loudness, resamples to 16 kHz mono, splits into 10-minute chunks |
| Transcribe | `pipeline/transcription.py` | faster-whisper per chunk, timestamps stitched back onto one timeline |
| Segment | `pipeline/segmentation.py` | Embeds sentences with `all-MiniLM-L6-v2`, starts a new chapter where similarity drops into the lowest percentile |
| Chapter | `pipeline/chaptering.py` | Titles (KeyBERT seed refined by distilBART), TF-IDF keywords, VADER sentiment, flags very short chapters as `is_micro` |
| Notes | `pipeline/notes.py` | Chapter summaries, representative key sentences, action-item detection, overall summary |

`jobs.py` runs these in a background task and updates the job's status and progress in SQLite. The frontend polls that status.

## Project structure

```
topictrail/
├── backend/
│   ├── app/
│   │   ├── pipeline/        preprocessing, transcription, segmentation, chaptering, notes
│   │   ├── sources/         upload, YouTube, Spotify (ListenNotes)
│   │   ├── config.py        settings, read from .env
│   │   ├── db.py            SQLite job storage
│   │   ├── jobs.py          pipeline orchestrator
│   │   ├── main.py          FastAPI routes
│   │   └── models.py        request models
│   ├── storage/             media files and topictrail.db (created at runtime)
│   ├── .env.example
│   └── requirements.txt
└── frontend/                React + Vite app
    └── src/
        ├── components/      Home, Processing, Workspace, NotesPanel, Library, ...
        ├── api.js           every backend call lives here
        ├── utils.js         time formatting, exports
        └── styles.css
```

## Requirements

- **Python 3.11 or 3.12** from python.org. Avoid 3.13 or newer (`pydub` needs the `audioop` module, which was removed). On Windows, avoid the MSYS2 build of Python: many packages have no prebuilt wheels for it.
- **Node.js** (LTS) for the frontend.
- **FFmpeg** on your PATH. Check with `ffmpeg -version`.
- Disk space and patience for the first run: the speech and language models download the first time they are used.

## Setup

### 1. Backend

```powershell
cd backend
py -3.11 -m venv .venv
.venv\Scripts\activate
python -m pip install --upgrade pip
pip install -r requirements.txt
pip install uvicorn python-multipart
```

On macOS or Linux, use `python3.11 -m venv .venv` and `source .venv/bin/activate` instead.

Copy `.env.example` to `.env` and fill in the values. If you want the Spotify tab, add your ListenNotes API key there (see `.env.example` for the variable names).

Make sure `CORS_ORIGINS` in `app/config.py` includes the address the frontend runs on, `http://localhost:5173`. Use the exact address from your browser's address bar: `localhost` and `127.0.0.1` count as different origins.

Start the server from the `backend` folder:

```
uvicorn app.main:app --reload --port 8000
```

Check it at <http://127.0.0.1:8000/docs>.

### 2. Frontend

In a second terminal:

```
cd frontend
npm install
npm run dev
```

Open <http://localhost:5173>. To preview the results screen without a backend, open <http://localhost:5173/?demo>.

For a production build run `npm run build`; the static site is written to `frontend/dist/`.

## Usage

1. Choose **Upload**, **YouTube** or **Spotify** on the home screen and start a job.
2. Watch the progress. Processing continues on the server, so you can leave the page and come back through **Library**.
3. Read the **AI Notes** tab, jump around with the **Chapters** tab, or follow along in the transcript.
4. Use **Export** to download notes, chapters, transcript or subtitles.

Keyboard shortcuts on the results screen: `Space` to play or pause, `←` and `→` to skip 5 seconds.

## Notes and limitations

- Transcripts are automatic. Names, jargon and noisy audio may be wrong.
- Action items come from phrase matching ("we need to", "make sure", ...), so interviews and lectures often have few or none.
- Very short chapters are flagged `is_micro` and hidden from lists and previous/next navigation. They stay in the stored data.
- The waveform decodes the whole media file in the browser, which may be heavy for multi-hour recordings.

## Credits

Built on faster-whisper, SentenceTransformers, KeyBERT, Hugging Face Transformers (distilBART), scikit-learn, VADER, FastAPI, React, Vite and wavesurfer.js. The frontend structure started from the AI-Driven Audio Chaptering and Segmentation System project.
