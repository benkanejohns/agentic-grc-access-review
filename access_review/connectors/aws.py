import csv
from datetime import datetime
from pathlib import Path
from typing import Optional

from access_review.models import AccessRecord

from .base import Connector


def _parse_dt(value: str) -> Optional[datetime]:
    if not value or value.strip().lower() in ("", "n/a", "not_supported"):
        return None
    return datetime.fromisoformat(value.replace("Z", "+00:00"))


class AWSIAMConnector(Connector):
    """Reads a file shaped like `aws iam generate-credential-report`, with
    one addition real IAM credential reports don't carry on their own: a
    role/policy column, enriched here because an access review needs to
    know what access someone has, not just when they last used it. A real
    pipeline would join this against `list-attached-user-policies`; the
    sample data includes it directly to keep the demo runnable with a
    single file.
    """

    name = "aws-iam"

    def load(self, path: Path) -> list[AccessRecord]:
        records = []
        with open(path, newline="", encoding="utf-8") as f:
            for row in csv.DictReader(f):
                last_activity = max(
                    (
                        d
                        for d in (
                            _parse_dt(row.get("password_last_used", "")),
                            _parse_dt(row.get("access_key_1_last_used_date", "")),
                            _parse_dt(row.get("access_key_2_last_used_date", "")),
                        )
                        if d is not None
                    ),
                    default=None,
                )
                records.append(
                    AccessRecord(
                        user_id=row["user"],
                        display_name=row["user"],
                        system=self.name,
                        role_or_policy=row.get("attached_policy", "Unknown"),
                        department=row.get("department") or None,
                        mfa_enabled=row.get("mfa_active", "false").strip().lower()
                        == "true",
                        last_activity_at=last_activity,
                        account_created_at=_parse_dt(row.get("user_creation_time", "")),
                    )
                )
        return records
