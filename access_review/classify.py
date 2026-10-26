from anthropic import Anthropic

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
        max_tokens=300,
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
    return Classification(**tool_use.input)
