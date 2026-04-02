import uuid

from fastapi import HTTPException, status
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models import Application, ApplicationStatus, RecordState, Scholarship
from app.schemas import SavedOpportunityItem
from app.services.recommendations.eligibility import scholarship_in_scope

TRACKER_STATUS_TO_APPLICATION_STATUS: dict[str, ApplicationStatus] = {
    "saved": ApplicationStatus.SAVED,
    "in_progress": ApplicationStatus.PLANNING,
    "applied": ApplicationStatus.SUBMITTED,
    "closed": ApplicationStatus.CLOSED,
}
APPLICATION_STATUS_TO_TRACKER_STATUS: dict[ApplicationStatus, str] = {
    status: tracker for tracker, status in TRACKER_STATUS_TO_APPLICATION_STATUS.items()
}


class SavedOpportunityService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def list_saved(self, user_id: uuid.UUID) -> list[SavedOpportunityItem]:
        result = await self.db.execute(
            select(Application)
            .where(
                Application.user_id == user_id,
                Application.status.in_(
                    [
                        ApplicationStatus.SAVED,
                        ApplicationStatus.PLANNING,
                        ApplicationStatus.SUBMITTED,
                        ApplicationStatus.CLOSED,
                    ]
                ),
            )
            .options(selectinload(Application.scholarship))
            .order_by(Application.created_at.desc())
        )
        saved_rows = result.scalars().all()
        return [
            self._serialize(application)
            for application in saved_rows
            if application.scholarship is not None
            and application.scholarship.record_state == RecordState.PUBLISHED
            and self._is_in_scope(application.scholarship)
        ]

    async def save(self, user_id: uuid.UUID, scholarship_id: uuid.UUID) -> SavedOpportunityItem:
        scholarship = await self._load_published_scholarship(scholarship_id)

        result = await self.db.execute(
            select(Application).where(
                Application.user_id == user_id,
                Application.scholarship_id == scholarship_id,
            )
        )
        existing = result.scalar_one_or_none()
        if existing is None:
            existing = Application(
                user_id=user_id,
                scholarship_id=scholarship_id,
                status=ApplicationStatus.SAVED,
            )
            self.db.add(existing)
            await self.db.flush()
            await self.db.refresh(existing)
        else:
            existing.status = ApplicationStatus.SAVED
            await self.db.flush()
            await self.db.refresh(existing)

        existing.scholarship = scholarship
        return self._serialize(existing)

    async def update_status(
        self,
        user_id: uuid.UUID,
        scholarship_id: uuid.UUID,
        tracker_status: str,
    ) -> SavedOpportunityItem:
        result = await self.db.execute(
            select(Application)
            .where(
                Application.user_id == user_id,
                Application.scholarship_id == scholarship_id,
                Application.status.in_(
                    [
                        ApplicationStatus.SAVED,
                        ApplicationStatus.PLANNING,
                        ApplicationStatus.SUBMITTED,
                        ApplicationStatus.CLOSED,
                    ]
                ),
            )
            .options(selectinload(Application.scholarship))
        )
        existing = result.scalar_one_or_none()
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Saved opportunity not found",
            )
        if (
            existing.scholarship is None
            or existing.scholarship.record_state != RecordState.PUBLISHED
            or not self._is_in_scope(existing.scholarship)
        ):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Saved opportunity not found",
            )

        existing.status = TRACKER_STATUS_TO_APPLICATION_STATUS[tracker_status]
        await self.db.flush()
        await self.db.refresh(existing)
        return self._serialize(existing)

    async def remove(self, user_id: uuid.UUID, scholarship_id: uuid.UUID) -> None:
        result = await self.db.execute(
            select(Application).where(
                Application.user_id == user_id,
                Application.scholarship_id == scholarship_id,
                Application.status.in_(
                    [
                        ApplicationStatus.SAVED,
                        ApplicationStatus.PLANNING,
                        ApplicationStatus.SUBMITTED,
                        ApplicationStatus.CLOSED,
                    ]
                ),
            )
        )
        existing = result.scalar_one_or_none()
        if existing is None:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Saved opportunity not found",
            )

        await self.db.execute(
            delete(Application).where(Application.id == existing.id)
        )

    async def _load_published_scholarship(self, scholarship_id: uuid.UUID) -> Scholarship:
        result = await self.db.execute(
            select(Scholarship).where(
                Scholarship.id == scholarship_id,
                Scholarship.record_state == RecordState.PUBLISHED,
            )
        )
        scholarship = result.scalar_one_or_none()
        if scholarship is None or not self._is_in_scope(scholarship):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Published scholarship not found",
            )
        return scholarship

    def _is_in_scope(self, scholarship: Scholarship) -> bool:
        in_scope, _, _ = scholarship_in_scope(scholarship)
        return in_scope

    def _serialize(self, application: Application) -> SavedOpportunityItem:
        scholarship = application.scholarship
        return SavedOpportunityItem(
            scholarship_id=str(scholarship.id),
            title=scholarship.title,
            provider_name=scholarship.provider_name,
            country_code=scholarship.country_code,
            deadline_at=scholarship.deadline_at,
            record_state=scholarship.record_state.value,
            saved_at=application.created_at,
            tracker_status=APPLICATION_STATUS_TO_TRACKER_STATUS.get(
                application.status,
                "saved",
            ),
        )
