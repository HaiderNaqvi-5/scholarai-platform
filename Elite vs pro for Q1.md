# Elite vs Pro for Q1 — Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Re-tier ScholarAI Pakistan monetisation — Pro PKR 2,999 / Elite PKR 6,000 — with bucket-based scholarship visibility (best-fits blurred for Pro, revealed for Elite), hard caps on SOPs/matches/tracker, 60% burn-cap accounting, WhatsApp-only premium channel, and zero internal vocabulary leakage to UI.

**Architecture:** Three migrations (scholarship `tier`, `sop_monthly_usage`, `usage_ledger`). Match service classifies internally (`eligible|partial|stretch`, `standard|premium`) but strips fields on serialization. Pro receives full-pool view with top-3 eligible-bucket rows redacted (`locked=true`, name/provider/deadline nulled, compatibility score preserved). Elite reveals all. Plan gates on SOP cap + WhatsApp channel. Burn ledger wraps Anthropic client + notifications. UI uses only neutral copy (`personalised`, `Compatibility`, `Unlock with Elite`); a CI vocab-guard test fails the build if `eligible|partial|stretch|premium|standard|bucket|tier` appears in any serialized API field or user-visible string.

**Tech Stack:** FastAPI · SQLAlchemy 2 async · Alembic · Pydantic v2 · Anthropic SDK (Haiku 4.5 / Sonnet 4.6) · Next.js 16 + React 19 + Tailwind 4 · pytest-asyncio · Bun · Playwright.

---

## File Structure

**Backend create**
- `backend/alembic/versions/20260516_0023_scholarship_tier.py`
- `backend/alembic/versions/20260516_0024_sop_monthly_usage.py`
- `backend/alembic/versions/20260516_0025_usage_ledger.py`
- `backend/app/core/burn_cap.py`
- `backend/tests/unit/test_sop_quota.py`
- `backend/tests/unit/test_burn_cap.py`
- `backend/tests/unit/test_user_facing_vocab.py`

**Backend modify**
- `backend/app/models/models.py` — add `ScholarshipTier` enum + `Scholarship.tier`, `User.lifetime_sop_count`, `SopMonthlyUsage`, `UsageLedger`
- `backend/app/core/plan_guard.py` — caps tables + helpers + PKR 2,999 price
- `backend/app/schemas/scholarships.py` — `ScholarshipMatchOut` strip bucket/tier, add `compatibility`+`locked`; new `UnlockOffer`
- `backend/app/services/scholarships/match_service.py` — internal buckets, blur logic, neutral copy
- `backend/app/services/documents/sop_builder.py` — quota gate + counter
- `backend/app/services/tracker/service.py` — replace hard-coded 3 with `TRACKER_CAP[plan]`
- `backend/app/services/notifications/channels.py` — drop `send_sms`, keep email + WhatsApp
- `backend/app/services/llm/anthropic_client.py` — wrap `complete()` with burn ledger
- `backend/app/tasks/alert_tasks.py` — remove SMS branch
- `backend/app/api/v1/routes/waitlist.py` — re-price + neutral bullets
- `backend/app/api/v1/routes/scholarships.py` — premium-tier filter for free/anon
- `backend/tests/unit/test_scholarship_match_service.py` — extend
- `backend/tests/unit/test_waitlist_and_pricing.py` — price assertions
- `backend/tests/unit/test_alert_tasks.py` — drop SMS, assert WhatsApp-only
- `backend/tests/unit/test_tracker_service.py` — parametrize plan caps

**Frontend modify**
- `frontend/src/lib/api/types.ts` — sync `ScholarshipMatchOut` + `UnlockOffer`
- `frontend/src/app/(student)/scholarships/page.tsx` — `MatchCard` with locked render
- `frontend/src/components/CompatibilityMeter.tsx` — new bar component
- `frontend/src/app/upgrade/page.tsx` — `COMPARISON_ROWS` + bullets sync
- `frontend/src/components/UpgradeWall/index.tsx` — neutral copy path

---

## Task 1 — Migration: `scholarship_tier`

**Files:** Create `backend/alembic/versions/20260516_0023_scholarship_tier.py`

- [ ] **Step 1:** Write migration

```python
"""scholarship tier (standard/premium) for Q1 retier."""
from alembic import op
import sqlalchemy as sa

revision = "20260516_0023"
down_revision = "20260515_0022"

def upgrade() -> None:
    tier = sa.Enum("standard", "premium", name="scholarship_tier")
    tier.create(op.get_bind(), checkfirst=True)
    op.add_column(
        "scholarships",
        sa.Column("tier", tier, nullable=False, server_default="standard"),
    )
    op.create_index("ix_scholarships_tier", "scholarships", ["tier"])
    op.execute(
        "UPDATE scholarships SET tier = 'premium' "
        "WHERE LOWER(name) ~ "
        "'(chevening|fulbright|daad|commonwealth|hec overseas|rhodes|gates|schwarzman|erasmus mundus)' "
        "OR LOWER(provider) ~ "
        "'(chevening|fulbright|daad|commonwealth|hec|rhodes|gates foundation|schwarzman|erasmus)'"
    )

def downgrade() -> None:
    op.drop_index("ix_scholarships_tier", table_name="scholarships")
    op.drop_column("scholarships", "tier")
    sa.Enum(name="scholarship_tier").drop(op.get_bind(), checkfirst=True)
```

- [ ] **Step 2:** Run `cd backend && alembic upgrade head` — expect `20260516_0023` applied, ≥5 premium rows.
- [ ] **Step 3:** Commit `feat(db): add scholarship.tier with premium backfill`.

## Task 2 — Migration: `sop_monthly_usage` + `lifetime_sop_count`

