from enum import Enum

class RecordState(str, Enum):
    RAW = "raw"
    VALIDATED = "validated"
    PUBLISHED = "published"
    ARCHIVED = "archived"

class InterviewPracticeMode(str, Enum):
    GENERAL = "general"
    TECHNICAL = "technical"
    VALUES = "values"
