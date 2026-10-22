"""Google Jobs via SerpAPI. Free key (100 searches/month): https://serpapi.com/"""

from __future__ import annotations

import os
from datetime import UTC, datetime

from ..models import Job
from .base import Source, log

API_URL = "https://serpapi.com/search.json"


def parse_results(data: dict) -> list[Job]:
    jobs = []
    for r in data.get("jobs_results", []):
        apply = r.get("apply_options") or []
        url = apply[0]["link"] if apply else r.get("share_link", "")
        jobs.append(
            Job(
                title=(r.get("title") or "").strip(),
                company=r.get("company_name") or "Unknown",
                location=r.get("location") or "London",
                url=url,
                source="Google Jobs",
            )
        )
    return jobs


class GoogleJobsSource(Source):
    name = "Google Jobs"
    check_location = False

    def fetch(self) -> list[Job]:
        api_key = os.getenv("SERPAPI_KEY")
        if not api_key:
            log.warning("Google Jobs skipped: SERPAPI_KEY not set")
            return []
        hour = datetime.now(UTC).hour
        if hour not in self.config.get("run_hours_utc", []) and not os.getenv("FORCE_GOOGLE_JOBS"):
            log.info("Google Jobs skipped: only runs at UTC hours %s to save quota", self.config.get("run_hours_utc"))
            return []
        jobs = []
        for query in self.config["queries"]:
            params = {
                "engine": "google_jobs",
                "q": query,
                "location": "London, England, United Kingdom",
                "gl": "uk",
                "hl": "en",
                "api_key": api_key,
            }
            jobs += parse_results(self.get_json(API_URL, params=params))
        return jobs