**Files:** Create `backend/alembic/versions/20260516_0024_sop_monthly_usage.py`

- [ ] **Step 1:** Write migration

```python
revision = "20260516_0024"
down_revision = "20260516_0023"

def upgrade():
    op.add_column("users",
        sa.Column("lifetime_sop_count", sa.Integer, nullable=False, server_default="0"))
    op.create_table(
        "sop_monthly_usage",
        sa.Column("user_id", sa.Integer,
                  sa.ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
        sa.Column("period_yyyymm", sa.String(6), primary_key=True),
        sa.Column("sop_count", sa.Integer, nullable=False, server_default="0"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now()),
    )

def downgrade():
    op.drop_table("sop_monthly_usage")
    op.drop_column("users", "lifetime_sop_count")
```

- [ ] **Step 2:** `alembic upgrade head` — expect `0024` applied.
- [ ] **Step 3:** Commit `feat(db): sop monthly usage + lifetime counter`.

## Task 3 — Migration: `usage_ledger`

**Files:** Create `backend/alembic/versions/20260516_0025_usage_ledger.py`

- [ ] **Step 1:** Write migration

```python
revision = "20260516_0025"
down_revision = "20260516_0024"

def upgrade():
    op.create_table(
        "usage_ledger",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column("user_id", sa.Integer,
                  sa.ForeignKey("users.id", ondelete="CASCADE"), nullable=False),
        sa.Column("period_yyyymm", sa.String(6), nullable=False),
        sa.Column("kind", sa.String(32), nullable=False),
        sa.Column("input_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("output_tokens", sa.Integer, nullable=False, server_default="0"),
        sa.Column("cost_pkr_micro", sa.BigInteger, nullable=False),
        sa.Column("endpoint", sa.String(64), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True),
                  server_default=sa.func.now(), nullable=False),
    )
    op.create_index("ix_usage_ledger_user_period",
                    "usage_ledger", ["user_id", "period_yyyymm"])

def downgrade():
    op.drop_index("ix_usage_ledger_user_period", table_name="usage_ledger")
    op.drop_table("usage_ledger")
```

- [ ] **Step 2:** `alembic upgrade head` — expect `0025` applied.
- [ ] **Step 3:** Commit `feat(db): usage_ledger for burn-cap accounting`.

## Task 4 — Models: enums + ORM rows

**Files:** Modify `backend/app/models/models.py`

- [ ] **Step 1:** Add enum `ScholarshipTier(str, enum.Enum) {STANDARD="standard", PREMIUM="premium"}` near other enums.
- [ ] **Step 2:** Add column `tier = Column(SAEnum(ScholarshipTier, name="scholarship_tier"), nullable=False, server_default=ScholarshipTier.STANDARD.value, index=True)` to `Scholarship`.
- [ ] **Step 3:** Add `lifetime_sop_count = Column(Integer, nullable=False, default=0, server_default="0")` to `User`.
- [ ] **Step 4:** Add models

```python
class SopMonthlyUsage(Base):
    __tablename__ = "sop_monthly_usage"
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True)
    period_yyyymm = Column(String(6), primary_key=True)
    sop_count = Column(Integer, nullable=False, default=0)
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())

class UsageLedger(Base):
    __tablename__ = "usage_ledger"
    id = Column(BigInteger, primary_key=True, autoincrement=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    period_yyyymm = Column(String(6), nullable=False)
    kind = Column(String(32), nullable=False)
    input_tokens = Column(Integer, nullable=False, default=0)
    output_tokens = Column(Integer, nullable=False, default=0)
    cost_pkr_micro = Column(BigInteger, nullable=False)
    endpoint = Column(String(64), nullable=False)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
```

- [ ] **Step 5:** `python -m compileall backend/app/models` — expect OK.
- [ ] **Step 6:** Commit `feat(models): scholarship tier + sop/usage ledger ORM`.

## Task 5 — `plan_guard.py` constants + helpers

**Files:** Modify `backend/app/core/plan_guard.py`

- [ ] **Step 1:** Replace `PRICE_BY_CURRENCY` block (lines 26–32) and append caps/helpers

```python
PRICE_BY_CURRENCY: dict[str, str] = {
    "PKR": "PKR 2,999/month",
    "GBP": "£8.49/month",
    "EUR": "€9.49/month",
    "AED": "AED 39/month",
    "USD": "$9.99/month",
}

MATCH_CAP   = {"free": 3, "pro": 6,  "elite": 12, "institution": 12}
TRACKER_CAP = {"free": 3, "pro": 6,  "elite": 12, "institution": 50}
MONTHLY_SOP_CAP = {"free": 0, "pro": 5, "elite": 10, "institution": 50}
LIFETIME_FREE_SOP = 1
PRO_BLURRED_BEST_FIT_COUNT = 3

BEST_FIT_REVEAL_PLANS = frozenset({"elite", "institution"})
PREMIUM_VISIBLE_PLANS = frozenset({"pro", "elite", "institution"})

def can_reveal_best_fit(user) -> bool:
    return (user.plan or "free").lower() in BEST_FIT_REVEAL_PLANS

def can_see_premium(user) -> bool:
    return (user.plan or "free").lower() in PREMIUM_VISIBLE_PLANS
```

- [ ] **Step 2:** Write failing tests in `backend/tests/unit/test_plan_caps.py`

