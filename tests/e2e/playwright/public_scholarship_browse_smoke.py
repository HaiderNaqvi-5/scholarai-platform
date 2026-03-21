from playwright.sync_api import sync_playwright


def main() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto("http://localhost:3000/scholarships")
        page.wait_for_load_state("networkidle")
        page.wait_for_selector('[data-testid="scholarship-browse-shell"]')
        page.wait_for_selector("text=Published records")

        page.get_by_test_id("field-filter-ai").click()
        page.wait_for_load_state("networkidle")
        page.get_by_test_id("scholarship-provider-input").fill("Waterloo")
        page.wait_for_load_state("networkidle")
        page.wait_for_selector("text=Waterloo AI Graduate Scholarship")

        page.locator("text=View details").first.click()
        page.wait_for_load_state("networkidle")
        page.wait_for_selector('[data-testid="scholarship-detail-shell"]')
        page.wait_for_selector("text=Requirements")

        page.goto("http://localhost:3000/login?next=/scholarships")
        page.wait_for_load_state("networkidle")
        page.locator('[data-testid="login-form"] input[name="email"]').fill(
            "student@example.com"
        )
        page.locator('[data-testid="login-form"] input[name="password"]').fill(
            "strongpass1"
        )
        page.locator('[data-testid="login-form"] button[type="submit"]').click()
        page.wait_for_url("**/scholarships")

        page.wait_for_selector("text=Waterloo AI Graduate Scholarship")
        page.locator("text=Save to shortlist").first.click()
        page.wait_for_selector("text=Saved")

        browser.close()


if __name__ == "__main__":
    main()
