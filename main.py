"""Main orchestration helpers for the job scraping project."""
from __future__ import annotations

import argparse
import asyncio
import logging
from pathlib import Path
from typing import Iterable, Sequence

import pandas as pd

from scrapers import JobListing, merge_job_lists
from scrapers.arbetsformedlingen import ArbetsformedlingenScraper
from scrapers.tng import TNGScraper
from utils.database import DEFAULT_DB_PATH, load_job_listings, save_job_listings
from utils.groq_client import GroqJobAnnotator

logger = logging.getLogger(__name__)

JOB_COLUMNS = [
    "title",
    "company",
    "location",
    "url",
    "source",
    "published_at",
    "last_application_date",
    "description",
    "employment_type",
    "categories",
    "summary",
]


async def collect_jobs(
    *,
    job_title: str | None = None,
    location: str | None = None,
    limit: int | None = None,
    use_groq: bool = False,
) -> list[JobListing]:
    """Fetch jobs from all scrapers concurrently and return the combined list."""
    scrapers = [
        ArbetsformedlingenScraper(),
        TNGScraper(),
    ]
    job_lists: list[list[JobListing]] = []
    for scraper in scrapers:
        try:
            result = await scraper.fetch_jobs(job_title=job_title, location=location, limit=limit)
        except Exception as exc:  # pragma: no cover - defensive guard for runtime scraping errors
            logger.warning("%s scraper failed: %s", scraper.source, exc)
            continue
        job_lists.append(result)

    jobs = merge_job_lists(job_lists)

    if use_groq and jobs:
        annotator = GroqJobAnnotator()
        if annotator.enabled:
            await annotator.enrich_jobs(jobs)
        else:
            logger.info("Skipping Groq enrichment; GROQ_API_KEY is not set.")

    return jobs


def jobs_to_dataframe(jobs: Iterable[JobListing] | Iterable[dict]) -> pd.DataFrame:
    """Convert job listings or dictionaries to a tidy Pandas DataFrame."""
    rows = []
    for job in jobs:
        if isinstance(job, JobListing):
            record = job.to_dict()
        else:
            record = dict(job)
        rows.append(record)

    if not rows:
        return pd.DataFrame(columns=JOB_COLUMNS)

    df = pd.DataFrame(rows)
    if "categories" in df.columns:
        df["categories"] = df["categories"].apply(
            lambda value: ", ".join(value) if isinstance(value, list) else (value or "")
        )
    if "last_application_date" in df.columns:
        dates = pd.to_datetime(df["last_application_date"], errors="coerce")
        df["last_application_date"] = dates.dt.strftime("%Y-%m-%dT%H:%M:%S")
        df.loc[dates.isna(), "last_application_date"] = ""

    for column in JOB_COLUMNS:
        if column not in df.columns:
            df[column] = ""

    ordered_columns = JOB_COLUMNS + [col for col in df.columns if col not in JOB_COLUMNS]
    return df[ordered_columns]


def load_jobs_dataframe_from_db(
    *,
    db_path: Path | None = None,
    job_title: str | None = None,
    location: str | None = None,
    sources: Sequence[str] | None = None,
) -> pd.DataFrame:
    """Materialise job listings from SQLite into a dataframe."""
    records = load_job_listings(db_path=db_path, job_title=job_title, location=location, sources=sources)
    return jobs_to_dataframe(records)


def export_to_csv(df: pd.DataFrame, output_path: Path) -> Path:
    """Persist the dataframe to CSV and return the file path."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(output_path, index=False)
    return output_path


def export_to_json(df: pd.DataFrame, output_path: Path) -> Path:
    """Persist the dataframe to JSON and return the file path."""
    output_path.parent.mkdir(parents=True, exist_ok=True)
    df.to_json(output_path, orient="records", force_ascii=False, indent=2)
    return output_path


def persist_jobs(jobs: Iterable[JobListing], *, db_path: Path | None = None) -> int:
    """Store the provided jobs in SQLite and return the number of upserts."""
    return save_job_listings(jobs, db_path=db_path)


def collect_jobs_sync(**kwargs) -> list[JobListing]:
    """Synchronous helper for environments that do not manage an event loop."""
    return asyncio.run(collect_jobs(**kwargs))


def parse_args() -> argparse.Namespace:
    """Parse CLI arguments to run the scrapers from the command line."""
    parser = argparse.ArgumentParser(description="Collect Swedish job postings from multiple sources.")
    parser.add_argument("--title", dest="job_title", help="Job title or keywords to search for.")
    parser.add_argument("--location", help="Preferred job location (city or region).")
    parser.add_argument("--limit", type=int, help="Maximum number of jobs per source (omit for all available).")
    parser.add_argument(
        "--groq",
        action="store_true",
        help="Enrich results with Groq summaries (requires GROQ_API_KEY).",
    )
    parser.add_argument("--db", type=Path, default=DEFAULT_DB_PATH, help="Path to the SQLite database file.")
    parser.add_argument("--csv", type=Path, help="Optional CSV file to export the results to.")
    parser.add_argument("--json", type=Path, help="Optional JSON file to export the results to.")
    return parser.parse_args()


def main() -> None:
    """Command-line entrypoint used during development and testing."""
    logging.basicConfig(level=logging.INFO, format="[%(levelname)s] %(message)s")
    args = parse_args()
    jobs = collect_jobs_sync(job_title=args.job_title, location=args.location, limit=args.limit, use_groq=args.groq)
    upserts = persist_jobs(jobs, db_path=args.db)
    df = jobs_to_dataframe(jobs)
    logger.info("Fetched %s jobs (%s upserted into %s)", len(df), upserts, args.db)

    if args.csv:
        export_to_csv(df, args.csv)
        logger.info("Exported CSV to %s", args.csv)
    if args.json:
        export_to_json(df, args.json)
        logger.info("Exported JSON to %s", args.json)


if __name__ == "__main__":
    main()
