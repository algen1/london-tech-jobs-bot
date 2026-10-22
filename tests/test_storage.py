from datetime import date

from jobbot.storage import SeenStore


def test_roundtrip(tmp_path):
    path = tmp_path / "seen.json"
    store = SeenStore(path)
    store.add("monzo|graduate engineer")
    store.save()

    reloaded = SeenStore(path)
    assert "monzo|graduate engineer" in reloaded
    assert "other|job" not in reloaded


def test_missing_or_empty_file(tmp_path):
    assert len(SeenStore(tmp_path / "nope.json")) == 0
    empty = tmp_path / "empty.json"
    empty.write_text("")
    assert len(SeenStore(empty)) == 0


def test_prune_old_entries(tmp_path):
    store = SeenStore(tmp_path / "seen.json", keep_days=30)
    store.add("old", today=date(2026, 1, 1))
    store.add("new", today=date(2026, 2, 20))
    assert store.prune(today=date(2026, 3, 1)) == 1
    assert "old" not in store and "new" in store
