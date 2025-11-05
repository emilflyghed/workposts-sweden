"""Common data structures and helpers shared across scraper modules."""
from __future__ import annotations

import asyncio
from abc import ABC, abstractmethod
from dataclasses import dataclass, field, asdict
from datetime import datetime
from typing import Any, Iterable

import requests

REQUEST_TIMEOUT = 15
DEFAULT_HEADERS = {
    "User-Agent": "Mozilla/5.0 (compatible; HackathonJobBot/1.0; +https://example.com/)",
    "Accept-Language": "sv-SE,sv;q=0.9,en-US;q=0.8,en;q=0.7",
}


@dataclass(slots=True)
class JobListing:
    """Lightweight representation of a single job posting."""

    title: str
    company: str
    location: str
    url: str
    source: str
    published_at: datetime | None = None
    last_application_date: datetime | None = None
    description: str | None = None
    employment_type: str | None = None
    categories: list[str] = field(default_factory=list)
    summary: str | None = None

    def to_dict(self) -> dict[str, Any]:
        """Return a serialisable dictionary representation of the job."""
        payload = asdict(self)
        if self.published_at:
            payload["published_at"] = self.published_at.isoformat()
        if self.last_application_date:
            payload["last_application_date"] = self.last_application_date.isoformat()
        return payload


class BaseScraper(ABC):
    """Base class implementing shared networking helpers for scrapers."""

    source: str = "unknown"

    def __init__(self, session: requests.Session | None = None) -> None:
        self._session = session or requests.Session()
        self._session.headers.update(DEFAULT_HEADERS)

    @abstractmethod
    async def fetch_jobs(
        self,
        *,
        job_title: str | None = None,
        location: str | None = None,
        limit: int = 20,
    ) -> list[JobListing]:
        """Fetch job postings and return them as JobListing objects."""

    async def _request_json(self, url: str, params: dict[str, Any] | None = None) -> dict[str, Any]:
        """Perform a GET request and return the JSON body."""
        response = await self._request(url, params=params)
        try:
            return response.json()
        except ValueError as exc:  # pragma: no cover - defensive guard
            raise RuntimeError(f"{self.source} returned invalid JSON") from exc

    async def _request(self, url: str, params: dict[str, Any] | None = None) -> requests.Response:
        """Execute a blocking HTTP GET inside a worker thread."""
        loop = asyncio.get_running_loop()

        def _do_request() -> requests.Response:
            response = self._session.get(url, params=params, timeout=REQUEST_TIMEOUT)
            response.raise_for_status()
            return response

        return await loop.run_in_executor(None, _do_request)

    @staticmethod
    def normalise_text(value: Any) -> str:
        """Collapse whitespace and strip a text value while keeping fallbacks."""
        if value is None:
            return ""
        if isinstance(value, dict):
            # prefer common textual keys if present
            for key in ("text", "label", "name", "value"):
                if key in value and isinstance(value[key], str):
                    return BaseScraper.normalise_text(value[key])
            value = " ".join(str(part) for part in value.values())
        elif isinstance(value, (list, tuple, set)):
            value = " ".join(str(part) for part in value)
        else:
            value = str(value)
        return " ".join(value.split())


def merge_job_lists(lists: Iterable[Iterable[JobListing]]) -> list[JobListing]:
    """Flatten job listings returned from multiple scrapers."""
    return [job for sublist in lists for job in sublist]
