"""Reed.co.uk API - UK job board. Free key: https://www.reed.co.uk/developers/jobseeker"""

from __future__ import annotations

import os
from datetime import UTC, datetime

from ..models import Job
from .base import Source, format_salary, log

API_URL = "https://www.reed.co.uk/api/1.0/search"


def _parse_date(value: str | None) -> datetime | None:
    try:
        return datetime.strptime(value, "%d/%m/%Y").replace(tzinfo=UTC)
    except (TypeError, ValueError):
        return None


def parse_results(data: dict) -> list[Job]:
    jobs = []
    for r in data.get("results", []):
        jobs.append(
            Job(
                title=(r.get("jobTitle") or "").strip(),
                company=r.get("employerName") or "Unknown",
                location=r.get("locationName") or "London",
                url=r.get("jobUrl", ""),
                source="Reed",
                posted=_parse_date(r.get("date")),
                salary=format_salary(r.get("minimumSalary"), r.get("maximumSalary")),
            )
        )
    return jobs


class ReedSource(Source):
    name = "Reed"
    check_location = False

    def fetch(self) -> list[Job]:
        api_key = os.getenv("REED_API_KEY")
        if not api_key:
            log.warning("Reed skipped: REED_API_KEY not set")
            return []
        jobs = []
        # Reed has a dedicated "graduate" flag, so we run each query twice:
        # once for graduate roles and once for everything (to catch interns/juniors).
        for query in self.config["queries"]:
            for graduate in (True, False):
                params = {
                    "keywords": query,
                    "locationName": "London",
                    "distanceFromLocation": self.config.get("distance_miles", 15),
                    "resultsToTake": 100,
                }
                if graduate:
                    params["graduate"] = "true"
                # Reed uses HTTP basic auth with the key as the username.
                jobs += parse_results(self.get_json(API_URL, params=params, auth=(api_key, "")))
        return jobs
