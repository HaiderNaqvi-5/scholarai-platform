"""Seed demo accounts in Clerk (admin / mentor / student)."""
from __future__ import annotations

import asyncio

from app.integrations.clerk.client import clerk_client


DEMO_ACCOUNTS = [
    {"email": "admin@example.com", "first": "Demo", "last": "Admin", "role": "admin"},
    {"email": "mentor@example.com", "first": "Demo", "last": "Mentor", "role": "mentor"},
    {"email": "student@example.com", "first": "Demo", "last": "Student", "role": "student"},
]


async def main() -> None:
    api = clerk_client()
    for acc in DEMO_ACCOUNTS:
        try:
            created = await api.users.create({
                "email_address": [acc["email"]],
                "password": "strongpass1",
                "first_name": acc["first"],
                "last_name": acc["last"],
                "public_metadata": {"role": acc["role"]},
                "skip_password_checks": True,
            })
            print(f"created {created.id} for {acc['email']}")
        except Exception as exc:
            print(f"skipped {acc['email']}: {exc}")


if __name__ == "__main__":
    asyncio.run(main())
