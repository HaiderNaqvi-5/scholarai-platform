from __future__ import annotations

import json
from pathlib import Path
from time import time
from urllib.request import urlopen

from playwright.sync_api import Page, sync_playwright


BASE_URL = "http://localhost:3000"
ARTIFACT_DIR = (
    Path(__file__).resolve().parents[2]
    / "artifacts"
    / "verification"
    / "grounding-citation-ui-2026-03-28"
)

GROUNDED_TEXT = """
Motivation:
I want to pursue graduate study in data science to build public-interest analytics systems.
I have worked on municipal service optimization projects and learned how research can improve
access and fairness in digital public services.

Preparation:
I completed statistics, machine learning, and data engineering coursework and led a capstone
with production-like pipelines, stakeholder interviews, and iterative model validation.

Future impact:
My goal is to apply graduate training to public-sector analytics and evidence-based policy,
especially in service delivery and resource allocation.

Scholarship fit:
This scholarship aligns with my goals because it supports high-impact graduate study and
requires evidence of academic readiness, research potential, and community contribution.
""".strip()

WEAK_TEXT = """
I want funding for graduate school.
I do not yet have clear motivation details.
I have not added preparation evidence.
I have not explained future impact.
This draft is intentionally weak for fallback testing.
""".strip()


def login(page: Page, email: str, password: str, next_path: str) -> None:
    page.goto(f"{BASE_URL}/login?next={next_path}")
    page.wait_for_load_state("domcontentloaded")
    page.locator('[data-testid="login-form"] input[name="email"]').fill(email)
    page.locator('[data-testid="login-form"] input[name="password"]').fill(password)
    page.locator('[data-testid="login-form"] button[type="submit"]').click()
    page.wait_for_url(f"**{next_path}")
    page.wait_for_load_state("domcontentloaded")


def fetch_first_scholarship_id() -> str:
    with urlopen("http://localhost:8000/api/v1/scholarships?page=1&page_size=1") as response:
        payload = json.loads(response.read().decode("utf-8"))
    first = (payload.get("items") or [None])[0]
    scholarship_id = None
    if isinstance(first, dict):
        scholarship_id = first.get("id") or first.get("scholarship_id")
    if not scholarship_id:
        raise RuntimeError("Unable to resolve a scholarship ID for grounding evidence.")
    return str(scholarship_id)


def submit_document(page: Page, text: str, title: str, scholarship_id: str) -> None:
    page.wait_for_selector('[data-testid="document-submission-form"]')
    page.locator('[data-testid="document-submission-form"] input[name="title"]').fill(title)
    page.locator(
        '[data-testid="document-submission-form"] input[name="scholarship_grounding"]'
    ).fill(scholarship_id)
    page.locator(
        '[data-testid="document-submission-form"] textarea[name="content_text"]'
    ).fill(text)
    page.locator('[data-testid="document-submission-form"] button[type="submit"]').click()
    page.wait_for_load_state("domcontentloaded")
    page.wait_for_selector('[data-testid="document-feedback-result"]')
    page.wait_for_selector("text=Writing guidance")


def expand_why_advice(page: Page) -> None:
    toggle = page.locator("button", has_text="Show details")
    if toggle.count() > 0:
        toggle.first.click()
        page.wait_for_timeout(300)


def capture_document_flow(page: Page) -> None:
    run_stamp = int(time())
    scholarship_id = fetch_first_scholarship_id()

    submit_document(
        page,
        GROUNDED_TEXT,
        f"grounded-evidence-{run_stamp}",
        scholarship_id,
    )
    expand_why_advice(page)
    page.screenshot(
        path=str(ARTIFACT_DIR / "document-grounded-desktop.png"),
        full_page=True,
    )

    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(400)
    page.screenshot(
        path=str(ARTIFACT_DIR / "document-grounded-mobile.png"),
        full_page=True,
    )
    page.set_viewport_size({"width": 1440, "height": 1100})

    submit_document(
        page,
        WEAK_TEXT,
        f"weak-evidence-{run_stamp}",
        scholarship_id,
    )
    page.wait_for_selector("text=Partial grounding coverage detected")
    expand_why_advice(page)
    page.screenshot(
        path=str(ARTIFACT_DIR / "document-weak-desktop.png"),
        full_page=True,
    )

    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(400)
    page.screenshot(
        path=str(ARTIFACT_DIR / "document-weak-mobile.png"),
        full_page=True,
    )
    page.set_viewport_size({"width": 1440, "height": 1100})


def capture_mentor_flow(page: Page) -> None:
    page.goto(f"{BASE_URL}/mentor")
    page.wait_for_load_state("domcontentloaded")

    queue_items = page.locator("button.list-item-btn")
    if queue_items.count() > 0:
        queue_items.first.click()
        page.wait_for_selector("text=Reference: Latest AI Feedback", timeout=15000)
    else:
        page.wait_for_selector("text=All caught up")

    page.screenshot(
        path=str(ARTIFACT_DIR / "mentor-citation-count-desktop.png"),
        full_page=True,
    )

    page.set_viewport_size({"width": 390, "height": 844})
    page.wait_for_timeout(400)
    page.screenshot(
        path=str(ARTIFACT_DIR / "mentor-citation-count-mobile.png"),
        full_page=True,
    )


def main() -> None:
    ARTIFACT_DIR.mkdir(parents=True, exist_ok=True)

    with sync_playwright() as playwright:
        browser = playwright.chromium.launch(headless=True)
        page = browser.new_page(viewport={"width": 1440, "height": 1100})

        login(page, "student@example.com", "strongpass1", "/document-feedback")
        capture_document_flow(page)

        login(page, "admin@example.com", "strongpass1", "/mentor")
        capture_mentor_flow(page)

        browser.close()


if __name__ == "__main__":
    main()
