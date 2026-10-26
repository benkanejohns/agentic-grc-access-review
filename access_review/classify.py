from anthropic import Anthropic
from pydantic import ValidationError

from access_review.models import AccessRecord, Classification

_CLIENT: Anthropic | None = None


def _client() -> Anthropic:
    global _CLIENT
    if _CLIENT is None:
        _CLIENT = Anthropic()
    return _CLIENT


CLASSIFY_TOOL = {
    "name": "classify_access",
    "description": (
        "Classify an access grant's privilege level and whether the role "
        "fits the user's department. Return only values from the fixed "
        "enums; never invent a new category."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "privilege_level": {
                "type": "string",
                "enum": ["read-only", "service-scoped-write", "full-admin", "unknown"],
            },
            "department_fit": {
                "type": "string",
                "enum": ["appropriate", "mismatch", "insufficient-info"],
            },
            "rationale": {
                "type": "string",
                "description": "One sentence explaining both classifications.",
            },
        },
        "required": ["privilege_level", "department_fit", "rationale"],
    },
}


def classify(record: AccessRecord, model: str = "claude-sonnet-5") -> Classification:
    """Standard Principle 2: the model's only job is to read the role/policy
    text and the department, and classify against the fixed taxonomy above.
    `tool_choice` forces the response through that schema; the model cannot
    return free text here even if it wanted to. It never decides whether
    the access is acceptable, that's `rules.evaluate`'s job, running on
    plain deterministic logic that never sees this function.
    """
    response = _client().messages.create(
        model=model,
        # Generous headroom: `required` in the tool schema is a strong hint
        # to the model, not a hard guarantee from the API. A tight budget
        # that truncates mid-JSON silently drops whichever field the model
        # was generating last, exactly the failure mode this guards against.
        max_tokens=1024,
        tools=[CLASSIFY_TOOL],
        tool_choice={"type": "tool", "name": "classify_access"},
        messages=[
            {
                "role": "user",
                "content": (
                    f"Role or policy: {record.role_or_policy}\n"
                    f"Department: {record.department or 'unknown'}\n"
                    "Classify this access grant."
                ),
            }
        ],
    )
    tool_use = next(block for block in response.content if block.type == "tool_use")
    try:
        return Classification(**tool_use.input)
    except ValidationError as e:
        raise ValueError(
            f"Model returned an incomplete classification for "
            f"{record.user_id} (stop_reason={response.stop_reason!r}): "
            f"{tool_use.input!r}"
        ) from e
