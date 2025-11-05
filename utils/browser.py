"""Helpers for working with Playwright browser instances."""
from __future__ import annotations

from contextlib import asynccontextmanager
from typing import AsyncIterator

from playwright.async_api import Browser, async_playwright


@asynccontextmanager
async def launch_browser(*, headless: bool = True, locale: str = "sv-SE") -> AsyncIterator[Browser]:
    """Launch a Chromium browser and yield it within a managed context."""
    async with async_playwright() as playwright:
        browser = await playwright.chromium.launch(headless=headless)
        try:
            yield browser
        finally:
            await browser.close()
