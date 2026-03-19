from enum import Enum

from sqlalchemy.orm import DeclarativeBase


class Base(DeclarativeBase):
    pass


class RecordState(str, Enum):
    RAW = "raw"
    VALIDATED = "validated"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class InterviewPracticeMode(str, Enum):
    GENERAL = "general"
    TECHNICAL = "technical"
    VALUES = "values"
