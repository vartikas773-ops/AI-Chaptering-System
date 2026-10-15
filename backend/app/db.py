"""
Tiny sqlite wrapper -- no ORM needed for one table.
Job status/results survive a server restart, per the README.
"""
import json
import sqlite3
import time
import uuid
from contextlib import contextmanager
from typing import Any, Optional

from .config import DB_PATH

SCHEMA = """
CREATE TABLE IF NOT EXISTS jobs (
    id TEXT PRIMARY KEY,
    source_type TEXT NOT NULL,       -- 'upload' | 'youtube' | 'spotify'
    source_ref TEXT,                 -- original url / filename / episode id
    title TEXT,
    media_path TEXT,
    status TEXT NOT NULL DEFAULT 'queued',  -- queued|downloading|transcribing|segmenting|titling|done|error
    progress REAL NOT NULL DEFAULT 0,
    error TEXT,
    result_json TEXT,
    created_at REAL NOT NULL,
    updated_at REAL NOT NULL
);
"""


@contextmanager
def get_conn():
    conn = sqlite3.connect(DB_PATH, timeout=30)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def init_db():
    with get_conn() as conn:
        conn.execute(SCHEMA)


def create_job(source_type: str, source_ref: str, title: Optional[str] = None) -> str:
    job_id = uuid.uuid4().hex[:12]
    now = time.time()
    with get_conn() as conn:
        conn.execute(
            "INSERT INTO jobs (id, source_type, source_ref, title, status, progress, created_at, updated_at) "
            "VALUES (?, ?, ?, ?, 'queued', 0, ?, ?)",
            (job_id, source_type, source_ref, title, now, now),
        )
    return job_id


def update_job(job_id: str, **fields: Any):
    if not fields:
        return
    fields["updated_at"] = time.time()
    cols = ", ".join(f"{k} = ?" for k in fields)
    values = list(fields.values()) + [job_id]
    with get_conn() as conn:
        conn.execute(f"UPDATE jobs SET {cols} WHERE id = ?", values)


def set_result(job_id: str, result: dict):
    update_job(job_id, result_json=json.dumps(result), status="done", progress=1.0)


def get_job(job_id: str) -> Optional[dict]:
    with get_conn() as conn:
        row = conn.execute("SELECT * FROM jobs WHERE id = ?", (job_id,)).fetchone()
        if not row:
            return None
        d = dict(row)
        if d.get("result_json"):
            d["result"] = json.loads(d.pop("result_json"))
        else:
            d["result"] = None
            d.pop("result_json", None)
        return d


def list_jobs(limit: int = 50) -> list[dict]:
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT id, source_type, source_ref, title, status, progress, error, created_at, updated_at "
            "FROM jobs ORDER BY created_at DESC LIMIT ?",
            (limit,),
        ).fetchall()
        return [dict(r) for r in rows]


def delete_job(job_id: str) -> bool:
    with get_conn() as conn:
        cur = conn.execute("DELETE FROM jobs WHERE id = ?", (job_id,))
        return cur.rowcount > 0
