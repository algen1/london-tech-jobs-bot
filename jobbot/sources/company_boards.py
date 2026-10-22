"""Public company job boards (Greenhouse, Lever, Ashby).

Lots of tech companies host their careers page on one of these platforms,
and each exposes a public, documented JSON API - no key needed.
"""

from __future__ import annotations

from datetime import UTC, datetime

from ..models import Job
from .base import Source, log, parse_iso


def parse_greenhouse(data: dict, board: str) -> list[Job]:
    return [
        Job(
            title=j.get("title", "").strip(),
            company=(j.get("company_name") or board.title()).strip(),
            location=(j.get("location") or {}).get("name", ""),
            url=j.get("absolute_url", ""),
            source="Greenhouse",
            posted=parse_iso(j.get("first_published") or j.get("updated_at")),
        )
        for j in data.get("jobs", [])
    ]


def parse_lever(data: list, board: str) -> list[Job]:
    jobs = []
    for j in data:
        created = j.get("createdAt")
        cats = j.get("categories") or {}
        locations = [cats.get("location", "")] + (cats.get("allLocations") or [])
        jobs.append(
            Job(
                title=j.get("text", "").strip(),
                company=board.title(),
                location=", ".join(dict.fromkeys(filter(None, locations))),
                url=j.get("hostedUrl", ""),
                source="Lever",
                posted=datetime.fromtimestamp(created / 1000, UTC) if created else None,
            )
        )
    return jobs


def parse_ashby(data: dict, board: str) -> list[Job]:
    jobs = []
    for j in data.get("jobs", []):
        if j.get("isListed") is False:
            continue
        locations = [j.get("location", "")] + [s.get("location", "") for s in j.get("secondaryLocations") or []]
        jobs.append(
            Job(
                title=j.get("title", "").strip(),
                company=board.title(),
                location=", ".join(filter(None, locations)),
                url=j.get("jobUrl", ""),
                source="Ashby",
                posted=parse_iso(j.get("publishedAt")),
            )
        )
    return jobs


class _BoardSource(Source):
    url_template: str
    parser = None

    def fetch(self) -> list[Job]:
        jobs = []
        for board in self.config.get("boards", []):
            try:
                data = self.get_json(self.url_template.format(board=board))
            except Exception as e:  # one dead board shouldn't stop the others
                log.warning("%s board %r failed: %s", self.name, board, e)
                continue
            jobs += type(self).parser(data, board)
        return jobs


class GreenhouseSource(_BoardSource):
    name = "Greenhouse"
    url_template = "https://boards-api.greenhouse.io/v1/boards/{board}/jobs"
    parser = parse_greenhouse


class LeverSource(_BoardSource):
    name = "Lever"
    url_template = "https://api.lever.co/v0/postings/{board}?mode=json"
    parser = parse_lever


class AshbySource(_BoardSource):
    name = "Ashby"
    url_template = "https://api.ashbyhq.com/posting-api/job-board/{board}"
    parser = parse_ashby
