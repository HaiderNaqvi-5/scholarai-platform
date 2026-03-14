"""
Scraper service for scholarship ingestion.

This remains intentionally lightweight for the MVP foundation, but it now
matches the current ORM schema and Celery runtime expectations.
"""

from __future__ import annotations

import asyncio
import logging
from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import List, Optional

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.models import Scholarship, ScraperRun

logger = logging.getLogger(__name__)


class ScrapedScholarship:
    def __init__(
        self,
        name: str,
        provider: str,
        country: str,
        source_url: str,
        description: str = "",
        deadline: Optional[date] = None,
        funding_type: str = "full",
        degree_levels: Optional[List[str]] = None,
        field_of_study: Optional[List[str]] = None,
        university: Optional[str] = None,
        amount: Optional[str] = None,
    ):
        self.name = name
        self.provider = provider
        self.country = country
        self.source_url = source_url
        self.description = description
        self.deadline = deadline
        self.funding_type = funding_type
        self.degree_levels = degree_levels or ["master", "phd"]
        self.field_of_study = field_of_study or []
        self.university = university
        self.amount = amount


class ScraperService:
    """Orchestrates source scraping and persists results."""

    SOURCE_NAME_MAP = {
        "daad": "daad",
        "fulbright": "fulbright",
        "scholarships_ca": "scholarships_ca",
        "scholarship_com": "scholarship_com",
    }

    def __init__(self, db: AsyncSession):
        self.db = db

    async def run_all(self) -> dict:
        """Run all configured scrapers and persist a summary."""
        run = ScraperRun(
            source_name="all",
            source_url="multi-source",
            status="running",
            started_at=datetime.utcnow(),
        )
        self.db.add(run)
        await self.db.commit()

        stats = {"sources": {}, "total_new": 0, "total_updated": 0, "errors": []}
        scrapers = [
            ("chevening", self.scrape_chevening),
            ("fulbright", self.scrape_fulbright),
            ("daad", self.scrape_daad),
        ]

        for source_name, scraper_fn in scrapers:
            try:
                items = await scraper_fn()
                new_count, updated_count = await self._upsert_scholarships(items, source_name)
                stats["sources"][source_name] = {"new": new_count, "updated": updated_count}
                stats["total_new"] += new_count
                stats["total_updated"] += updated_count
                logger.info("[%s] new=%s updated=%s", source_name, new_count, updated_count)
            except Exception as exc:
                logger.exception("[%s] scraper error", source_name)
                stats["errors"].append({"source": source_name, "error": str(exc)})

        run.status = "success" if not stats["errors"] else "failed"
        run.completed_at = datetime.utcnow()
        run.scholarships_found = stats["total_new"] + stats["total_updated"]
        run.scholarships_new = stats["total_new"]
        run.scholarships_updated = stats["total_updated"]
        if stats["errors"]:
            run.error_message = "; ".join(
                f"{item['source']}: {item['error']}" for item in stats["errors"]
            )[:2000]
        await self.db.commit()

        return stats

    async def scrape_chevening(self) -> List[ScrapedScholarship]:
        return await self._playwright_scrape(
            url="https://www.chevening.org/scholarships/",
            parse_fn=self._parse_chevening_page,
        )

    async def scrape_fulbright(self) -> List[ScrapedScholarship]:
        return await self._playwright_scrape(
            url="https://foreign.fulbrightonline.org/",
            parse_fn=self._parse_generic_page,
        )

    async def scrape_daad(self) -> List[ScrapedScholarship]:
        return await self._playwright_scrape(
            url="https://www.daad.de/en/study-and-research-in-germany/scholarships/",
            parse_fn=self._parse_generic_page,
        )

    async def _playwright_scrape(self, url: str, parse_fn) -> List[ScrapedScholarship]:
        """Generic Playwright browser automation."""
        from playwright.async_api import async_playwright

        async with async_playwright() as playwright:
            browser = await playwright.chromium.launch(headless=True)
            context = await browser.new_context(
                user_agent="Mozilla/5.0 (X11; Linux x86_64) Chrome/125 ScholarAI-Bot/1.0"
            )
            page = await context.new_page()
            await page.goto(url, wait_until="domcontentloaded", timeout=30_000)
            await asyncio.sleep(2)
            results = await parse_fn(page, url)
            await browser.close()
            return results

    async def _parse_chevening_page(self, page, base_url: str) -> List[ScrapedScholarship]:
        scholarships = []
        cards = await page.query_selector_all(".scholarship-card, .card-scholarship, article.scholarship")

        for card in cards[:20]:
            try:
                name_el = await card.query_selector("h2, h3, .card-title")
                desc_el = await card.query_selector("p, .card-description")
                link_el = await card.query_selector("a")
                name = (await name_el.inner_text()).strip() if name_el else ""
                description = (await desc_el.inner_text()).strip() if desc_el else ""
                href = await link_el.get_attribute("href") if link_el else base_url
                source_url = href if href.startswith("http") else f"https://www.chevening.org{href}"

                if name:
                    scholarships.append(
                        ScrapedScholarship(
                            name=name,
                            provider="Chevening / UK FCDO",
                            country="United Kingdom",
                            source_url=source_url,
                            description=description,
                            degree_levels=["master"],
                            funding_type="full",
                        )
                    )
            except Exception:
                continue

        if scholarships:
            return scholarships

        return [
            ScrapedScholarship(
                name="Chevening Scholarships",
                provider="Chevening / UK FCDO",
                country="United Kingdom",
                source_url="https://www.chevening.org/scholarships/",
                description="UK government scholarship programme for outstanding emerging leaders.",
                degree_levels=["master"],
                funding_type="full",
            )
        ]

    async def _parse_generic_page(self, page, base_url: str) -> List[ScrapedScholarship]:
        title = await page.title()
        return [
            ScrapedScholarship(
                name=title or "Unknown Scholarship",
                provider=base_url.split("/")[2],
                country="International",
                source_url=base_url,
                description=f"Scraped from {base_url}",
            )
        ]

    async def _upsert_scholarships(self, items: List[ScrapedScholarship], tag: str) -> tuple[int, int]:
        """Insert new scholarships or update existing rows matched by source_url."""
        new_count = 0
        updated_count = 0

        for item in items:
            result = await self.db.execute(
                select(Scholarship).where(Scholarship.source_url == item.source_url)
            )
            existing = result.scalar_one_or_none()

            if existing:
                existing.name = item.name
                existing.provider = item.provider
                existing.country = item.country
                existing.university = item.university
                existing.field_of_study = item.field_of_study
                existing.degree_levels = item.degree_levels
                existing.description = item.description or existing.description
                existing.deadline = item.deadline or existing.deadline
                existing.funding_type = item.funding_type
                existing.funding_amount_usd = self._parse_amount(item.amount)
                existing.source_name = self._normalize_source_name(tag)
                existing.is_active = True
                existing.last_scraped_at = datetime.utcnow()
                existing.scholarship_embedding = None
                updated_count += 1
                continue

            scholarship = Scholarship(
                name=item.name,
                provider=item.provider,
                country=item.country,
                source_url=item.source_url,
                description=item.description,
                deadline=item.deadline,
                funding_type=item.funding_type,
                funding_amount_usd=self._parse_amount(item.amount),
                degree_levels=item.degree_levels,
                field_of_study=item.field_of_study,
                university=item.university,
                source_name=self._normalize_source_name(tag),
                is_active=True,
                last_scraped_at=datetime.utcnow(),
            )
            self.db.add(scholarship)
            new_count += 1

        await self.db.commit()
        return new_count, updated_count

    def _normalize_source_name(self, tag: str) -> str:
        return self.SOURCE_NAME_MAP.get(tag, "other")

    @staticmethod
    def _parse_amount(amount: Optional[str]) -> Optional[Decimal]:
        if not amount:
            return None

        cleaned = "".join(ch for ch in amount if ch.isdigit() or ch in {".", ","}).replace(",", "")
        if not cleaned:
            return None

        try:
            return Decimal(cleaned)
        except InvalidOperation:
            return None
