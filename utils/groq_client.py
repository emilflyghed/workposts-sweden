"""Helpers for working with the Groq LLM service."""
from __future__ import annotations

import asyncio
import os
from typing import Iterable, TYPE_CHECKING

from groq import Groq

if TYPE_CHECKING:  # pragma: no cover - import used for type checking only
    from scrapers import JobListing


class GroqJobAnnotator:
    """Wrap the Groq client to classify and summarise job postings."""

    def __init__(self, *, model: str = "llama3-8b-8192", api_key: str | None = None, max_concurrency: int = 3) -> None:
        self.api_key = api_key or os.getenv("GROQ_API_KEY")
        self.model = model
        self.max_concurrency = max(1, max_concurrency)
        self._client: Groq | None = None
        if self.api_key:
            self._client = Groq(api_key=self.api_key)
        self.enabled = self._client is not None

    async def enrich_jobs(self, jobs: Iterable["JobListing"]) -> None:
        """Populate the summary field on each job listing using Groq."""
        if not self.enabled or not self._client:
            return

        semaphore = asyncio.Semaphore(self.max_concurrency)
        tasks = [self._annotate_with_semaphore(job, semaphore) for job in jobs]
        await asyncio.gather(*tasks)

    async def _annotate_with_semaphore(self, job: "JobListing", semaphore: asyncio.Semaphore) -> None:
        """Guard Groq usage with a semaphore to avoid spamming the API."""
        async with semaphore:
            job.summary = await self.summarise_job(job)

    async def summarise_job(self, job: "JobListing") -> str | None:
        """Return a concise summary for the provided job using the LLM."""
        if not self.enabled or not self._client:
            return None
        return await asyncio.to_thread(self._summarise_job_sync, job)

    def _summarise_job_sync(self, job: "JobListing") -> str | None:
        """Blocking helper that performs the Groq API call."""
        try:
            response = self._client.chat.completions.create(  # type: ignore[union-attr]
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": (
                            "You assist recruiters. Highlight the core skills, experience level, "
                            "and a short takeaway from the job description."
                        ),
                    },
                    {
                        "role": "user",
                        "content": (
                            f"Job title: {job.title}\n"
                            f"Company: {job.company}\n"
                            f"Location: {job.location}\n"
                            f"Description: {job.description or 'No description available.'}\n"
                            "Respond in English using no more than three sentences."
                        ),
                    },
                ],
                temperature=0.3,
                max_tokens=200,
            )
        except Exception:  # pragma: no cover - defensive guard to keep pipeline running
            return None
        choice = response.choices[0]
        return choice.message.content.strip() if choice.message and choice.message.content else None