```python
import pytest
from app.core.plan_guard import (
    MATCH_CAP, TRACKER_CAP, MONTHLY_SOP_CAP,
    can_reveal_best_fit, can_see_premium,
)

class _U:
    def __init__(self, plan): self.plan = plan

@pytest.mark.parametrize("plan,m,t,s", [
    ("free", 3, 3, 0), ("pro", 6, 6, 5), ("elite", 12, 12, 10)
])
def test_caps(plan, m, t, s):
    assert MATCH_CAP[plan] == m
    assert TRACKER_CAP[plan] == t
    assert MONTHLY_SOP_CAP[plan] == s

def test_reveal_gates():
    assert can_reveal_best_fit(_U("elite"))
    assert not can_reveal_best_fit(_U("pro"))
    assert can_see_premium(_U("pro"))
    assert not can_see_premium(_U("free"))
```

- [ ] **Step 3:** Run `pytest backend/tests/unit/test_plan_caps.py -v` — expect PASS.
- [ ] **Step 4:** Commit `feat(plan_guard): Q1 retier caps + reveal gates`.

## Task 6 — `burn_cap.py` accounting module

**Files:** Create `backend/app/core/burn_cap.py`, `backend/tests/unit/test_burn_cap.py`

- [ ] **Step 1:** Write failing tests

```python
import pytest
from decimal import Decimal
from app.core.burn_cap import llm_cost_pkr, tier_budget, _period

class _U:
    def __init__(self, plan): self.plan = plan; self.id = 1

def test_haiku_cost():
    c = llm_cost_pkr("llm_haiku", 1000, 500)
    assert Decimal("0.99") < c < Decimal("1.10")  # ~PKR 1

def test_sonnet_cost():
    c = llm_cost_pkr("llm_sonnet", 5000, 1800)
    assert Decimal("11") < c < Decimal("13")  # ~PKR 12

def test_tier_budgets():
    assert tier_budget(_U("free"))  == Decimal("50")
    assert tier_budget(_U("pro"))   == Decimal("1799")  # 2999 * 0.6
    assert tier_budget(_U("elite")) == Decimal("3600")  # 6000 * 0.6

def test_period_format():
    p = _period()
    assert len(p) == 6 and p.isdigit()
```

- [ ] **Step 2:** Run tests — expect ImportError.
- [ ] **Step 3:** Implement module

```python
from decimal import Decimal
from datetime import datetime, timezone
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import HTTPException
from app.models import User, UsageLedger

PKR_PER_USD = Decimal("280")
PRICING_USD_PER_MTOK = {
    "llm_haiku":  (Decimal("1"), Decimal("5")),
    "llm_sonnet": (Decimal("3"), Decimal("15")),
}
WHATSAPP_COST_PKR = Decimal("3")
TIER_BUDGET_PKR = {
    "free":  Decimal("50"),
    "pro":   Decimal("1799"),
    "elite": Decimal("3600"),
}

def _period() -> str:
    n = datetime.now(timezone.utc)
    return f"{n.year:04d}{n.month:02d}"

def llm_cost_pkr(kind: str, inp: int, out: int) -> Decimal:
    i, o = PRICING_USD_PER_MTOK[kind]
    usd = (Decimal(inp) * i + Decimal(out) * o) / Decimal(1_000_000)
    return usd * PKR_PER_USD

def tier_budget(user: User) -> Decimal:
    if (user.plan or "").lower() == "institution":
        return Decimal("999999")
    return TIER_BUDGET_PKR.get((user.plan or "free").lower(), Decimal("50"))

async def month_to_date_pkr(db: AsyncSession, user_id: int) -> Decimal:
    q = select(func.coalesce(func.sum(UsageLedger.cost_pkr_micro), 0)).where(
        UsageLedger.user_id == user_id,
        UsageLedger.period_yyyymm == _period(),
    )
    micro = (await db.execute(q)).scalar_one()
    return Decimal(micro) / Decimal(1_000_000)

async def assert_within_burn_cap(db: AsyncSession, user: User, projected: Decimal) -> None:
    spent = await month_to_date_pkr(db, user.id)
    budget = tier_budget(user)
    if spent + projected > budget:
        raise HTTPException(429, detail={
            "error": "burn_cap_reached",
            "spent_pkr": str(spent.quantize(Decimal("0.01"))),
            "budget_pkr": str(budget),
            "upgrade_url": "/upgrade" if (user.plan or "free").lower() != "elite" else None,
            "message": "Monthly AI budget reached. Resets next month, or upgrade tier.",
        })

async def record_llm(db: AsyncSession, user_id: int, kind: str,
                     inp: int, out: int, endpoint: str) -> None:
    cost = llm_cost_pkr(kind, inp, out)
    db.add(UsageLedger(
        user_id=user_id, period_yyyymm=_period(), kind=kind,
        input_tokens=inp, output_tokens=out,
        cost_pkr_micro=int(cost * Decimal(1_000_000)), endpoint=endpoint,
    ))
    await db.flush()

async def record_whatsapp(db: AsyncSession, user_id: int) -> None:
    db.add(UsageLedger(
        user_id=user_id, period_yyyymm=_period(), kind="whatsapp",
        cost_pkr_micro=int(WHATSAPP_COST_PKR * Decimal(1_000_000)),
        endpoint="notifications.whatsapp",
    ))
    await db.flush()
```

- [ ] **Step 4:** Run tests — expect PASS.
- [ ] **Step 5:** Commit `feat(burn_cap): 60% per-tier accounting`.

## Task 7 — Match service: internal buckets + blur

**Files:** Modify `backend/app/schemas/scholarships.py`, `backend/app/services/scholarships/match_service.py`

- [ ] **Step 1:** Schema — replace `ScholarshipMatchOut` and add `UnlockOffer` / extend `MatchResponse`

