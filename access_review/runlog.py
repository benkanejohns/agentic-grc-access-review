import json
from datetime import datetime, timezone
from pathlib import Path

from access_review.models import AccessRecord, Classification, ReviewVerdict

RUNS_DIR = Path("runs")


def new_run_path() -> Path:
    RUNS_DIR.mkdir(exist_ok=True)
    ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
    return RUNS_DIR / f"{ts}.jsonl"


def append(
    path: Path,
    record: AccessRecord,
    classification: Classification,
    verdict: ReviewVerdict,
    model: str,
) -> None:
    """Standard Principle 1: every classification is logged with the model
    version and timestamp it ran under, so a result can be replayed exactly
    rather than regenerated.
    """
    entry = {
        "logged_at": datetime.now(timezone.utc).isoformat(),
        "model": model,
        "record": record.model_dump(mode="json"),
        "classification": classification.model_dump(mode="json"),
        "verdict": verdict.model_dump(mode="json"),
    }
    with open(path, "a", encoding="utf-8") as f:
        f.write(json.dumps(entry) + "\n")


def load(path: Path) -> list[dict]:
    with open(path, encoding="utf-8") as f:
        return [json.loads(line) for line in f if line.strip()]
