"""Wave 2 verification: autoplay rail, hover-pause, reduced-motion, arrows,
FAQ chips, footer chip. Server on :3000 + backend on :8000 must be up."""
from pathlib import Path
from playwright.sync_api import sync_playwright

OUT = Path(r"C:\Users\HP\scholarai-platform\frontend\audit-out\phase12")
OUT.mkdir(parents=True, exist_ok=True)


def main():
    with sync_playwright() as p:
        b = p.chromium.launch(headless=True)
        # ===== 1) Default motion: confirm autoplay advances scrollLeft =====
        ctx = b.new_context(viewport={"width": 1440, "height": 900})
        page = ctx.new_page()
        errs = []
        page.on("console", lambda m: errs.append(m.text) if m.type == "error" else None)
        page.goto("http://localhost:3000/", wait_until="load", timeout=60000)
        page.get_by_text("Real, fully-funded").first.scroll_into_view_if_needed()
        ul_sel = '[aria-label="All live scholarships"]'
        try:
            page.wait_for_function(
                f"() => document.querySelectorAll('{ul_sel} > li').length >= 4",
                timeout=15000,
            )
        except Exception as e:
            print(f"WAIT-FOR-CARDS failed: {e}")
        cards = page.evaluate(
            f"() => document.querySelectorAll('{ul_sel} > li').length"
        )
        print(f"RAIL cards rendered: {cards}")
        s0 = page.evaluate(f"() => document.querySelector('{ul_sel}')?.scrollLeft ?? -1")
        page.wait_for_timeout(6000)  # > one ADVANCE_MS (5000)
        s1 = page.evaluate(f"() => document.querySelector('{ul_sel}')?.scrollLeft ?? -1")
        print(f"AUTOPLAY: scrollLeft {s0} -> {s1} (advanced={s1 > s0})")
        # ===== 2) Hover pause =====
        page.hover(ul_sel)
        sH0 = page.evaluate(f"() => document.querySelector('{ul_sel}')?.scrollLeft")
        page.wait_for_timeout(6500)
        sH1 = page.evaluate(f"() => document.querySelector('{ul_sel}')?.scrollLeft")
        print(f"HOVER PAUSE: scrollLeft {sH0} -> {sH1} (paused={sH1 == sH0})")
        # leave hover, click next button, confirm advance
        page.mouse.move(10, 10)
        page.wait_for_timeout(300)
        prev_btn = page.locator('button[aria-label="Previous scholarships"]').count()
        next_btn = page.locator('button[aria-label="Next scholarships"]').count()
        print(f"ARROW CONTROLS: prev={prev_btn} next={next_btn}")
        nb = page.locator('button[aria-label="Next scholarships"]')
        if nb.is_enabled():
            nb.click()
            page.wait_for_timeout(800)
            sN = page.evaluate(f"() => document.querySelector('{ul_sel}')?.scrollLeft")
            print(f"NEXT click scrolled to {sN}")
        else:
            print("NEXT button disabled, skipping click probe")
        # ===== 3) FAQ chips + footer chip on landing =====
        page.get_by_text("The things every applicant").first.scroll_into_view_if_needed()
        page.wait_for_timeout(400)
        page.screenshot(path=str(OUT / "faq-chips.png"))
        chips = page.get_by_text("Pricing").first.count()
        print(f"FAQ chips visible (Pricing chip count): {chips}")
        page.evaluate("() => window.scrollTo(0, document.body.scrollHeight)")
        page.wait_for_timeout(600)
        page.screenshot(path=str(OUT / "footer-chip.png"))
        print(f"console_errors (default): {len(errs)}")
        for e in errs:
            print("  ", e)
        ctx.close()

        # ===== 4) Reduced-motion: autoplay must NOT advance =====
        ctx2 = b.new_context(viewport={"width": 1440, "height": 900}, reduced_motion="reduce")
        page2 = ctx2.new_page()
        errs2 = []
        page2.on("console", lambda m: errs2.append(m.text) if m.type == "error" else None)
        page2.goto("http://localhost:3000/", wait_until="load", timeout=60000)
        page2.get_by_text("Real, fully-funded").first.scroll_into_view_if_needed()
        try:
            page2.wait_for_function(
                f"() => document.querySelectorAll('{ul_sel} > li').length >= 4",
                timeout=15000,
            )
        except Exception as e:
            print(f"(reduced) WAIT-FOR-CARDS failed: {e}")
        r0 = page2.evaluate(f"() => document.querySelector('{ul_sel}')?.scrollLeft ?? -1")
        page2.wait_for_timeout(6500)
        r1 = page2.evaluate(f"() => document.querySelector('{ul_sel}')?.scrollLeft ?? -1")
        print(f"REDUCED-MOTION: scrollLeft {r0} -> {r1} (static={r1 == r0})")
        print(f"console_errors (reduced): {len(errs2)}")
        ctx2.close()
        b.close()
    print("done")


if __name__ == "__main__":
    main()
