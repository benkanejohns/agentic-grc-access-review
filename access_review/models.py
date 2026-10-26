"""The normalised schema every connector outputs, and the fixed taxonomy
the model classifies against (Standard Principle 2: a closed taxonomy,
never invent a new category).
"""
from datetime import datetime
from enum import Enum
from typing import Literal, Optional

from pydantic import BaseModel


class PrivilegeLevel(str, Enum):
    READ_ONLY = "read-only"
    SERVICE_SCOPED_WRITE = "service-scoped-write"
    FULL_ADMIN = "full-admin"
    UNKNOWN = "unknown"


class DepartmentFit(str, Enum):
    APPROPRIATE = "appropriate"
    MISMATCH = "mismatch"
    INSUFFICIENT_INFO = "insufficient-info"


class AccessRecord(BaseModel):
    """What every connector (AWS, and later Azure/GCP) normalises its
    platform-specific export into. Nothing downstream of this model knows
    or cares which cloud the record came from."""

    user_id: str
    display_name: str
    system: str
    role_or_policy: str
    department: Optional[str] = None
    mfa_enabled: bool
    last_activity_at: Optional[datetime] = None
    account_created_at: Optional[datetime] = None


class Classification(BaseModel):
    privilege_level: PrivilegeLevel
    department_fit: DepartmentFit
    rationale: str


class ReviewVerdict(BaseModel):
    status: Literal["OK", "FLAG"]
    reasons: list[str]
