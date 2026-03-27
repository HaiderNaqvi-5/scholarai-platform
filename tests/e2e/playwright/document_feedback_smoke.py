from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright


SAMPLE_TEXT = """
I want to pursue graduate study in data science because my undergraduate projects
showed me how practical analytics can improve public services. I led a capstone,
worked with real stakeholders, and learned that I want to build systems that are
both technically strong and socially useful. This draft is intentionally simple,
but it is long enough to exercise the MVP document assistance flow.
""".strip()


def login_and_wait(page, next_path: str) -> None:
    page.goto(f"http://localhost:3000/login?next={next_path}")
    page.wait_for_load_state("domcontentloaded")
    page.locator('[data-testid="login-form"] input[name="email"]').fill(
        "student@example.com"
    )
    page.locator('[data-testid="login-form"] input[name="password"]').fill(
        "strongpass1"
    )
    submit = page.locator('[data-testid="login-form"] button[type="submit"]')
    submit.click()
    try:
        page.wait_for_function(
            "expectedPath => window.location.pathname === expectedPath",
            arg=next_path,
            timeout=60000,
        )
        page.wait_for_load_state("networkidle")
        return
    except PlaywrightTimeoutError:
        pass

    current_path = page.evaluate("window.location.pathname")
    raise AssertionError(
        f"Failed to reach {next_path} after login; current path: {current_path}"
    )


def main() -> None:
    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page()

        login_and_wait(page, "/document-feedback")
        page.wait_for_selector('[data-testid="document-submission-form"]')

        page.locator(
            '[data-testid="document-submission-form"] textarea[name="content_text"]'
        ).fill(SAMPLE_TEXT)
        page.locator('[data-testid="document-submission-form"] button[type="submit"]').click()
        page.wait_for_load_state("networkidle")
        page.wait_for_selector('[data-testid="document-feedback-result"]')
        page.wait_for_selector("text=Writing guidance")

        browser.close()


if __name__ == "__main__":
    main()
