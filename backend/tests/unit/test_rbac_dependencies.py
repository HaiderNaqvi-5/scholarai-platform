from types import SimpleNamespace
from uuid import uuid4

import pytest

import logging

from app.core.authorization import Capability
from app.core.dependencies import require_capability
from app.models import UserRole
from scholarai_common.errors import ScholarAIException

pytestmark = pytest.mark.asyncio


async def test_require_capability_uses_token_claims_when_present():
    dependency = require_capability(Capability.CURATION_QUEUE_READ)
    user = SimpleNamespace(
        id=uuid4(),
        role=UserRole.ADMIN,
        _token_capabilities={Capability.PROFILE_SELF_READ.value},
    )

    with pytest.raises(ScholarAIException) as caught:
        await dependency(current_user=user)

    assert caught.value.status_code == 403
    assert caught.value.code.value == "auth_insufficient_permissions"


async def test_require_capability_falls_back_to_role_map_when_no_token_caps():
    dependency = require_capability(Capability.CURATION_QUEUE_READ)
    user = SimpleNamespace(
        id=uuid4(),
        role=UserRole.ADMIN,
    )

    resolved = await dependency(current_user=user)
    assert resolved is user


async def test_require_capability_fallback_emits_warning(caplog):
    dependency = require_capability(Capability.CURATION_QUEUE_READ)
    user = SimpleNamespace(
        id=uuid4(),
        role=UserRole.ADMIN,
    )

    with caplog.at_level(logging.WARNING):
        await dependency(current_user=user)

    assert any("Capability fallback to role map" in message for message in caplog.messages)
