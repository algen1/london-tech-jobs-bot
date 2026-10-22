from __future__ import annotations

import re
from dataclasses import dataclass, field
from datetime import datetime


def _normalise(text: str) -> str:
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


@dataclass
class Job:
    title: str
    company: str
    location: str
    url: str
    source: str
    posted: datetime | None = None
    salary: str | None = None
    extra: dict = field(default_factory=dict)

    @property
    def key(self) -> str:
        """Identity used for de-duplication across sources and runs.

        The same role often appears on several sites (e.g. a company board
        and Adzuna), so we key on company + title instead of a source id.
        """
        return f"{_normalise(self.company)}|{_normalise(self.title)}"
