from datetime import datetime, timezone
from typing import Optional

from access_review.models import AccessRecord, Classification, ReviewVerdict
from access_review.policy import PolicyControl, PolicyControlCategory


def _find(
    policy: list[PolicyControl], category: PolicyControlCategory
) -> Optional[PolicyControl]:
    return next((c for c in policy if c.category == category), None)


def evaluate(
    record: AccessRecord, classification: Classification, policy: list[PolicyControl]
) -> ReviewVerdict:
    """Standard Principle 2, enforced: every reason below is a plain
    comparison against objective facts, the model's closed-taxonomy
    classification, or a specific cited clause of the governing policy
    parsed once at the start of the run (see `policy.py`). Nothing here
    asks the model what the verdict should be, invents a threshold that
    isn't in the policy, or calls the API.

    If the policy doesn't define a control this logic looks for, that
    check is skipped rather than silently defaulting to a guessed
    threshold, call `policy.missing_categories` at the start of a run
    and surface it, don't let coverage quietly weaken with no trace.
    """
    reasons: list[str] = []
    now = datetime.now(timezone.utc)

    mfa_control = _find(policy, PolicyControlCategory.MFA_REQUIREMENT)
    if mfa_control and not record.mfa_enabled:
        reasons.append(f"MFA not enabled ({mfa_control.control_id})")

    days_inactive = (
        (now - record.last_activity_at).days if record.last_activity_at else None
    )

    general_control = _find(policy, PolicyControlCategory.INACTIVITY_THRESHOLD)
    if days_inactive is None:
        reasons.append("No recorded activity")
    elif (
        general_control
        and general_control.threshold_days is not None
        and days_inactive > general_control.threshold_days
    ):
        reasons.append(
            f"No activity in {days_inactive} days "
            f"({general_control.control_id}: threshold {general_control.threshold_days} days)"
        )

    privileged_control = _find(policy, PolicyControlCategory.PRIVILEGED_INACTIVITY_THRESHOLD)
    if (
        classification.privilege_level == "full-admin"
        and privileged_control
        and privileged_control.threshold_days is not None
        and (days_inactive is None or days_inactive > privileged_control.threshold_days)
    ):
        reasons.append(
            f"Full-admin access with no activity in "
            f"{privileged_control.threshold_days}+ days ({privileged_control.control_id})"
        )

    role_control = _find(policy, PolicyControlCategory.ROLE_ALIGNMENT)
    if classification.department_fit == "mismatch" and role_control:
        reasons.append(
            f"Role does not appear to match department ({role_control.control_id})"
        )

    return ReviewVerdict(status="FLAG" if reasons else "OK", reasons=reasons)
