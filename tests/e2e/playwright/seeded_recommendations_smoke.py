from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright

RECOMMENDATION_CARD_TIMEOUT_MS = 8000
ERROR_PANEL_TIMEOUT_MS = 2000


def main() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto("http://localhost:3000/login?next=/recommendations")
        page.wait_for_load_state("networkidle")
        page.locator('[data-testid="login-form"] input[name="email"]').fill(
            "student@example.com"
        )
        page.locator('[data-testid="login-form"] input[name="password"]').fill(
            "strongpass1"
        )
        page.locator('[data-testid="login-form"] button[type="submit"]').click()
        page.wait_for_url("**/recommendations")

        page.wait_for_selector('[data-testid="recommendations-workspace"]')
        try:
            page.wait_for_selector(
                '[data-testid="recommendation-card"]',
                timeout=RECOMMENDATION_CARD_TIMEOUT_MS,
            )
        except PlaywrightTimeoutError as timeout_error:
            try:
                page.wait_for_selector(
                    '[data-testid="recommendations-error"]',
                    timeout=ERROR_PANEL_TIMEOUT_MS,
                )
            except PlaywrightTimeoutError:
                raise timeout_error
            error_panel_profile_link = page.locator(
                '[data-testid="recommendations-error"] a[href="/profile"]'
            )
            try:
                error_panel_profile_link.wait_for(
                    state="visible",
                    timeout=ERROR_PANEL_TIMEOUT_MS,
                )
            except PlaywrightTimeoutError:
                raise AssertionError(
                    "Profile link not found in recommendations error panel within timeout period"
                )
            error_panel_profile_link.click()
            page.wait_for_url("**/profile")
            page.wait_for_selector('[data-testid="profile-form"]')
            page.locator('[data-testid="profile-form"] button[type="submit"]').click()
            page.wait_for_url("**/recommendations")
            page.wait_for_selector('[data-testid="recommendations-workspace"]')
            page.wait_for_selector(
                '[data-testid="recommendation-card"]',
                timeout=RECOMMENDATION_CARD_TIMEOUT_MS,
            )
        page.wait_for_selector("text=What aligned")
        page.wait_for_selector("text=What to verify")

        browser.close()


if __name__ == "__main__":
    main()
