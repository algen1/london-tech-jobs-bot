"""Adzuna API - a UK job aggregator. Free key: https://developer.adzuna.com/"""

from __future__ import annotations

import os

from ..models import Job
from .base import Source, format_salary, log, parse_iso

API_URL = "https://api.adzuna.com/v1/api/jobs/gb/search/1"


def parse_results(data: dict) -> list[Job]:
    jobs = []
    for r in data.get("results", []):
        jobs.append(
            Job(
                title=r.get("title", "").strip(),
                company=(r.get("company") or {}).get("display_name", "Unknown"),
                location=(r.get("location") or {}).get("display_name", "London"),
                url=r.get("redirect_url", ""),
                source="Adzuna",
                posted=parse_iso(r.get("created")),
                salary=format_salary(r.get("salary_min"), r.get("salary_max")),
            )
        )
    return jobs


class AdzunaSource(Source):
    name = "Adzuna"
    check_location = False

    def fetch(self) -> list[Job]:
        app_id, app_key = os.getenv("ADZUNA_APP_ID"), os.getenv("ADZUNA_APP_KEY")
        if not (app_id and app_key):
            log.warning("Adzuna skipped: ADZUNA_APP_ID / ADZUNA_APP_KEY not set")
            return []
        jobs = []
        for query in self.config["queries"]:
            params = {
                "app_id": app_id,
                "app_key": app_key,
                "what": query,
                "where": "London",
                "distance": 25,
                "max_days_old": self.config.get("max_days_old", 7),
                "results_per_page": 50,
                "sort_by": "date",
            }
            jobs += parse_results(self.get_json(API_URL, params=params))
        return jobs
