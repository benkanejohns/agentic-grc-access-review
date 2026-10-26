from access_review.models import AccessRecord, Classification, ReviewVerdict


def render(rows: list[tuple[AccessRecord, Classification, ReviewVerdict]]) -> str:
    """Standard Principle 4: the report surfaces every flag with its
    reasoning and leaves the actual decision to a named human reviewer.
    Nothing in this agent revokes access or closes a finding.
    """
    lines = [
        "| User | System | Role/Policy | Privilege | Dept. fit | Status | Reasons | Reviewer decision |",
        "|---|---|---|---|---|---|---|---|",
    ]
    for record, classification, verdict in rows:
        reasons = "; ".join(verdict.reasons) if verdict.reasons else "n/a"
        lines.append(
            f"| {record.display_name} | {record.system} | {record.role_or_policy} | "
            f"{classification.privilege_level.value} | {classification.department_fit.value} | "
            f"**{verdict.status}** | {reasons} | _pending_ |"
        )
    return "\n".join(lines)
