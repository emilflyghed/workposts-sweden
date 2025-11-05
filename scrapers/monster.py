"""HTML scraper for Monster.se job listings."""
from __future__ import annotations

from typing import Any
from urllib.parse import urljoin

from bs4 import BeautifulSoup

from . import BaseScraper, JobListing

SEARCH_URL = "https://www.monster.se/jobb/sok/"


class MonsterScraper(BaseScraper):
    """Parse job cards from Monster using requests + BeautifulSoup."""

    source = "Monster"

    async def fetch_jobs(
        self,
        *,
        job_title: str | None = None,
        location: str | None = None,
        limit: int = 20,
    ) -> list[JobListing]:
        """Scrape Monster search results and build job listings."""
        params = self._build_search_params(job_title, location)
        response = await self._request(SEARCH_URL, params=params)
        soup = BeautifulSoup(response.text, "html.parser")
        cards = soup.select("section.card-content, div.job-cardstyle__JobCard")
        jobs: list[JobListing] = []
        for card in cards:
            title_element = card.select_one("h2 a, a.job-cardstyle__JobTitleAnchor")
            if not title_element:
                continue
            title = self.normalise_text(title_element.get_text())
            if not title:
                continue
            url = urljoin(SEARCH_URL, title_element.get("href") or "")
            company_node = card.select_one("div.company, span.job-cardstyle__JobCompany")
            company = self.normalise_text(company_node.get_text()) if company_node else "Monster"
            location_text = self._parse_location(card)
            description = self._parse_snippet(card)

            jobs.append(
                JobListing(
                    title=title,
                    company=company,
                    location=location_text,
                    url=url,
                    source=self.source,
                    description=description,
                )
            )
            if len(jobs) >= limit:
                break
        return jobs

    @staticmethod
    def _build_search_params(job_title: str | None, location: str | None) -> dict[str, Any]:
        params: dict[str, Any] = {}
        if job_title:
            params["q"] = job_title
        if location:
            params["where"] = location
        return params

    @staticmethod
    def _parse_location(card: BeautifulSoup) -> str:
        location_node = card.select_one("div.location, span.job-cardstyle__JobLocation")
        if location_node:
            return BaseScraper.normalise_text(location_node.get_text())
        return "Sweden"

    @staticmethod
    def _parse_snippet(card: BeautifulSoup) -> str:
        snippet_node = card.select_one("div.summary, div.job-cardstyle__JobDescription")
        if snippet_node:
            return BaseScraper.normalise_text(snippet_node.get_text())
        return ""
