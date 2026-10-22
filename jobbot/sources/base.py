from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import UTC, datetime

import requests

from ..models import Job

log = logging.getLogger(__name__)

USER_AGENT = "london-tech-jobs-bot/1.0 (+https://github.com/)"


class Source(ABC):
    name: str = "source"
    # Aggregators are already searched around London; company boards list
    # jobs worldwide, so those need the location filter applied.
    check_location: bool = True

    def __init__(self, config: dict, session: requests.Session):
        self.config = config
        self.session = session

    def get_json(self, url: str, **kwargs):
        kwargs.setdefault("timeout", 30)
        resp = self.session.get(url, **kwargs)
        resp.raise_for_status()
        return resp.json()

    @abstractmethod
    def fetch(self) -> list[Job]: ...


def parse_iso(value) -> datetime | None:
    if not value:
        return None
    try:
        dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
    except ValueError:
        return None
    return dt if dt.tzinfo else dt.replace(tzinfo=UTC)


def format_salary(low, high, currency: str = "£") -> str | None:
    if not low and not high:
        return None
    if low and high and round(low) != round(high):
        return f"{currency}{low:,.0f} - {currency}{high:,.0f}"
    return f"{currency}{(low or high):,.0f}"