```python
from typing import Literal
from pydantic import BaseModel, Field

class ScholarshipMatchOut(BaseModel):
    id: int | None
    name: str
    provider: str
    country_code: str | None
    funding_amount: str | None
    deadline: "date | None"
    compatibility: float = Field(ge=0, le=1)
    locked: bool = False

class UnlockOffer(BaseModel):
    to_plan: Literal["pro", "elite"]
    locked_count: int = 0
    headline: str
    message: str

class MatchResponse(BaseModel):
    items: list[ScholarshipMatchOut]
    unlock_offer: UnlockOffer | None = None
```

- [ ] **Step 2:** Replace `match()` in `match_service.py`

```python
from app.core.plan_guard import (
    MATCH_CAP, PRO_BLURRED_BEST_FIT_COUNT,
    can_reveal_best_fit, can_see_premium,
)
from app.models import Scholarship, ScholarshipTier, RecordState

_B_ELIG, _B_PART, _B_STRETCH = "eligible", "partial", "stretch"
_REDACT = "Reveal with upgrade"

def _strip(row, *, locked: bool, fit: float) -> ScholarshipMatchOut:
    if locked:
        return ScholarshipMatchOut(
            id=None, name=_REDACT, provider=_REDACT,
            country_code=row.country_code, funding_amount=None, deadline=None,
            compatibility=fit, locked=True,
        )
    return ScholarshipMatchOut(
        id=row.id, name=row.name, provider=row.provider,
        country_code=row.country_code,
        funding_amount=getattr(row, "funding_amount_display", None),
        deadline=row.deadline, compatibility=fit, locked=False,
    )

async def match(self, *, user, top_n: int | None = None) -> MatchResponse:
    plan = (user.plan or "free").lower()
    cap = top_n or MATCH_CAP.get(plan, 3)

    q = select(Scholarship).where(Scholarship.record_state == RecordState.PUBLISHED)
    if not can_see_premium(user):
        q = q.where(Scholarship.tier == ScholarshipTier.STANDARD)
    rows = (await self.db.execute(q)).scalars().all()

    classified = [(self._classify_bucket(r, self._profile), r, self._fit_score(r, self._profile))
                  for r in rows]
    bucket_rank = {_B_ELIG: 0, _B_PART: 1, _B_STRETCH: 2}
    classified.sort(key=lambda t: (bucket_rank[t[0]], -t[2]))

    if plan == "free":
        free_pool = [t for t in classified if t[0] == _B_STRETCH][:cap]
        items = [_strip(r, locked=False, fit=f) for _, r, f in free_pool]
        offer = UnlockOffer(
            to_plan="pro",
            locked_count=max(0, len(classified) - len(free_pool)),
            headline="More personalised matches available",
            message="Upgrade to Pro to see your full match list.",
        )
        return MatchResponse(items=items, unlock_offer=offer)

    visible = classified[:cap]
    if not can_reveal_best_fit(user):
        out, blurred = [], 0
        for bucket, row, fit in visible:
            if bucket == _B_ELIG and blurred < PRO_BLURRED_BEST_FIT_COUNT:
                out.append(_strip(row, locked=True, fit=fit))
                blurred += 1
            else:
                out.append(_strip(row, locked=False, fit=fit))
        offer = UnlockOffer(
            to_plan="elite",
            locked_count=blurred,
            headline=f"{blurred} match{'es' if blurred != 1 else ''} reserved",
            message="Upgrade to Elite to reveal matches personalised to your profile.",
        ) if blurred > 0 else None
        return MatchResponse(items=out, unlock_offer=offer)

    return MatchResponse(
        items=[_strip(r, locked=False, fit=f) for _, r, f in visible],
        unlock_offer=None,
    )
```

- [ ] **Step 3:** Extend `backend/tests/unit/test_scholarship_match_service.py`

```python
async def test_free_returns_3_locked_false_no_premium(client, db, free_user, premium_seed):
    resp = await client.post("/api/v1/scholarships/match", headers=auth(free_user))
    body = resp.json()
    assert len(body["items"]) <= 3
    assert all(not it["locked"] for it in body["items"])
    assert all("chevening" not in (it["name"] or "").lower() for it in body["items"])

async def test_pro_full_pool_top_eligible_blurred(client, db, pro_user, fit_seed):
    body = (await client.post("/api/v1/scholarships/match", headers=auth(pro_user))).json()
    blurred = [it for it in body["items"] if it["locked"]]
    assert len(blurred) <= 3
    for it in blurred:
        assert it["id"] is None
        assert it["name"] == "Reveal with upgrade"
        assert it["deadline"] is None
        assert it["compatibility"] is not None
    assert body["unlock_offer"]["to_plan"] == "elite"

async def test_elite_full_reveal(client, db, elite_user, fit_seed):
    body = (await client.post("/api/v1/scholarships/match", headers=auth(elite_user))).json()
    assert all(not it["locked"] for it in body["items"])
    assert body["unlock_offer"] is None
```

- [ ] **Step 4:** Run extended tests — expect PASS.
- [ ] **Step 5:** Commit `feat(match): internal buckets, Pro blur, Elite reveal`.

## Task 8 — SOP quota enforcement

**Files:** Modify `backend/app/services/documents/sop_builder.py`. Create `backend/tests/unit/test_sop_quota.py`.

- [ ] **Step 1:** Write failing tests

