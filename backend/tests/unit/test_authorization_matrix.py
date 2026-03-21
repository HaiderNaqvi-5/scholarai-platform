from app.core.authorization import Capability, ROLE_TO_CAPABILITIES
from app.models import UserRole


def test_all_mapped_capabilities_exist_in_enum():
    known = {cap.value for cap in Capability}
    mapped = set().union(*ROLE_TO_CAPABILITIES.values())
    assert mapped <= known


def test_every_role_has_non_empty_capability_bundle():
    for role, capabilities in ROLE_TO_CAPABILITIES.items():
        assert capabilities, f"Role {role.value} has no capability assignments"


def test_owner_is_superset_of_admin():
    assert ROLE_TO_CAPABILITIES[UserRole.ADMIN] <= ROLE_TO_CAPABILITIES[UserRole.OWNER]


def test_admin_bundle_includes_required_high_risk_operations():
    admin_capabilities = ROLE_TO_CAPABILITIES[UserRole.ADMIN]
    assert Capability.CURATION_RECORD_VALIDATE.value in admin_capabilities
    assert Capability.CURATION_RECORD_PUBLISH.value in admin_capabilities
    assert Capability.ADMIN_INGESTION_RUN.value in admin_capabilities
