from __future__ import annotations

import json
from datetime import date, timedelta
from pathlib import Path


class SeenStore:
    """Remembers which jobs have already been sent, as {job_key: first_seen_iso_date}.

    The JSON file is committed back to the repo by the GitHub Action, which is
    how state survives between otherwise stateless workflow runs.
    """

    def __init__(self, path: str | Path, keep_days: int = 60):
        self.path = Path(path)
        self.keep_days = keep_days
        self._seen: dict[str, str] = {}
        if self.path.exists():
            text = self.path.read_text().strip()
            self._seen = json.loads(text) if text else {}

    def __contains__(self, key: str) -> bool:
        return key in self._seen

    def __len__(self) -> int:
        return len(self._seen)

    def add(self, key: str, today: date | None = None) -> None:
        self._seen.setdefault(key, (today or date.today()).isoformat())

    def prune(self, today: date | None = None) -> int:
        cutoff = ((today or date.today()) - timedelta(days=self.keep_days)).isoformat()
        old = [k for k, d in self._seen.items() if d < cutoff]
        for k in old:
            del self._seen[k]
        return len(old)

    def save(self) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self.path.write_text(json.dumps(self._seen, indent=1, sort_keys=True) + "\n")