```python
async def test_free_blocks_after_1_lifetime(client, db, free_user):
    r1 = await client.post("/api/v1/documents/sop/draft", json=PAYLOAD, headers=auth(free_user))
    assert r1.status_code == 200
    r2 = await client.post("/api/v1/documents/sop/draft", json=PAYLOAD, headers=auth(free_user))
    assert r2.status_code == 402
    assert r2.json()["detail"]["error"] == "plan_required"

async def test_pro_blocks_after_5_monthly(client, db, pro_user):
    for _ in range(5):
        r = await client.post("/api/v1/documents/sop/draft", json=PAYLOAD, headers=auth(pro_user))
        assert r.status_code == 200
    r = await client.post("/api/v1/documents/sop/draft", json=PAYLOAD, headers=auth(pro_user))
    assert r.status_code == 429
    assert r.json()["detail"]["error"] == "sop_quota_exhausted"

async def test_elite_blocks_after_10_monthly(client, db, elite_user):
    for _ in range(10):
        assert (await client.post("/api/v1/documents/sop/draft",
                                   json=PAYLOAD, headers=auth(elite_user))).status_code == 200
    r = await client.post("/api/v1/documents/sop/draft", json=PAYLOAD, headers=auth(elite_user))
    assert r.status_code == 429
    assert r.json()["detail"]["upgrade_url"] is None
```

- [ ] **Step 2:** Add helpers in `sop_builder.py`

```python
from datetime import datetime, timezone
from sqlalchemy import select, update, func
from sqlalchemy.dialects.postgresql import insert as pg_insert
from fastapi import HTTPException
from app.core.plan_guard import (
    MONTHLY_SOP_CAP, LIFETIME_FREE_SOP, raise_plan_required,
)
from app.models import SopMonthlyUsage, User

def _yyyymm() -> str:
    n = datetime.now(timezone.utc); return f"{n.year:04d}{n.month:02d}"

async def _assert_sop_quota(db, user) -> None:
    plan = (user.plan or "free").lower()
    if plan == "free":
        if user.lifetime_sop_count >= LIFETIME_FREE_SOP:
            raise_plan_required(
                user, ["pro", "elite"],
                message="Free plan includes 1 SOP. Upgrade for 5/month (Pro) or 10/month (Elite).",
            )
        return
    cap = MONTHLY_SOP_CAP[plan]
    period = _yyyymm()
    row = (await db.execute(
        select(SopMonthlyUsage).where(
            SopMonthlyUsage.user_id == user.id,
            SopMonthlyUsage.period_yyyymm == period,
        )
    )).scalar_one_or_none()
    used = row.sop_count if row else 0
    if used >= cap:
        raise HTTPException(429, detail={
            "error": "sop_quota_exhausted",
            "plan": plan, "used": used, "cap": cap,
            "upgrade_url": "/upgrade" if plan == "pro" else None,
            "message": f"{cap} SOP drafts used this month. Resets next month."
                       + (" Upgrade to Elite for 10/month." if plan == "pro" else ""),
        })

async def _record_sop_use(db, user) -> None:
    plan = (user.plan or "free").lower()
    if plan == "free":
        await db.execute(
            update(User).where(User.id == user.id)
            .values(lifetime_sop_count=User.lifetime_sop_count + 1)
        )
        return
    period = _yyyymm()
    stmt = pg_insert(SopMonthlyUsage).values(
        user_id=user.id, period_yyyymm=period, sop_count=1,
    ).on_conflict_do_update(
        index_elements=["user_id", "period_yyyymm"],
        set_={"sop_count": SopMonthlyUsage.sop_count + 1, "updated_at": func.now()},
    )
    await db.execute(stmt)
```

Call `await _assert_sop_quota(db, user)` at the top of `draft_sop()` and `line_feedback()`. After successful LLM completion, `await _record_sop_use(db, user)`.

- [ ] **Step 3:** Run tests — expect PASS.
- [ ] **Step 4:** Commit `feat(sop): per-plan monthly quota + free lifetime`.

## Task 9 — Tracker cap bump

**Files:** Modify `backend/app/services/tracker/service.py`, `backend/tests/unit/test_tracker_service.py`

- [ ] **Step 1:** Replace hard-coded `3` cap with `TRACKER_CAP[plan]`. Search the file for the `3` literal in the cap check and substitute:

```python
from app.core.plan_guard import TRACKER_CAP
cap = TRACKER_CAP.get((user.plan or "free").lower(), 3)
if active_count >= cap:
    raise_plan_required(user, ["pro", "elite"],
        message=f"Free tracker limit reached ({cap} items). Upgrade for more.")
```

- [ ] **Step 2:** Parametrize tracker test:

```python
@pytest.mark.parametrize("plan,cap", [("free", 3), ("pro", 6), ("elite", 12)])
async def test_tracker_cap_per_plan(client, db, user_factory, plan, cap):
    u = await user_factory(plan=plan)
    for _ in range(cap):
        assert (await client.post("/api/v1/tracker", json=ITEM, headers=auth(u))).status_code == 201
    r = await client.post("/api/v1/tracker", json=ITEM, headers=auth(u))
    assert r.status_code in (402, 429)
```

- [ ] **Step 3:** Run tests — expect PASS.
- [ ] **Step 4:** Commit `feat(tracker): plan-aware cap (3/6/12)`.

## Task 10 — Notification channels: drop SMS, add WhatsApp-only premium

**Files:** Modify `backend/app/services/notifications/channels.py`, `backend/app/tasks/alert_tasks.py`, `backend/tests/unit/test_alert_tasks.py`

- [ ] **Step 1:** Replace the contents of `channels.py`:

```python
import logging
from app.core.burn_cap import record_whatsapp

log = logging.getLogger(__name__)

PLAN_CHANNELS: dict[str, tuple[str, ...]] = {
    "free":  ("email",),
    "pro":   ("email",),
    "elite": ("email", "whatsapp"),
    "institution": ("email", "whatsapp"),
}

async def send_email(user, message: str) -> None:
    log.info("email -> %s: %s", user.email, message[:80])

async def send_whatsapp(db, user, message: str) -> None:
    log.info("whatsapp -> %s: %s", user.whatsapp_e164 or user.phone_e164, message[:80])
    await record_whatsapp(db, user.id)

async def fan_out_for_plan(db, user, message: str) -> None:
    for ch in PLAN_CHANNELS.get((user.plan or "free").lower(), ("email",)):
        if ch == "email":
            await send_email(user, message)
        elif ch == "whatsapp":
            await send_whatsapp(db, user, message)
```

