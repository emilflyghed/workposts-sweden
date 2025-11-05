"""Playwright-powered scraper for Arbetsformedlingen."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from . import BaseScraper, JobListing
from utils.browser import launch_browser

API_URL = "https://jobsearch.api.jobtechdev.se/search"

MUNICIPALITY_CODE_MAP: dict[str, str] = {
    "stockholm": "0180",
    "goteborg": "1480",
    "malmo": "1280",
    "uppsala": "0380",
    "vasteras": "1980",
    "orebro": "1880",
    "linkoping": "0580",
    "helsingborg": "1283",
    "norrkoping": "0581",
    "umea": "2280",
    "jonkoping": "0680",
}

PAGE_SIZE = 100


class ArbetsformedlingenScraper(BaseScraper):
    """Collect job postings by leveraging Playwright's request API."""

    source = "Arbetsformedlingen"

    async def fetch_jobs(
        self,
        *,
        job_title: str | None = None,
        location: str | None = None,
        limit: int | None = None,
    ) -> list[JobListing]:
        params: dict[str, Any] = {
            "limit": PAGE_SIZE,
            "offset": 0,
        }
        if job_title:
            params["q"] = job_title

        municipality_code = self._municipality_code(location) if location else None
        if municipality_code:
            params["municipality"] = municipality_code
        elif location:
            params["q"] = f"{job_title or ''} {location}".strip()

        jobs: list[JobListing] = []
        async with launch_browser() as browser:
            context = await browser.new_context(locale="sv-SE")
            try:
                while True:
                    response = await context.request.get(API_URL, params=params, timeout=20000)
                    if response.status != 200:
                        break
                    data = await response.json()
                    hits: list[dict[str, Any]] = data.get("hits", []) if isinstance(data, dict) else []
                    if not hits:
                        break

                    for hit in hits:
                        jobs.append(self._parse_hit(hit))
                        if limit is not None and len(jobs) >= limit:
                            break
                    if limit is not None and len(jobs) >= limit:
                        break

                    params["offset"] += PAGE_SIZE
            finally:
                await context.close()

        if limit is not None:
            return jobs[:limit]
        return jobs

    @staticmethod
    def _municipality_code(location: str | None) -> str | None:
        if not location:
            return None
        key = "".join(ch for ch in location.lower() if ch.isalnum())
        return MUNICIPALITY_CODE_MAP.get(key)

    @staticmethod
    def _parse_hit(hit: dict[str, Any]) -> JobListing:
        company = ArbetsformedlingenScraper._extract_company(hit)
        location_text = ArbetsformedlingenScraper._extract_location(hit)
        description = ArbetsformedlingenScraper._extract_description(hit)
        categories = ArbetsformedlingenScraper._extract_categories(hit)
        published = ArbetsformedlingenScraper._parse_datetime(hit.get("publication_date"))
        last_application = ArbetsformedlingenScraper._extract_application_deadline(hit)
        url = ArbetsformedlingenScraper._extract_url(hit)

        return JobListing(
            title=BaseScraper.normalise_text(hit.get("headline") or "Unknown job"),
            company=company,
            location=location_text,
            url=url,
            source=ArbetsformedlingenScraper.source,
            published_at=published,
            last_application_date=last_application,
            description=description,
            employment_type=BaseScraper.normalise_text(hit.get("employment_type")),
            categories=categories,
        )

    @staticmethod
    def _extract_company(hit: dict[str, Any]) -> str:
        employer = hit.get("employer") or {}
        return BaseScraper.normalise_text(employer.get("name") or "Not specified")

    @staticmethod
    def _extract_location(hit: dict[str, Any]) -> str:
        addresses = hit.get("workplace_addresses") or hit.get("workplace_address") or []
        if isinstance(addresses, dict):
            addresses = [addresses]
        parts = []
        for address in addresses:
            city = BaseScraper.normalise_text(address.get("municipality"))
            region = BaseScraper.normalise_text(address.get("region"))
            country = BaseScraper.normalise_text(address.get("country"))
            location = ", ".join(part for part in [city, region, country] if part)
            if location:
                parts.append(location)
        return parts[0] if parts else "Sweden"

    @staticmethod
    def _extract_description(hit: dict[str, Any]) -> str | None:
        description = hit.get("description")
        if isinstance(description, dict):
            return BaseScraper.normalise_text(description.get("text"))
        return BaseScraper.normalise_text(description)

    @staticmethod
    def _extract_categories(hit: dict[str, Any]) -> list[str]:
        keywords = hit.get("keywords") or []
        if not isinstance(keywords, list):
            return []
        labels: list[str] = []
        for keyword in keywords:
            if isinstance(keyword, dict):
                value = keyword.get("label") or keyword.get("concept_label")
            else:
                value = str(keyword)
            value = BaseScraper.normalise_text(value)
            if value:
                labels.append(value)
        return labels

    @staticmethod
    def _parse_datetime(raw: str | None) -> datetime | None:
        if not raw:
            return None
        raw = raw.strip()
        if not raw:
            return None
        if raw.endswith('Z'):
            raw = raw[:-1] + '+00:00'
        try:
            dt = datetime.fromisoformat(raw)
        except ValueError:
            dt = None
            for fmt in ("%Y-%m-%dT%H:%M:%S.%f", "%Y-%m-%dT%H:%M:%S", "%Y-%m-%d"):
                try:
                    dt = datetime.strptime(raw, fmt)
                    break
                except ValueError:
                    continue
            if dt is None:
                return None
        if dt.tzinfo is not None:
            return dt.astimezone(timezone.utc)
        return dt

    @staticmethod
    def _extract_application_deadline(hit: dict[str, Any]) -> datetime | None:
        raw = (
            hit.get('application_deadline')
            or hit.get('last_application_date')
            or hit.get('application_last_date')
        )
        if isinstance(raw, dict):
            raw = raw.get('date') or raw.get('text')
        if isinstance(raw, list) and raw:
            raw = raw[0]
        if not isinstance(raw, str):
            raw = BaseScraper.normalise_text(raw)
        return ArbetsformedlingenScraper._parse_datetime(raw)


    @staticmethod
    def _extract_url(hit: dict[str, Any]) -> str:
        links = hit.get("links") or {}
        if isinstance(links, dict):
            apply_url = links.get("apply") or links.get("self")
            if isinstance(apply_url, str) and apply_url:
                return apply_url
        url = hit.get("webpage_url") or hit.get("application_mail") or ""
        return BaseScraper.normalise_text(url)
