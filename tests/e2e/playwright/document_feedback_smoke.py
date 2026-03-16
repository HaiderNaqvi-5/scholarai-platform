from playwright.sync_api import sync_playwright


SAMPLE_TEXT = """
I want to pursue graduate study in data science because my undergraduate projects
showed me how practical analytics can improve public services. I led a capstone,
worked with real stakeholders, and learned that I want to build systems that are
both technically strong and socially useful. This draft is intentionally simple,
but it is long enough to exercise the MVP document assistance flow.
""".strip()


def main() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()

        page.goto("http://localhost:3000/login")
        page.wait_for_load_state("networkidle")

        page.locator('[data-testid="login-form"] input[name="email"]').fill(
            "student@example.com"
        )
        page.locator('[data-testid="login-form"] input[name="password"]').fill(
            "strongpass1"
        )
        page.locator('[data-testid="login-form"] button[type="submit"]').click()
        page.wait_for_load_state("networkidle")

        page.goto("http://localhost:3000/document-feedback")
        page.wait_for_load_state("networkidle")
        page.wait_for_selector('[data-testid="document-submission-form"]')

        page.locator(
            '[data-testid="document-submission-form"] textarea[name="content_text"]'
        ).fill(SAMPLE_TEXT)
        page.locator('[data-testid="document-submission-form"] button[type="submit"]').click()
        page.wait_for_load_state("networkidle")
        page.wait_for_selector('[data-testid="document-feedback-result"]')
        page.wait_for_selector("text=Structured writing guidance")

        browser.close()


if __name__ == "__main__":
    main()