- [ ] **Step 2:** In `alert_tasks.py`, delete every reference to `send_sms` and any `if "sms" in channels` branch. Route through `fan_out_for_plan`.

- [ ] **Step 3:** Rewrite SMS-related tests:

```python
def test_send_sms_function_removed():
    from app.services.notifications import channels
    assert not hasattr(channels, "send_sms")

async def test_elite_plan_channels_email_and_whatsapp_only(...):
    from app.services.notifications.channels import PLAN_CHANNELS
    assert PLAN_CHANNELS["elite"] == ("email", "whatsapp")
    assert "sms" not in PLAN_CHANNELS["elite"]

async def test_priority_alerts_records_whatsapp_ledger(db, elite_user, scholarship):
    await run_priority_scholarship_alerts(db)
    rows = (await db.execute(
        select(UsageLedger).where(UsageLedger.user_id == elite_user.id,
                                  UsageLedger.kind == "whatsapp")
    )).scalars().all()
    assert len(rows) >= 1
```

- [ ] **Step 4:** Run alert tests — expect PASS.
- [ ] **Step 5:** Commit `feat(notifications): WhatsApp-only premium, drop SMS`.

## Task 11 — Wrap Anthropic client with burn ledger

**Files:** Modify `backend/app/services/llm/anthropic_client.py`, and every existing caller (`services/documents/sop_builder.py`, `services/documents/professor_email.py`, `services/reports/strategy_report.py`, `services/visa_interview/evaluator.py`)

- [ ] **Step 1:** Add accounting wrapper around the existing `complete()` (anthropic_client.py:85+)

```python
from app.core.burn_cap import llm_cost_pkr, assert_within_burn_cap, record_llm

async def complete_with_accounting(
    self, *, db, user, endpoint: str, model: str,
    system, messages, max_tokens: int = 1500,
):
    kind = "llm_sonnet" if "sonnet" in model.lower() else "llm_haiku"
    estimated_input = self._estimate_input_tokens(system, messages)
    projected = llm_cost_pkr(kind, estimated_input, max_tokens)
    await assert_within_burn_cap(db, user, projected)

    resp = await self._client.messages.create(
        model=model, system=system, messages=messages, max_tokens=max_tokens,
    )
    await record_llm(
        db, user.id, kind,
        resp.usage.input_tokens, resp.usage.output_tokens, endpoint,
    )
    return resp
```

Implement `_estimate_input_tokens` as `len(json.dumps(system+messages)) // 4`.

- [ ] **Step 2:** Update every call site to pass `db` + `user` + `endpoint`. Example for `sop_builder.py:210`:

```python
resp = await llm.complete_with_accounting(
    db=db, user=user, endpoint="documents.sop.draft",
    model="claude-sonnet-4-6", system=SYSTEM_SOP, messages=msgs,
    max_tokens=1800,
)
```

Apply identically to professor_email, strategy_report, visa_interview/evaluator.

- [ ] **Step 3:** Add a test

```python
async def test_burn_ledger_records_after_sop_draft(db, elite_user, sop_payload):
    await draft_sop(db, elite_user, sop_payload)
    rows = (await db.execute(
        select(UsageLedger).where(UsageLedger.user_id == elite_user.id)
    )).scalars().all()
    assert rows and rows[0].kind in {"llm_sonnet", "llm_haiku"}
    assert rows[0].cost_pkr_micro > 0
```

- [ ] **Step 4:** Run — expect PASS.
- [ ] **Step 5:** Commit `feat(llm): burn-ledger accounting wrapper`.

## Task 12 — Waitlist pricing + neutral bullets

**Files:** Modify `backend/app/api/v1/routes/waitlist.py:22-32` and `_build_tiers` bullets.

- [ ] **Step 1:** Replace `_PRICING_BY_CURRENCY`:

```python
_PRICING_BY_CURRENCY = {
    "PKR": {"pro": "PKR 2,999/month", "elite": "PKR 6,000/month", "institution": "Custom annual"},
    "GBP": {"pro": "£8.49/month",     "elite": "£16.99/month",    "institution": "Custom annual"},
    "EUR": {"pro": "€9.49/month",     "elite": "€18.99/month",    "institution": "Custom annual"},
    "AED": {"pro": "AED 39/month",    "elite": "AED 79/month",    "institution": "Custom annual"},
    "USD": {"pro": "$9.99/month",     "elite": "$19.99/month",    "institution": "Custom annual"},
}
```

- [ ] **Step 2:** Replace Pro/Elite bullets:

```python
# Pro (line ~61)
bullet_features=[
    "5 SOP drafts per month",
    "Full match list — 6 personalised scholarships",
    "6 university matches",
    "Full 10-question visa interview sessions",
    "6-card application tracker",
    "Email deadline reminders",
],

# Elite (line ~76)
bullet_features=[
    "10 SOP drafts per month with line-by-line AI feedback",
    "12 personalised scholarships — every match revealed",
    "12 university matches",
    "12-card application tracker",
    "Downloadable visa interview transcripts",
    "Professor cold-email generator",
    "Application strategy PDF report",
    "Priority WhatsApp deadline alerts",
],
```

