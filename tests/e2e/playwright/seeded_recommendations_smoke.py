from time import time

from playwright.sync_api import sync_playwright


def main() -> None:
    email = f"student+{int(time())}@example.com"

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto("http://localhost:3000/signup")
        page.wait_for_load_state("networkidle")

        page.locator('[data-testid="signup-form"] input[name="full_name"]').fill(
            "Recommendation Demo Student"
        )
        page.locator('[data-testid="signup-form"] input[name="email"]').fill(email)
        page.locator('[data-testid="signup-form"] input[name="password"]').fill(
            "strongpass1"
        )
        page.locator('[data-testid="signup-form"] button[type="submit"]').click()
        page.wait_for_load_state("networkidle")

        page.goto("http://localhost:3000/profile")
        page.wait_for_load_state("networkidle")
        page.wait_for_selector('[data-testid="profile-form"]')

        page.locator('[data-testid="profile-form"] input[name="citizenship_country_code"]').fill(
            "PK"
        )
        page.locator('[data-testid="profile-form"] select[name="target_country_code"]').select_option(
            "CA"
        )
        page.locator('[data-testid="profile-form"] select[name="target_field"]').select_option(
            "Data Science"
        )
        page.locator('[data-testid="profile-form"] input[name="gpa_value"]').fill("3.7")
        page.locator('[data-testid="profile-form"] input[name="gpa_scale"]').fill("4")
        page.locator('[data-testid="profile-form"] button[type="submit"]').click()
        page.wait_for_load_state("networkidle")

        page.wait_for_selector('[data-testid="recommendations-workspace"]')
        page.wait_for_selector('[data-testid="recommendation-card"]')
        page.wait_for_selector("text=What aligned")
        page.wait_for_selector("text=What to verify")

        browser.close()


if __name__ == "__main__":
    main()
