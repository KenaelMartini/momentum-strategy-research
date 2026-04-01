from __future__ import annotations

from pathlib import Path

import yaml

from momentum_strategy.research.archive_run import archive_reference_run


def test_archive_reference_run_writes_metadata(tmp_path: Path) -> None:
    dest = tmp_path / "archive_test"
    archive_reference_run(dest, copy_latest_event_driven=False)
    meta = dest / "run_metadata.yaml"
    assert meta.exists()
    data = yaml.safe_load(meta.read_text(encoding="utf-8"))
    assert "archived_at_utc" in data
    assert "configs_copied" in data
    assert (dest / "configs_snapshot").is_dir()
