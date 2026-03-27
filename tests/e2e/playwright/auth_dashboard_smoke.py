from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright


def main() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()
        page.goto("http://localhost:3000/dashboard")
        page.wait_for_load_state("networkidle")
        try:
            page.wait_for_function(
                "window.location.pathname === '/login'",
                timeout=5000,
            )
        except PlaywrightTimeoutError:
            page.goto("http://localhost:3000/login?next=/dashboard")
            page.wait_for_load_state("networkidle")

        page.locator('[data-testid="login-form"] input[name="email"]').fill(
            "student@example.com"
        )
        page.locator('[data-testid="login-form"] input[name="password"]').fill(
            "strongpass1"
        )
        page.locator('[data-testid="login-form"] button[type="submit"]').click()
        page.wait_for_function("window.location.pathname === '/dashboard'")
        page.wait_for_load_state("networkidle")
        page.wait_for_selector('[data-testid="dashboard-shell"]')

        browser.close()


if __name__ == "__main__":
    main()
