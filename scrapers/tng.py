"""Playwright-powered scraper for TNG job listings."""
from __future__ import annotations

from typing import Any

from bs4 import BeautifulSoup

from . import BaseScraper, JobListing
from utils.browser import launch_browser

API_URL = "https://www.tng.se/wp-json/wp/v2/tng_job"


class TNGScraper(BaseScraper):
    """Scrape job postings listed on TNG using their WordPress API via Playwright."""

    source = "TNG"

    async def fetch_jobs(
        self,
        *,
        job_title: str | None = None,
        location: str | None = None,
        limit: int = 20,
    ) -> list[JobListing]:
        jobs: list[JobListing] = []
        per_page = min(limit, 50)
        page = 1
        search_query = job_title or ""

        async with launch_browser() as browser:
            context = await browser.new_context(locale="sv-SE")
            request = context.request
            try:
                while len(jobs) < limit:
                    params: dict[str, Any] = {
                        "page": page,
                        "per_page": per_page,
                        "_fields": "id,title,link,excerpt,content,acf",
                    }
                    if search_query:
                        params["search"] = search_query

                    response = await request.get(API_URL, params=params, timeout=15000)
                    if response.status != 200:
                        break
                    data = await response.json()
                    if not isinstance(data, list) or not data:
                        break

                    for entry in data:
                        job = self._parse_entry(entry)
                        if not job:
                            continue
                        if location and not self._matches_location(job.location, location):
                            continue
                        jobs.append(job)
                        if len(jobs) >= limit:
                            break

                    if len(data) < per_page:
                        break
                    page += 1
            finally:
                await context.close()

        return jobs

    def _parse_entry(self, entry: dict[str, Any]) -> JobListing | None:
        title_html = entry.get("title", {}).get("rendered")
        link = entry.get("link")
        if not title_html or not link:
            return None

        title = self.normalise_text(BeautifulSoup(title_html, "html.parser").get_text())
        excerpt_html = entry.get("excerpt", {}).get("rendered") or ""
        description_html = entry.get("content", {}).get("rendered") or excerpt_html
        description = self._clean_html(description_html)

        acf = entry.get("acf") or {}
        company = self.normalise_text(acf.get("employer") or acf.get("client") or "TNG")
        location_text = self.normalise_text(acf.get("location") or acf.get("job_location") or "Sweden")

        return JobListing(
            title=title or "Unknown job",
            company=company or "TNG",
            location=location_text or "Sweden",
            url=link,
            source=self.source,
            description=description,
        )

    def _clean_html(self, html: str) -> str:
        if not html:
            return ""
        soup = BeautifulSoup(html, "html.parser")
        return self.normalise_text(soup.get_text())

    @staticmethod
    def _matches_location(job_location: str, desired_location: str) -> bool:
        job_normalised = "".join(ch for ch in job_location.lower() if ch.isalnum() or ch.isspace())
        desired_normalised = "".join(ch for ch in desired_location.lower() if ch.isalnum() or ch.isspace())
        return desired_normalised in job_normalised
