from playwright.sync_api import sync_playwright


def main() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://localhost:3000/dashboard")
        page.wait_for_load_state("networkidle")
        page.wait_for_url("**/login?next=%2Fdashboard")

        page.locator('[data-testid="login-form"] input[name="email"]').fill(
            "student@example.com"
        )
        page.locator('[data-testid="login-form"] input[name="password"]').fill(
            "strongpass1"
        )
        page.locator('[data-testid="login-form"] button[type="submit"]').click()
        page.wait_for_load_state("networkidle")
        page.wait_for_selector('[data-testid="dashboard-shell"]')

        browser.close()


if __name__ == "__main__":
    main()
