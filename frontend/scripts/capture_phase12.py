"""One-off Phase 1+2 visual verification capture. Server must already run on :3000."""
import sys
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(r"C:\Users\HP\scholarai-platform\frontend\audit-out\phase12")
OUT.mkdir(parents=True, exist_ok=True)

VIEWPORTS = {"mobile": (375, 812), "tablet": (768, 1024), "desktop": (1440, 900)}
SURFACES = [("landing", "http://localhost:3000/"), ("login", "http://localhost:3000/login")]


def main():
    errors = []
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        for sname, url in SURFACES:
            for vname, (w, h) in VIEWPORTS.items():
                page = browser.new_page(viewport={"width": w, "height": h})
                console_errs = []
                page.on("console", lambda m: console_errs.append(m.text) if m.type == "error" else None)
                page.goto(url, wait_until="load", timeout=30000)
                page.wait_for_timeout(2500)  # let rail react-query settle (HMR ws blocks networkidle)
                shot = OUT / f"{sname}-{vname}.png"
                page.screenshot(path=str(shot), full_page=True)
                # Probe Phase 2 landmarks on landing
                probes = {}
                if sname == "landing":
                    probes["rail"] = page.locator('[aria-label="All live scholarships"]').count()
                    probes["comparison"] = page.get_by_text("Lahore consultant").count()
                    probes["cta_match"] = page.get_by_text("Show scholarships I qualify for").count()
                print(f"{sname}/{vname}: shot={shot.name} probes={probes} console_errors={len(console_errs)}")
                for e in console_errs:
                    errors.append(f"[{sname}/{vname}] {e}")
                page.close()
        browser.close()
    if errors:
        print("\n=== CONSOLE ERRORS ===")
        for e in errors:
            print(e)
    else:
        print("\nNo console errors.")


if __name__ == "__main__":
    sys.exit(main())
