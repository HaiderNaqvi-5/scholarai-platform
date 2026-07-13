"""Seed / promote demo + admin accounts in Clerk.

Idempotent: if an email already exists in Clerk the account is *promoted*
(public_metadata.role is updated) instead of re-created. This lets the script
grant admin to a user who already signed up via the app.

The admin identity is read from settings (env-driven: DEMO_ADMIN_EMAIL /
DEMO_ADMIN_FULL_NAME) so no real person's email is hardcoded in source. Set
those in the backend environment before running to target a specific user.
"""
from __future__ import annotations

import asyncio

from app.core.config import settings
from app.integrations.clerk.client import clerk_client


def _admin_account() -> dict[str, str]:
    parts = settings.DEMO_ADMIN_FULL_NAME.split(maxsplit=1)
    first = parts[0] if parts else "Demo"
    last = parts[1] if len(parts) > 1 else "Admin"
    return {"email": settings.DEMO_ADMIN_EMAIL, "first": first, "last": last, "role": "admin"}


DEMO_ACCOUNTS = [
    _admin_account(),
    {"email": "mentor@example.com", "first": "Demo", "last": "Mentor", "role": "mentor"},
    {"email": "student@example.com", "first": "Demo", "last": "Student", "role": "student"},
]


async def main() -> None:
    api = clerk_client()
    for acc in DEMO_ACCOUNTS:
        try:
            # clerk-backend-api 1.6.0 SDK is sync — do NOT await.
            existing = api.users.list(email_address=[acc["email"]])
            if existing:
                user = existing[0]
                api.users.update(
                    user_id=user.id,
                    public_metadata={"role": acc["role"]},
                )
                print(f"promoted {user.id} ({acc['email']}) -> role={acc['role']}")
                continue

            created = api.users.create(request={
                "email_address": [acc["email"]],
                "password": settings.DEMO_ADMIN_PASSWORD,
                "first_name": acc["first"],
                "last_name": acc["last"],
                "public_metadata": {"role": acc["role"]},
                "skip_password_checks": True,
            })
            print(f"created {created.id} for {acc['email']} -> role={acc['role']}")
        except Exception as exc:
            print(f"skipped {acc['email']}: {exc}")


if __name__ == "__main__":
    asyncio.run(main())
