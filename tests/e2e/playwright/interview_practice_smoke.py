from playwright.sync_api import sync_playwright


SAMPLE_ANSWER = """
I want to pursue graduate study in data science because I led a capstone project
that forced me to connect messy public-service data with real decisions. That
experience taught me how much I enjoy translating technical work into practical
impact, and it gave me the confidence to pursue a graduate program where I can
deepen both my analytical skills and my long-term contribution goals.
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

        page.goto("http://localhost:3000/interview")
        page.wait_for_load_state("networkidle")
        page.wait_for_selector('[data-testid="interview-practice-shell"]')

        start_selector = '[data-testid="interview-start-session"], [data-testid="interview-start-new-session"]'
        page.locator(start_selector).first.click()
        page.wait_for_load_state("networkidle")
        page.wait_for_selector('[data-testid="interview-question-panel"]')

        page.locator('[data-testid="interview-answer-input"]').fill(SAMPLE_ANSWER)
        page.locator('[data-testid="interview-submit-answer"]').click()
        page.wait_for_load_state("networkidle")
        page.wait_for_selector('[data-testid="interview-result-view"]')
        page.wait_for_selector("text=Rubric scores")

        browser.close()


if __name__ == "__main__":
    main()
