from playwright.sync_api import sync_playwright


def login_and_wait(page, next_path: str) -> None:
    page.goto(f"http://localhost:3000/login?next={next_path}")
    page.wait_for_load_state("networkidle")
    page.locator('[data-testid="login-form"] input[name="email"]').fill(
        "admin@example.com"
    )
    page.locator('[data-testid="login-form"] input[name="password"]').fill(
        "strongpass1"
    )
    page.locator('[data-testid="login-form"] button[type="submit"]').click()
    page.wait_for_url(f"**{next_path}")
    page.wait_for_load_state("networkidle")


def main() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()

        login_and_wait(page, "/curation")
        page.wait_for_selector('[data-testid="curation-dashboard-shell"]')

        first_raw_record = page.locator('[data-testid="curation-record-raw"]').first
        if first_raw_record.count():
            first_raw_record.click()
            page.wait_for_load_state("networkidle")
            if page.locator('[data-testid="curation-approve"]').count():
                page.locator('[data-testid="curation-approve"]').click()
                page.wait_for_load_state("networkidle")

        browser.close()


if __name__ == "__main__":
    main()