- [ ] **Step 3:** Update `test_waitlist_and_pricing.py` to assert `PKR 2,999/month`, `PKR 6,000/month`, `$9.99/month`, `$19.99/month`.
- [ ] **Step 4:** Run — expect PASS.
- [ ] **Step 5:** Commit `feat(pricing): Q1 retier 2999/6000 + neutral bullets`.

## Task 13 — Public catalog premium filter

**Files:** Modify `backend/app/api/v1/routes/scholarships.py`

- [ ] **Step 1:** In the public `list_published` handler, after building the base query:

```python
from app.core.plan_guard import can_see_premium
if current_user is None or not can_see_premium(current_user):
    q = q.where(Scholarship.tier == ScholarshipTier.STANDARD)
```

For the detail handler, when the row is premium and `not can_see_premium(current_user)`, raise the 402 via `raise_plan_required(current_user, ["pro", "elite"], message="Upgrade to Pro to view premium scholarship details.")`.

- [ ] **Step 2:** Tests:

```python
async def test_anon_catalog_excludes_premium(client, premium_seed):
    body = (await client.get("/api/v1/scholarships?limit=100")).json()
    assert all("chevening" not in (s["name"] or "").lower() for s in body["items"])

async def test_pro_catalog_includes_premium(client, pro_user, premium_seed):
    body = (await client.get("/api/v1/scholarships?limit=100", headers=auth(pro_user))).json()
    names = {s["name"].lower() for s in body["items"]}
    assert any("chevening" in n for n in names)

async def test_premium_detail_blocked_for_free(client, free_user, chevening_id):
    r = await client.get(f"/api/v1/scholarships/{chevening_id}", headers=auth(free_user))
    assert r.status_code == 402
```

- [ ] **Step 3:** Run — expect PASS.
- [ ] **Step 4:** Commit `feat(scholarships): premium filter on public catalog`.

## Task 14 — Vocab guard (CI fail if internal terms leak)

**Files:** Create `backend/tests/unit/test_user_facing_vocab.py`

- [ ] **Step 1:** Write

```python
import json, re
from pathlib import Path
import pytest
from app.api.v1.routes.waitlist import _build_tiers

FORBIDDEN = {"eligible", "partial", "stretch", "premium", "standard", "bucket", "tier"}

def _scan(text: str) -> set[str]:
    return {w for w in FORBIDDEN if re.search(rf"\b{w}\b", text, re.IGNORECASE)}

@pytest.mark.parametrize("currency", ["PKR", "GBP", "EUR", "AED", "USD"])
def test_pricing_bullets_have_no_internal_vocab(currency):
    for t in _build_tiers(currency):
        text = " ".join(t.bullet_features + [t.feature_summary or ""])
        hits = _scan(text)
        assert not hits, f"forbidden tokens in {t.key} bullets: {hits}"

def test_match_serialized_payload_no_internal_vocab():
    from app.schemas.scholarships import ScholarshipMatchOut, MatchResponse, UnlockOffer
    sample = MatchResponse(
        items=[ScholarshipMatchOut(
            id=1, name="Test", provider="Org", country_code="PK",
            funding_amount="PKR 1,000,000", deadline=None, compatibility=0.7, locked=False,
        )],
        unlock_offer=UnlockOffer(
            to_plan="elite", locked_count=2,
            headline="2 matches reserved",
            message="Upgrade to Elite to reveal matches personalised to your profile.",
        ),
    )
    blob = sample.model_dump_json()
    hits = _scan(blob)
    assert not hits, f"forbidden tokens in serialized match: {hits}"

def test_frontend_user_facing_strings_no_internal_vocab():
    root = Path(__file__).resolve().parents[3] / "frontend" / "src"
    offenders = []
    pattern = re.compile(rf"\b({'|'.join(FORBIDDEN)})\b", re.IGNORECASE)
    for path in root.rglob("*.tsx"):
        for i, line in enumerate(path.read_text(encoding="utf-8").splitlines(), 1):
            stripped = line.strip()
            if stripped.startswith("//") or stripped.startswith("/*"):
                continue
            for m in pattern.finditer(line):
                # Allow `tier` / `bucket` only inside import lines or type-only contexts
                if "import " in line or ": Tier" in line:
                    continue
                offenders.append(f"{path}:{i}: {m.group(0)}")
    assert not offenders, "\n".join(offenders)
```

- [ ] **Step 2:** Run — expect PASS after Task 12 bullets are updated.
- [ ] **Step 3:** Commit `test(vocab): internal terms must not leak to API or UI`.

## Task 15 — Frontend types sync + match card

**Files:** Modify `frontend/src/lib/api/types.ts`. Create `frontend/src/components/CompatibilityMeter.tsx`. Modify `frontend/src/app/(student)/scholarships/page.tsx`.

- [ ] **Step 1:** Update `types.ts`:

```ts
export interface ScholarshipMatchOut {
  id: number | null;
  name: string;
  provider: string;
  country_code: string | null;
  funding_amount: string | null;
  deadline: string | null;
  compatibility: number;
  locked: boolean;
}
export interface UnlockOffer {
  to_plan: "pro" | "elite";
  locked_count: number;
  headline: string;
  message: string;
}
export interface MatchResponse {
  items: ScholarshipMatchOut[];
  unlock_offer: UnlockOffer | null;
}
```

- [ ] **Step 2:** Add `CompatibilityMeter`:

```tsx
export function CompatibilityMeter({ value }: { value: number }) {
  const pct = Math.round(Math.max(0, Math.min(1, value)) * 100);
  return (
    <div className="flex items-center gap-2" aria-label={`Compatibility ${pct}%`}>
      <div className="h-1.5 w-24 rounded-full bg-ink/10">
        <div className="h-full rounded-full bg-ink" style={{ width: `${pct}%` }} />
      </div>
      <span className="text-xs text-ink-muted">{pct}%</span>
    </div>
  );
}
```

