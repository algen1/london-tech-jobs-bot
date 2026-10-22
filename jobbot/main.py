from __future__ import annotations

import argparse
import logging
import os
import sys
from datetime import UTC, datetime
from pathlib import Path

import requests
import yaml

from .filters import JobFilter, dedupe
from .models import Job
from .notifier import DiscordNotifier
from .sources import SOURCES
from .sources.base import USER_AGENT
from .storage import SeenStore

log = logging.getLogger("jobbot")
_EPOCH = datetime.min.replace(tzinfo=UTC)


def load_config(path: str | Path) -> dict:
    with open(path) as f:
        return yaml.safe_load(f)


def collect_jobs(config: dict, session: requests.Session) -> list[Job]:
    job_filter = JobFilter.from_config(config)
    matched: list[Job] = []
    for key, source_cls in SOURCES.items():
        source_cfg = config["sources"].get(key, {})
        if not source_cfg.get("enabled"):
            continue
        source = source_cls(source_cfg, session)
        try:
            jobs = source.fetch()
        except Exception as e:  # keep going if one site is down
            log.error("%s failed: %s", source.name, e)
            continue
        kept = [j for j in jobs if job_filter(j, check_location=source.check_location)]
        log.info("%-12s fetched %4d, matched %3d", source.name, len(jobs), len(kept))
        matched += kept
    return dedupe(matched)


def run(config_path: str = "config.yaml", dry_run: bool = False) -> int:
    config = load_config(config_path)
    session = requests.Session()
    session.headers["User-Agent"] = USER_AGENT

    store = SeenStore(config["storage"]["seen_file"], config["storage"].get("keep_days", 60))
    jobs = collect_jobs(config, session)
    new_jobs = [j for j in jobs if j.key not in store]
    new_jobs.sort(key=lambda j: j.posted or _EPOCH, reverse=True)

    limit = config["notifications"].get("max_alerts_per_run", 40)
    to_send = new_jobs[:limit]
    log.info("%d matching jobs, %d new, sending %d", len(jobs), len(new_jobs), len(to_send))

    if dry_run:
        for j in to_send:
            print(f"- [{j.source}] {j.title} @ {j.company} ({j.location})\n  {j.url}")
        return 0

    webhook = os.getenv("DISCORD_WEBHOOK_URL")
    if not webhook:
        log.error("DISCORD_WEBHOOK_URL is not set (use --dry-run to just print jobs)")
        return 1
    DiscordNotifier(webhook, session).send(to_send)

    # Only mark as seen once Discord accepted them, so nothing is lost on failure.
    for j in to_send:
        store.add(j.key)
    pruned = store.prune()
    store.save()
    log.info("Seen store: %d jobs (%d pruned)", len(store), pruned)
    return 0


def main(argv: list[str] | None = None) -> None:
    parser = argparse.ArgumentParser(description="Find London tech internships and graduate jobs.")
    parser.add_argument("--config", default="config.yaml")
    parser.add_argument("--dry-run", action="store_true", help="print matches instead of sending to Discord")
    args = parser.parse_args(argv)

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    try:
        from dotenv import load_dotenv  # optional, for local runs

        load_dotenv()
    except ImportError:
        pass
    sys.exit(run(args.config, args.dry_run))
