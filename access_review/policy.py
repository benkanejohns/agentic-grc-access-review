"""Reads the governing policy once per run and extracts the structured,
numbered controls the rules engine applies deterministically to every
record.

Standard Principle 2 ("reading a policy to see if it addresses a
control") happening literally, once per run, not re-interpreted per
record, which would risk the same run-to-run inconsistency already
observed in department_fit classification. The extracted result is the
versioned knowledge base Principle 6 describes; rules.py retrieves
from it rather than from hardcoded constants.
"""
from enum import Enum
from pathlib import Path
from typing import Optional

from anthropic import Anthropic
from pydantic import BaseModel, ValidationError

_DEFAULT_POLICY_PATH = Path(__file__).parent / "default_policy.md"


class PolicyControlCategory(str, Enum):
    MFA_REQUIREMENT = "mfa_requirement"
    INACTIVITY_THRESHOLD = "inactivity_threshold"
    PRIVILEGED_INACTIVITY_THRESHOLD = "privileged_inactivity_threshold"
    ROLE_ALIGNMENT = "role_alignment"
    OTHER = "other"


class PolicyControl(BaseModel):
    control_id: str
    title: str
    text: str
    category: PolicyControlCategory
    threshold_days: Optional[int] = None
    applies_to: str


_EXTRACT_TOOL = {
    "name": "extract_policy_controls",
    "description": (
        "Extract every numbered control clause from this policy excerpt "
        "into a structured list, one entry per clause. Do not invent "
        "clauses that are not in the text, and do not merge separate "
        "clauses together."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "controls": {
                "type": "array",
                "items": {
                    "type": "object",
                    "properties": {
                        "control_id": {"type": "string"},
                        "title": {"type": "string"},
                        "text": {
                            "type": "string",
                            "description": "The clause, close to verbatim.",
                        },
                        "category": {
                            "type": "string",
                            "enum": [
                                "mfa_requirement",
                                "inactivity_threshold",
                                "privileged_inactivity_threshold",
                                "role_alignment",
                                "other",
                            ],
                            "description": (
                                "Which rule this clause maps to. Use "
                                "'other' if it genuinely doesn't fit; "
                                "never invent a new category."
                            ),
                        },
                        "threshold_days": {
                            "type": "integer",
                            "description": "Omit if this clause has no day-based threshold.",
                        },
                        "applies_to": {
                            "type": "string",
                            "description": "Which access types this applies to, e.g. 'all' or 'full-admin'.",
                        },
                    },
                    "required": ["control_id", "title", "text", "category", "applies_to"],
                },
            },
        },
        "required": ["controls"],
    },
}


def parse_policy(
    path: Optional[Path] = None, model: str = "claude-sonnet-5"
) -> list[PolicyControl]:
    path = path or _DEFAULT_POLICY_PATH
    text = path.read_text(encoding="utf-8")

    client = Anthropic()
    response = client.messages.create(
        model=model,
        max_tokens=2048,
        tools=[_EXTRACT_TOOL],
        tool_choice={"type": "tool", "name": "extract_policy_controls"},
        messages=[
            {
                "role": "user",
                "content": f"Policy document:\n\n{text}\n\nExtract every control clause.",
            }
        ],
    )
    tool_use = next(block for block in response.content if block.type == "tool_use")
    try:
        return [PolicyControl(**c) for c in tool_use.input["controls"]]
    except (ValidationError, KeyError) as e:
        raise ValueError(
            f"Model returned an incomplete policy extraction "
            f"(stop_reason={response.stop_reason!r}): {tool_use.input!r}"
        ) from e


def missing_categories(policy: list[PolicyControl]) -> list[PolicyControlCategory]:
    """Standard Principle 6: if the structured source doesn't cover a
    question, say so explicitly rather than silently applying no check
    at all. Call this once after parsing and surface the result,
    don't let a thin policy quietly weaken coverage with no trace."""
    expected = {
        PolicyControlCategory.MFA_REQUIREMENT,
        PolicyControlCategory.INACTIVITY_THRESHOLD,
        PolicyControlCategory.PRIVILEGED_INACTIVITY_THRESHOLD,
        PolicyControlCategory.ROLE_ALIGNMENT,
    }
    present = {c.category for c in policy}
    return sorted(expected - present, key=lambda c: c.value)
