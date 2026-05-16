"""Application strategy report service (PRD §0.6, Elite-exclusive).

Trust boundary: this package sources only from the student profile, the
scholarship match service, the tracker, and the public ``universities`` table.
It MUST NOT import ``institutions`` / ``institution_students`` /
``referral_enrollments`` / ``university_leads`` — B2B relationships never
influence a student's strategy output.
"""

from app.services.reports.strategy_report import StrategyReportService

__all__ = ["StrategyReportService"]
