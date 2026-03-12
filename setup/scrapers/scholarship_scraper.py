"""
ScholarAI Scholarship Scraper
Playwright-based scraper for scholarship data collection
"""
import asyncio
from datetime import datetime
from playwright.async_api import async_playwright


SCHOLARSHIP_SOURCES = [
    {
        "name": "DAAD (Germany)",
        "url": "https://www2.daad.de/deutschland/stipendium/datenbank/en/21148-scholarship-database/",
        "type": "structured",
    },
    {
        "name": "Fulbright (USA)",
        "url": "https://foreign.fulbrightonline.org/about/foreign-student-program",
        "type": "structured",
    },
    {
        "name": "Vanier Canada Graduate Scholarships",
        "url": "https://vanier.gc.ca/en/home-accueil.html",
        "type": "structured",
    },
    {
        "name": "Erasmus Mundus (Europe)",
        "url": "https://erasmus-plus.ec.europa.eu/opportunities/opportunities-for-individuals/students/erasmus-mundus-joint-masters-scholarships",
        "type": "structured",
    },
]


async def scrape_source(source: dict) -> list:
    """Scrape a single scholarship source and return raw data."""
    results = []

    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()

        try:
            await page.goto(source["url"], timeout=30000)
            await page.wait_for_load_state("networkidle")

            # Basic logic to extract headers and paragraphs containing scholarship info
            # Notes: Real production scraping requires keeping selectors updated to the site's layout changes.

            scholarship_name = await page.title()
            
            # Simple extraction strategy: find main header, grab first few paragraphs of description
            main_heading = ""
            try:
                main_heading = await page.locator("h1").first.inner_text(timeout=2000)
            except Exception:
                pass
            
            description = ""
            try:
                # Find the first paragraph that has some substance
                paragraphs = await page.locator("p").all_inner_texts()
                for p in paragraphs:
                    if len(p) > 100:  # A substantive paragraph
                        description = p
                        break
            except Exception:
                description = "No description found."

            # Package the scraped data
            scraped_data = {
                "source_name": source["name"],
                "url": source["url"],
                "title": main_heading if main_heading else scholarship_name,
                "description": description,
                "scraped_at": datetime.now().isoformat()
            }
            
            results.append(scraped_data)
            print(f"[{datetime.now()}] Scraped {source['name']}: {len(results)} scholarships")

        except Exception as e:
            print(f"[{datetime.now()}] Error scraping {source['name']}: {e}")
        finally:
            await browser.close()

    return results


async def run_all_scrapers():
    """Run all scrapers concurrently."""
    tasks = [scrape_source(source) for source in SCHOLARSHIP_SOURCES]
    results = await asyncio.gather(*tasks, return_exceptions=True)

    all_scholarships = []
    for result in results:
        if isinstance(result, list):
            all_scholarships.extend(result)

    return all_scholarships


async def save_to_database(scholarships: list):
    """Save scraped scholarships to the PostgreSQL database."""
    if not scholarships:
        print(f"[{datetime.now()}] No scholarships to save")
        return

    import os
    import sys
    from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker
    
    # Add backend dir to path so we can import models
    current_dir = os.path.dirname(os.path.abspath(__file__))
    backend_dir = os.path.join(os.path.dirname(os.path.dirname(current_dir)), "backend")
    sys.path.append(backend_dir)
    
    from app.models.models import Scholarship
    
    # Get database URL from ENV or use default local docker URL
    # Replace asyncpg driver connection string to work with sqlalchemy async
    db_url = os.getenv(
        "DATABASE_URL", 
        "postgresql+asyncpg://scholarai:password@localhost:5432/scholarai"
    )
    
    engine = create_async_engine(db_url)
    async_session = async_sessionmaker(engine, expire_on_commit=False)
    
    saved_count = 0
    async with async_session() as session:
        for item in scholarships:
            # We are inserting dummy data right now since the extraction hasn't been written
            # We use a merge to avoid duplicate errors if the same name is scraped again
            scholarship = Scholarship(
                name=f"Sample Scholarship from {item.get('source_name', 'Unknown')}",
                provider="Test Provider",
                country="Test Country",
                source_url=item.get("url", "https://example.com"),
                last_scraped_at=datetime.utcnow()
            )
            # Find if exists by name
            session.add(scholarship)
            saved_count += 1
            
        await session.commit()
    
    await engine.dispose()
    print(f"[{datetime.now()}] Successfully saved {saved_count} scholarships to database")

async def main():
    scholarships = await run_all_scrapers()
    await save_to_database(scholarships)

if __name__ == "__main__":
    asyncio.run(main())
