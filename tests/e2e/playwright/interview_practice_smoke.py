from playwright.sync_api import TimeoutError as PlaywrightTimeoutError, sync_playwright


SAMPLE_ANSWER = """
I want to pursue graduate study in data science because I led a capstone project
that forced me to connect messy public-service data with real decisions. That
experience taught me how much I enjoy translating technical work into practical
impact, and it gave me the confidence to pursue a graduate program where I can
deepen both my analytical skills and my long-term contribution goals.
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

        login_and_wait(page, "/interview")
        page.wait_for_selector('[data-testid="interview-practice-shell"]')

        start_selector = '[data-testid="interview-start-session"], [data-testid="interview-start-new-session"]'
        page.locator(start_selector).first.click()
        page.wait_for_load_state("networkidle")
        page.wait_for_selector('[data-testid="interview-question-panel"]')

        answer_input = page.locator('[data-testid="interview-answer-input"]')
        if answer_input.count():
            answer_input.fill(SAMPLE_ANSWER)
            page.locator('[data-testid="interview-submit-answer"]').click()
            page.wait_for_load_state("networkidle")
        page.wait_for_selector('[data-testid="interview-result-view"]')
        page.wait_for_selector("text=Rubric scores")

        browser.close()


if __name__ == "__main__":
    main()
