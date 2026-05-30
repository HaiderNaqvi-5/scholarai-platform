"""Phase 4 verification: scroll-progress bar visible after scroll. Server on :3000."""
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(r"C:\Users\HP\scholarai-platform\frontend\audit-out\phase12")

with sync_playwright() as p:
    b = p.chromium.launch(headless=True)
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    errs = []
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.goto("http://localhost:3000/", wait_until="load", timeout=30000)
    pg.wait_for_timeout(1500)
    # Scroll to ~55% so the scroll-progress bar is partially filled.
    pg.evaluate("window.scrollTo(0, document.body.scrollHeight * 0.55)")
    pg.wait_for_timeout(600)
    # Measure the bar's rendered scaleX via getComputedStyle transform.
    info = pg.evaluate(
        """() => {
            const el = document.querySelector('.scroll-progress');
            if (!el) return {present:false};
            const cs = getComputedStyle(el);
            return {present:true, display:cs.display, transform:cs.transform};
        }"""
    )
    print(f"scroll-progress: {info}")
    pg.screenshot(path=str(OUT / "scroll-progress.png"))  # viewport shot, bar at very top
    print(f"console_errors={len(errs)}")
    for e in errs:
        print("  ", e)
    b.close()
print("done")
