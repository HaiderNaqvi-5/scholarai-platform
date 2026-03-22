import enum

from app.models import UserRole


class Capability(enum.StrEnum):
    AUTH_SESSION_READ = "auth.session.read"
    AUTH_SESSION_REFRESH = "auth.session.refresh"

    SCHOLARSHIP_PUBLIC_READ = "scholarship.public.read"

    PROFILE_SELF_READ = "profile.self.read"
    PROFILE_SELF_WRITE = "profile.self.write"

    SAVED_OPPORTUNITY_SELF_READ = "saved_opportunity.self.read"
    SAVED_OPPORTUNITY_SELF_WRITE = "saved_opportunity.self.write"

    RECOMMENDATION_SELF_GENERATE = "recommendation.self.generate"
    RECOMMENDATION_EVALUATE = "recommendation.evaluate"

    DOCUMENT_SELF_READ = "document.self.read"
    DOCUMENT_SELF_CREATE = "document.self.create"
    DOCUMENT_SELF_FEEDBACK = "document.self.feedback"
    DOCUMENT_MENTOR_REVIEW = "document.mentor.review"
    DOCUMENT_MENTOR_SUBMIT = "document.mentor.submit"

    INTERVIEW_SELF_CREATE = "interview.self.create"
    INTERVIEW_SELF_READ = "interview.self.read"
    INTERVIEW_SELF_RESPOND = "interview.self.respond"

    CURATION_QUEUE_READ = "curation.queue.read"
    CURATION_RECORD_VALIDATE = "curation.record.validate"
    CURATION_RECORD_PUBLISH = "curation.record.publish"

    ADMIN_AUDIT_READ = "admin.audit.read"
    ADMIN_INGESTION_RUN = "admin.ingestion.run"

    UNIVERSITY_APPLICATIONS_READ = "university.applications.read"
    UNIVERSITY_STUDENTS_READ = "university.students.read"

    OWNER_SYSTEM_READ = "owner.system.read"
    OWNER_SYSTEM_CONTROL = "owner.system.control"


STUDENT_BASE_CAPABILITIES: set[str] = {
    Capability.AUTH_SESSION_READ,
    Capability.AUTH_SESSION_REFRESH,
    Capability.SCHOLARSHIP_PUBLIC_READ,
    Capability.PROFILE_SELF_READ,
    Capability.PROFILE_SELF_WRITE,
    Capability.SAVED_OPPORTUNITY_SELF_READ,
    Capability.SAVED_OPPORTUNITY_SELF_WRITE,
    Capability.RECOMMENDATION_SELF_GENERATE,
    Capability.DOCUMENT_SELF_READ,
    Capability.DOCUMENT_SELF_CREATE,
    Capability.DOCUMENT_SELF_FEEDBACK,
    Capability.INTERVIEW_SELF_CREATE,
    Capability.INTERVIEW_SELF_READ,
    Capability.INTERVIEW_SELF_RESPOND,
}

INTERNAL_VIEW_CAPABILITIES: set[str] = {
    Capability.CURATION_QUEUE_READ,
    Capability.ADMIN_AUDIT_READ,
    Capability.DOCUMENT_MENTOR_REVIEW,
    Capability.DOCUMENT_MENTOR_SUBMIT,
}

DEV_CAPABILITIES: set[str] = {
    Capability.CURATION_RECORD_VALIDATE,
    Capability.CURATION_RECORD_PUBLISH,
    Capability.RECOMMENDATION_EVALUATE,
}

ADMIN_CAPABILITIES: set[str] = {
    Capability.ADMIN_INGESTION_RUN,
}

UNIVERSITY_CAPABILITIES: set[str] = {
    Capability.UNIVERSITY_APPLICATIONS_READ,
    Capability.UNIVERSITY_STUDENTS_READ,
}

OWNER_CAPABILITIES: set[str] = {
    Capability.OWNER_SYSTEM_READ,
    Capability.OWNER_SYSTEM_CONTROL,
}


ROLE_TO_CAPABILITIES: dict[UserRole, set[str]] = {
    UserRole.STUDENT: set(STUDENT_BASE_CAPABILITIES),
    UserRole.ENDUSER_STUDENT: set(STUDENT_BASE_CAPABILITIES),
    UserRole.INTERNAL_USER: set(STUDENT_BASE_CAPABILITIES | INTERNAL_VIEW_CAPABILITIES),
    UserRole.MENTOR: set(STUDENT_BASE_CAPABILITIES | INTERNAL_VIEW_CAPABILITIES),
    UserRole.DEV: set(STUDENT_BASE_CAPABILITIES | INTERNAL_VIEW_CAPABILITIES | DEV_CAPABILITIES),
    UserRole.ADMIN: set(
        STUDENT_BASE_CAPABILITIES
        | INTERNAL_VIEW_CAPABILITIES
        | DEV_CAPABILITIES
        | ADMIN_CAPABILITIES
    ),
    UserRole.UNIVERSITY: set(UNIVERSITY_CAPABILITIES),
    UserRole.OWNER: set(
        STUDENT_BASE_CAPABILITIES
        | INTERNAL_VIEW_CAPABILITIES
        | DEV_CAPABILITIES
        | ADMIN_CAPABILITIES
        | UNIVERSITY_CAPABILITIES
        | OWNER_CAPABILITIES
    ),
}


def get_role_capabilities(role: UserRole) -> set[str]:
    return set(ROLE_TO_CAPABILITIES.get(role, set()))
