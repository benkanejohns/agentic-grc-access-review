from abc import ABC, abstractmethod
from pathlib import Path

from access_review.models import AccessRecord


class Connector(ABC):
    """Reads one cloud IAM platform's export format and normalises it into
    AccessRecord objects. This is the only part of the pipeline that knows
    anything about AWS, Azure, or GCP specifically; classification, rules,
    logging, and reporting are all provider-agnostic. Add Azure or GCP
    support by implementing this interface, not by touching anything else.
    """

    name: str

    @abstractmethod
    def load(self, path: Path) -> list[AccessRecord]:
        ...
