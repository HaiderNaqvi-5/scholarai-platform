"""Phase 3 visual verification: pricing drench + password meter. Server on :3000."""
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(r"C:\Users\HP\scholarai-platform\frontend\audit-out\phase12")
OUT.mkdir(parents=True, exist_ok=True)


def wait_ready(pg):
    pg.wait_for_timeout(2000)


with sync_playwright() as p:
    b = p.chromium.launch(headless=True)

    # 1. Landing pricing section (drenched Elite cell)
    pg = b.new_page(viewport={"width": 1440, "height": 900})
    errs = []
    pg.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
    pg.goto("http://localhost:3000/", wait_until="load", timeout=30000)
    wait_ready(pg)
    # pricing section is the one containing "Start free."
    heading = pg.get_by_text("Start free. Upgrade when").first
    heading.scroll_into_view_if_needed()
    pg.wait_for_timeout(600)
    pg.screenshot(path=str(OUT / "pricing-drench.png"))
    print(f"pricing shot done; console_errors={len(errs)}")
    pg.close()

    # 2. Signup password meter — type a partial password to reveal it
    pg2 = b.new_page(viewport={"width": 1024, "height": 1200})
    errs2 = []
    pg2.on("console", lambda m: errs2.append(m.text) if m.type == "error" else None)
    pg2.goto("http://localhost:3000/signup", wait_until="load", timeout=30000)
    wait_ready(pg2)
    pw = pg2.locator("#signup-password")
    if pw.count() > 0:
        pw.fill("Abc123")  # weak: has upper/lower/number, <12, no symbol
        pg2.wait_for_timeout(500)
        meter = pg2.locator("#signup-password-meter")
        print(f"meter visible (weak)={meter.count()}")
        pg2.screenshot(path=str(OUT / "pwmeter-weak.png"), full_page=True)
        pw.fill("Abcdef123!@#xyz")  # strong: all criteria
        pg2.wait_for_timeout(500)
        pg2.screenshot(path=str(OUT / "pwmeter-strong.png"), full_page=True)
    else:
        print("WARN: no #signup-password (clerk mode renders different form?)")
    print(f"signup console_errors={len(errs2)}")
    pg2.close()
    b.close()
print("done")
