from datetime import datetime, timezone

from access_review.models import AccessRecord, Classification, ReviewVerdict

STALE_DAYS = 90
PRIVILEGED_STALE_DAYS = 30


def evaluate(record: AccessRecord, classification: Classification) -> ReviewVerdict:
    """Standard Principle 2, enforced: every reason below is a plain
    comparison against objective facts or the model's closed-taxonomy
    classification. Nothing here asks the model what the verdict should be,
    this function never calls the API.
    """
    reasons: list[str] = []
    now = datetime.now(timezone.utc)

    if not record.mfa_enabled:
        reasons.append("MFA not enabled")

    days_inactive = (
        (now - record.last_activity_at).days if record.last_activity_at else None
    )
    if days_inactive is None:
        reasons.append("No recorded activity")
    elif days_inactive > STALE_DAYS:
        reasons.append(f"No activity in {days_inactive} days (threshold: {STALE_DAYS})")

    if classification.privilege_level == "full-admin" and (
        days_inactive is None or days_inactive > PRIVILEGED_STALE_DAYS
    ):
        reasons.append(
            f"Full-admin access with no activity in {PRIVILEGED_STALE_DAYS}+ days"
        )

    if classification.department_fit == "mismatch":
        reasons.append("Role does not appear to match department")

    return ReviewVerdict(status="FLAG" if reasons else "OK", reasons=reasons)
