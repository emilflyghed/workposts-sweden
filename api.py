"""REST API for job scraping and retrieval."""
from __future__ import annotations

from typing import Optional

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from main import collect_jobs_sync, persist_jobs
from utils.database import load_job_listings

app = FastAPI(title="Job Scraper API", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ScrapeRequest(BaseModel):
    job_title: Optional[str] = None
    location: Optional[str] = None
    limit: Optional[int] = None
    use_groq: bool = False


class ScrapeResponse(BaseModel):
    fetched: int
    upserted: int


@app.get("/health")
def healthcheck() -> dict[str, str]:
    """Simple healthcheck endpoint."""
    return {"status": "ok"}


@app.get("/jobs")
def list_jobs(
    title: Optional[str] = None,
    location: Optional[str] = None,
    source: Optional[str] = None,
) -> dict[str, list[dict]]:
    """Return jobs stored in SQLite, optionally filtered by title/location/source."""
    sources = None
    if source:
        sources = [s.strip() for s in source.split(",") if s.strip()]
    records = load_job_listings(job_title=title, location=location, sources=sources)
    return {"jobs": records}


@app.get("/jobs/{job_id}")
def get_job(job_id: int) -> dict:
    """Return a single job by its primary key."""
    records = load_job_listings()
    for job in records:
        if job.get("id") == job_id:
            return job
    raise HTTPException(status_code=404, detail="Job not found")


@app.post("/scrape", response_model=ScrapeResponse)
def scrape_jobs(request: ScrapeRequest) -> ScrapeResponse:
    """Trigger the scrapers and persist the results to SQLite."""
    jobs = collect_jobs_sync(
        job_title=request.job_title,
        location=request.location,
        limit=request.limit,
        use_groq=request.use_groq,
    )
    upserts = persist_jobs(jobs)
    return ScrapeResponse(fetched=len(jobs), upserted=upserts)
