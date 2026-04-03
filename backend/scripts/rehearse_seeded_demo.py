import os
from time import time

import httpx


API_BASE_URL = os.getenv("DEMO_API_BASE_URL", "http://localhost:8000/api/v1")


def main() -> None:
    email = f"demo-seeded-{int(time())}@example.com"
    password = "StrongPass1!x"

    with httpx.Client(timeout=30.0) as client:
        register_response = client.post(
            f"{API_BASE_URL}/auth/register",
            json={
                "full_name": "Seeded Demo Student",
                "email": email,
                "password": password,
            },
        )
        register_response.raise_for_status()

        login_response = client.post(
            f"{API_BASE_URL}/auth/login",
            json={"email": email, "password": password},
        )
        login_response.raise_for_status()
        tokens = login_response.json()
        headers = {"Authorization": f"Bearer {tokens['access_token']}"}

        profile_response = client.put(
            f"{API_BASE_URL}/profile",
            headers=headers,
            json={
                "citizenship_country_code": "PK",
                "gpa_value": 3.7,
                "gpa_scale": 4.0,
                "target_field": "Data Science",
                "target_degree_level": "MS",
                "target_country_code": "CA",
                "language_test_type": "IELTS",
                "language_test_score": 7.5,
            },
        )
        profile_response.raise_for_status()

        recommendation_response = client.post(
            f"{API_BASE_URL}/recommendations",
            headers=headers,
            json={"limit": 5},
        )
        recommendation_response.raise_for_status()
        recommendations = recommendation_response.json()["items"]

        if not recommendations:
            raise RuntimeError("No seeded recommendations were returned.")

        first_recommendation = recommendations[0]

        save_response = client.post(
            f"{API_BASE_URL}/saved-opportunities/{first_recommendation['scholarship_id']}",
            headers=headers,
        )
        save_response.raise_for_status()

        saved_response = client.get(
            f"{API_BASE_URL}/saved-opportunities",
            headers=headers,
        )
        saved_response.raise_for_status()
        saved_items = saved_response.json()["items"]

    print("ScholarAI seeded demo rehearsal completed.")
    print(f"User: {email}")
    print(f"Top recommendation: {first_recommendation['title']}")
    print(f"Match summary: {first_recommendation['match_summary']}")
    print(f"Saved opportunities: {len(saved_items)}")


if __name__ == "__main__":
    main()
