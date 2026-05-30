"""Crop just the scholarships rail section for close inspection. Server on :3000."""
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(r"C:\Users\HP\scholarai-platform\frontend\audit-out\phase12")

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    pg.goto("http://localhost:3000/", wait_until="load", timeout=30000)
    pg.wait_for_timeout(2500)
    sec = pg.locator("#scholarships")
    sec.scroll_into_view_if_needed()
    pg.wait_for_timeout(800)
    sec.screenshot(path=str(OUT / "rail-crop.png"))
    print("rail crop saved")
    b.close()
