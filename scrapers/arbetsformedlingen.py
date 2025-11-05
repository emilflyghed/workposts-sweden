"""Scraper for the Arbetsformedlingen JobTech public API."""
from __future__ import annotations

from datetime import datetime
from typing import Any

from . import BaseScraper, JobListing

API_URL = "https://jobsearch.api.jobtechdev.se/search"


class ArbetsformedlingenScraper(BaseScraper):
    """Collect job postings from Arbetsformedlingen's public JobTech API."""

    source = "Arbetsformedlingen"

    async def fetch_jobs(
        self,
        *,
        job_title: str | None = None,
        location: str | None = None,
        limit: int = 20,
    ) -> list[JobListing]:
        """Call the public API and return parsed job listings."""
        params: dict[str, Any] = {
            "limit": limit,
            "q": job_title or "",
            "offset": 0,
        }
        if location:
            params["municipality"] = location

        data = await self._request_json(API_URL, params=params)
        hits: list[dict[str, Any]] = data.get("hits", [])
        jobs: list[JobListing] = []
        for hit in hits:
            company = self._extract_company(hit)
            location_text = self._extract_location(hit)
            description = self._extract_description(hit)
            categories = self._extract_categories(hit)
            published = self._parse_datetime(hit.get("publication_date"))
            url = self._extract_url(hit)

            jobs.append(
                JobListing(
                    title=self.normalise_text(hit.get("headline") or "Unknown job"),
                    company=company,
                    location=location_text,
                    url=url,
                    source=self.source,
                    published_at=published,
                    description=description,
                    employment_type=self.normalise_text(hit.get("employment_type")),
                    categories=categories,
                )
            )
        return jobs

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
        for fmt in ("%Y-%m-%dT%H:%M:%S.%fZ", "%Y-%m-%dT%H:%M:%SZ", "%Y-%m-%d"):
            try:
                return datetime.strptime(raw, fmt)
            except ValueError:
                continue
        return None

    @staticmethod
    def _extract_url(hit: dict[str, Any]) -> str:
        links = hit.get("links") or {}
        if isinstance(links, dict):
            apply_url = links.get("apply") or links.get("self")
            if isinstance(apply_url, str) and apply_url:
                return apply_url
        url = hit.get("webpage_url") or hit.get("application_mail") or ""
        return BaseScraper.normalise_text(url)
