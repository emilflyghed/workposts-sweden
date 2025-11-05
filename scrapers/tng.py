"""HTML scraper for TNG (Swedish recruitment agency)."""
from __future__ import annotations

from typing import Any
from urllib.parse import urlencode, urljoin

from bs4 import BeautifulSoup

from . import BaseScraper, JobListing

BASE_URL = "https://www.tng.se/lediga-jobb/"


class TNGScraper(BaseScraper):
    """Scrape job postings listed on TNG."""

    source = "TNG"

    async def fetch_jobs(
        self,
        *,
        job_title: str | None = None,
        location: str | None = None,
        limit: int = 20,
    ) -> list[JobListing]:
        """Scrape the listing page and convert entries to JobListing objects."""
        url = self._build_url(job_title, location)
        response = await self._request(url)
        soup = BeautifulSoup(response.text, "html.parser")
        cards = soup.select("article.job-list__item, div.job-listing__item")
        jobs: list[JobListing] = []
        for card in cards:
            title_link = card.select_one("a.job-list__link, a.job-listing__link")
            if not title_link:
                continue
            title = self.normalise_text(title_link.get_text())
            link = urljoin(BASE_URL, title_link.get("href") or "")
            company = self._parse_company(card)
            location_text = self._parse_location(card)
            snippet = self._parse_snippet(card)

            jobs.append(
                JobListing(
                    title=title or "Unknown job",
                    company=company,
                    location=location_text,
                    url=link,
                    source=self.source,
                    description=snippet,
                )
            )
            if len(jobs) >= limit:
                break
        return jobs

    @staticmethod
    def _build_url(job_title: str | None, location: str | None) -> str:
        params: dict[str, Any] = {}
        if job_title:
            params["s"] = job_title
        if location:
            params["location"] = location
        if not params:
            return BASE_URL
        return f"{BASE_URL}?{urlencode(params)}"

    @staticmethod
    def _parse_company(card: BeautifulSoup) -> str:
        company_node = card.select_one("span.job-list__company, span.job-listing__company")
        if company_node:
            return BaseScraper.normalise_text(company_node.get_text())
        return "TNG"

    @staticmethod
    def _parse_location(card: BeautifulSoup) -> str:
        location_node = card.select_one("span.job-list__location, span.job-listing__location")
        if location_node:
            return BaseScraper.normalise_text(location_node.get_text())
        return "Sweden"

    @staticmethod
    def _parse_snippet(card: BeautifulSoup) -> str:
        snippet_node = card.select_one("p.job-list__excerpt, div.job-listing__excerpt")
        if snippet_node:
            return BaseScraper.normalise_text(snippet_node.get_text())
        return ""
