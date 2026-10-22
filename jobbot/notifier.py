from __future__ import annotations

import logging
import time

import requests

from .models import Job

log = logging.getLogger(__name__)

EMBEDS_PER_MESSAGE = 10  # Discord's limit
SOURCE_COLOURS = {
    "Adzuna": 0x2E7D32,
    "Reed": 0xD32F2F,
    "Google Jobs": 0x1A73E8,
    "Greenhouse": 0x24A47F,
    "Lever": 0x6B7280,
    "Ashby": 0x7C3AED,
}


def job_to_embed(job: Job) -> dict:
    fields = [
        {"name": "Company", "value": job.company[:1024] or "-", "inline": True},
        {"name": "Location", "value": job.location[:1024] or "-", "inline": True},
    ]
    if job.salary:
        fields.append({"name": "Salary", "value": job.salary[:1024], "inline": True})
    embed = {
        "title": job.title[:256],
        "url": job.url,
        "color": SOURCE_COLOURS.get(job.source, 0x5865F2),
        "fields": fields,
        "footer": {"text": f"via {job.source}"},
    }
    if job.posted:
        embed["timestamp"] = job.posted.isoformat()
    return embed


class DiscordNotifier:
    def __init__(self, webhook_url: str, session: requests.Session | None = None):
        self.webhook_url = webhook_url
        self.session = session or requests.Session()

    def _post(self, payload: dict) -> None:
        for _ in range(5):
            resp = self.session.post(self.webhook_url, json=payload, timeout=20)
            if resp.status_code == 429:  # rate limited - Discord tells us how long to wait
                time.sleep(float(resp.json().get("retry_after", 2)))
                continue
            resp.raise_for_status()
            return
        raise RuntimeError("Discord kept rate-limiting the webhook")

    def send(self, jobs: list[Job]) -> None:
        if not jobs:
            return
        header = f"**{len(jobs)} new London tech role{'s' if len(jobs) != 1 else ''}** 🎓"
        for i in range(0, len(jobs), EMBEDS_PER_MESSAGE):
            chunk = jobs[i : i + EMBEDS_PER_MESSAGE]
            payload = {"embeds": [job_to_embed(j) for j in chunk]}
            if i == 0:
                payload["content"] = header
            self._post(payload)
            time.sleep(1)
        log.info("Sent %d jobs to Discord", len(jobs))