- [ ] **Step 3:** Match card in `scholarships/page.tsx`:

```tsx
import { CompatibilityMeter } from "@/components/CompatibilityMeter";

function MatchCard({ row, onUpgrade }: { row: ScholarshipMatchOut; onUpgrade: () => void }) {
  if (row.locked) {
    return (
      <Card className="relative overflow-hidden">
        <div className="pointer-events-none select-none">
          <CardTitle className="blur-sm">████████████</CardTitle>
          <p className="text-sm text-ink-muted blur-sm">████████</p>
          <CompatibilityMeter value={row.compatibility} />
        </div>
        <div className="absolute inset-0 grid place-items-center bg-ink/5">
          <Button onClick={onUpgrade}>Unlock with Elite</Button>
        </div>
      </Card>
    );
  }
  return (
    <Card>
      <CardTitle>{row.name}</CardTitle>
      <p className="text-sm text-ink-muted">{row.provider}</p>
      <CompatibilityMeter value={row.compatibility} />
      <p className="text-xs text-ink-muted">
        {row.deadline ? `Deadline ${row.deadline}` : "Deadline TBA"}
        {row.funding_amount ? ` · ${row.funding_amount}` : ""}
      </p>
    </Card>
  );
}
```

Wire `unlock_offer.headline` + `.message` into the existing `UpgradeWall` at list footer.

- [ ] **Step 4:** Run `cd frontend && bunx --bun tsc --noEmit && bun run lint && bun run build` — expect 0 errors, 0 warnings.
- [ ] **Step 5:** Commit `feat(frontend): locked match card + CompatibilityMeter`.

## Task 16 — Upgrade-page comparison rows

**Files:** Modify `frontend/src/app/upgrade/page.tsx`

- [ ] **Step 1:** Replace `COMPARISON_ROWS`:

```tsx
const COMPARISON_ROWS = [
  { feature: "Scholarship matches", values: { free: "3 sample",       pro: "6 personalised",      elite: "12 with every match revealed", institution: "Unlimited" } },
  { feature: "University matches",  values: { free: "—",              pro: "6",                   elite: "12",                            institution: "Unlimited" } },
  { feature: "Tracker cards",       values: { free: "3",              pro: "6",                   elite: "12",                            institution: "Unlimited" } },
  { feature: "SOP drafts",          values: { free: "1 lifetime",     pro: "5 / month",           elite: "10 / month",                    institution: "50 / seat" } },
  { feature: "SOP line-by-line AI", values: { free: "—",              pro: "—",                   elite: "✓",                              institution: "✓" } },
  { feature: "Visa interview",      values: { free: "3 questions",    pro: "10 questions",        elite: "10 questions + transcript",      institution: "10 questions + transcript" } },
  { feature: "Deadline alerts",     values: { free: "Email (30 days)", pro: "Email always-on",    elite: "Email + WhatsApp",               institution: "Email + WhatsApp" } },
  { feature: "Strategy report",     values: { free: "—",              pro: "—",                   elite: "✓",                              institution: "✓" } },
  { feature: "Professor cold-email",values: { free: "—",              pro: "—",                   elite: "✓",                              institution: "✓" } },
];
```

- [ ] **Step 2:** `bunx --bun tsc --noEmit && bun run lint && bun run build` — expect green.
- [ ] **Step 3:** Commit `feat(upgrade): refreshed comparison rows for Q1 tiers`.

## Task 17 — Push gate verification

- [ ] **Step 1:** Backend `pytest backend/tests/unit backend/tests/integration -q` — expect previous 369 + new ~25 = ~394 PASS, 0 FAIL.
- [ ] **Step 2:** `python -m compileall backend/app backend/tests` — expect OK.
- [ ] **Step 3:** KPI regression — `pytest backend/tests/integration/test_kpi_regression.py -q`.
- [ ] **Step 4:** Frontend `cd frontend && bun run lint && bunx --bun tsc --noEmit && bun run build` — expect 0 warnings.
- [ ] **Step 5:** Docs governance — `python scripts/docs_governance_check.py` — expect 0 failures.
- [ ] **Step 6:** Browser smoke — `python tests/e2e/playwright/run_smoke_suite.py` (relaxed on greenfield branch; capture failures for follow-up only).
- [ ] **Step 7:** Update `CLAUDE.md` and `progress.md` per global session rules.
- [ ] **Step 8:** Commit `chore(q1-retier): push-gate green; CLAUDE.md+progress.md updated`.

---

## Burn-cap budget recheck

| Tier  | Price    | 60% cap   | Worst-case month  | Util |
|-------|----------|-----------|-------------------|------|
| Pro   | PKR 2,999 | PKR 1,799 | ~PKR 30 (Haiku only) | 1.7% |
| Elite | PKR 6,000 | PKR 3,600 | ~PKR 480 (Sonnet + WhatsApp) | 13.3% |

## Internal vocab discipline

API never serializes `bucket` / `tier` / `eligible` / `partial` / `stretch` / `premium` / `standard`. UI uses `personalised`, `Compatibility N%`, `Unlock with Elite`, `Reveal with upgrade`. Task 14 fails the build if any of those tokens appear in `_build_tiers` bullets, `match_service` serialized output, or `frontend/src/**/*.tsx` user-visible strings.

## Recommended execution

1. **Subagent-Driven** — one task per fresh subagent, review between tasks. Tasks 1–4 (DB/model) sequential. Tasks 5–11 (services) sequential. Tasks 15–16 (frontend) can parallelise after API stabilises. Task 17 last.
2. **Inline** — checkpoint after Tasks 4, 11, 16, 17.
