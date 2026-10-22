from __future__ import annotations

import re
from collections.abc import Iterable

from .models import Job


def _compile(terms: Iterable[str]) -> re.Pattern:
    # Word boundaries stop "ai" matching "maintain" or "it" matching "with".
    escaped = sorted((re.escape(t.lower()) for t in terms), key=len, reverse=True)
    return re.compile(r"(?<![a-z0-9])(?:" + "|".join(escaped) + r")(?![a-z0-9])")


class JobFilter:
    def __init__(self, early_career, tech, exclude, location_keywords):
        self.early = _compile(early_career)
        self.tech = _compile(tech)
        self.exclude = _compile(exclude)
        self.location_keywords = [k.lower() for k in location_keywords]

    @classmethod
    def from_config(cls, config: dict) -> JobFilter:
        f = config["filters"]
        return cls(f["early_career"], f["tech"], f["exclude"], config["location"]["keywords"])

    def title_matches(self, title: str) -> bool:
        t = title.lower()
        return bool(self.early.search(t) and self.tech.search(t) and not self.exclude.search(t))

    def location_matches(self, location: str) -> bool:
        loc = location.lower()
        return any(k in loc for k in self.location_keywords)

    def __call__(self, job: Job, check_location: bool = True) -> bool:
        if not self.title_matches(job.title):
            return False
        return not check_location or self.location_matches(job.location)


def dedupe(jobs: Iterable[Job]) -> list[Job]:
    seen: dict[str, Job] = {}
    for job in jobs:
        seen.setdefault(job.key, job)
    return list(seen.values())
