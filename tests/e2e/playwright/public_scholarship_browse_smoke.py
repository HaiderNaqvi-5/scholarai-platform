from playwright.sync_api import sync_playwright


def main() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto("http://localhost:3000/scholarships")
        page.wait_for_load_state("networkidle")
        page.wait_for_selector('[data-testid="scholarship-browse-shell"]')
        page.wait_for_selector("text=Published scholarship corpus")

        page.locator("text=View details").first.click()
        page.wait_for_load_state("networkidle")
        page.wait_for_selector('[data-testid="scholarship-detail-shell"]')
        page.wait_for_selector("text=Published summary")

        browser.close()


if __name__ == "__main__":
    main()
