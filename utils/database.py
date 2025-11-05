"""SQLite persistence helpers for job listings."""
from __future__ import annotations

import json
import sqlite3
from contextlib import contextmanager
from pathlib import Path
from typing import Iterable, Iterator, Sequence

from scrapers import JobListing

DATA_DIR = Path(__file__).resolve().parent.parent / "data"
DEFAULT_DB_PATH = DATA_DIR / "workposts.db"

SCHEMA_STATEMENTS: Sequence[str] = (
    """
    CREATE TABLE IF NOT EXISTS jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        company TEXT,
        location TEXT,
        url TEXT NOT NULL,
        source TEXT NOT NULL,
        published_at TEXT,
        last_application_date TEXT,
        description TEXT,
        employment_type TEXT,
        categories TEXT,
        summary TEXT,
        created_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        updated_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
        UNIQUE(source, url)
    );
    """.strip(),
    "CREATE INDEX IF NOT EXISTS idx_jobs_source ON jobs(source);",
    "CREATE INDEX IF NOT EXISTS idx_jobs_location ON jobs(location);",
    "CREATE INDEX IF NOT EXISTS idx_jobs_title ON jobs(title);",
)


def ensure_data_dir(path: Path) -> None:
    """Ensure the parent directory for the database exists."""
    path.parent.mkdir(parents=True, exist_ok=True)


def get_connection(db_path: Path | None = None) -> sqlite3.Connection:
    """Return a SQLite connection with sensible defaults."""
    resolved_path = Path(db_path) if db_path else DEFAULT_DB_PATH
    ensure_data_dir(resolved_path)
    conn = sqlite3.connect(resolved_path)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL;")
    conn.execute("PRAGMA foreign_keys=ON;")
    initialise_database(conn)
    return conn


@contextmanager
def connection_scope(db_path: Path | None = None) -> Iterator[sqlite3.Connection]:
    """Context manager that yields a connection and closes it afterwards."""
    conn = get_connection(db_path)
    try:
        yield conn
    finally:
        conn.close()


def initialise_database(conn: sqlite3.Connection) -> None:
    """Create tables and indexes if they are missing."""
    with conn:
        for statement in SCHEMA_STATEMENTS:
            conn.execute(statement)
        _ensure_column(conn, "jobs", "last_application_date", "TEXT")


def save_job_listings(jobs: Iterable[JobListing], conn: sqlite3.Connection | None = None, db_path: Path | None = None) -> int:
    """Persist a collection of job listings, returning the number of upserts."""
    owned_connection = False
    if conn is None:
        conn = get_connection(db_path)
        owned_connection = True

    payloads = []
    for job in jobs:
        record = job.to_dict()
        record["categories"] = json.dumps(record.get("categories") or [])
        record.setdefault("last_application_date", None)
        payloads.append(record)

    if not payloads:
        if owned_connection:
            conn.close()
        return 0

    try:
        baseline_changes = conn.total_changes
        with conn:
            conn.executemany(
                """
                INSERT INTO jobs (
                    title,
                    company,
                    location,
                    url,
                    source,
                    published_at,
                    last_application_date,
                    description,
                    employment_type,
                    categories,
                    summary
                ) VALUES (
                    :title,
                    :company,
                    :location,
                    :url,
                    :source,
                    :published_at,
                    :last_application_date,
                    :description,
                    :employment_type,
                    :categories,
                    :summary
                )
                ON CONFLICT(source, url) DO UPDATE SET
                    title=excluded.title,
                    company=excluded.company,
                    location=excluded.location,
                    published_at=excluded.published_at,
                    last_application_date=excluded.last_application_date,
                    description=excluded.description,
                    employment_type=excluded.employment_type,
                    categories=excluded.categories,
                    summary=excluded.summary,
                    updated_at=CURRENT_TIMESTAMP;
                """,
                payloads,
            )
        return conn.total_changes - baseline_changes
    finally:
        if owned_connection:
            conn.close()


def load_job_listings(
    *,
    conn: sqlite3.Connection | None = None,
    db_path: Path | None = None,
    job_title: str | None = None,
    location: str | None = None,
    sources: Sequence[str] | None = None,
) -> list[dict]:
    """Load job listings from the database applying optional filters."""
    owned_connection = False
    if conn is None:
        conn = get_connection(db_path)
        owned_connection = True

    query = [
        "SELECT id, title, company, location, url, source, published_at, last_application_date, description, employment_type, categories, summary, created_at, updated_at",
        "FROM jobs",
        "WHERE 1=1",
    ]
    params: list = []

    if job_title:
        query.append("AND title LIKE ?")
        params.append(f"%{job_title}%")
    if location:
        query.append("AND location LIKE ?")
        params.append(f"%{location}%")
    if sources:
        placeholders = ",".join("?" for _ in sources)
        query.append(f"AND source IN ({placeholders})")
        params.extend(sources)

    query.append("ORDER BY updated_at DESC, created_at DESC")

    cursor = conn.execute("\n".join(query), params)
    records = []
    for row in cursor.fetchall():
        record = dict(row)
        try:
            record["categories"] = json.loads(record.get("categories") or "[]")
        except json.JSONDecodeError:
            record["categories"] = []
        records.append(record)

    if owned_connection:
        conn.close()

    return records


def _ensure_column(conn: sqlite3.Connection, table: str, column: str, column_type: str) -> None:
    info = conn.execute(f"PRAGMA table_info({table})").fetchall()
    if not any(col[1] == column for col in info):
        conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {column_type}")
