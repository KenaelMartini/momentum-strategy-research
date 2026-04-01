"""Copie configs + manifeste + métadonnées pour traçabilité d'un run (contraintes institutionnelles)."""

from __future__ import annotations

import argparse
import hashlib
import shutil
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

import yaml

from momentum_strategy.paths import configs_dir, project_root


def _file_sha256(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(65536), b""):
            h.update(chunk)
    return h.hexdigest()


def archive_reference_run(
    dest: Path,
    *,
    copy_latest_event_driven: bool = False,
    event_driven_dir: Path | None = None,
) -> Path:
    """
    Crée ``dest`` avec copies des configs, manifeste matrice, métadonnées.
    Si ``copy_latest_event_driven``, copie le dernier jeu stats_*/rebal_* du dossier event_driven.
    """
    root = project_root()
    dest = Path(dest).resolve()
    dest.mkdir(parents=True, exist_ok=True)
    cfg_dst = dest / "configs_snapshot"
    cfg_dst.mkdir(exist_ok=True)

    config_names = [
        "strategy_defaults.yaml",
        "risk_event_driven.yaml",
        "universe.yaml",
        "ibkr.yaml",
        "research_windows.yaml",
        "sensitivity_presets.yaml",
        "sensitivity_presets_train1.yaml",
        "sensitivity_rebal_train1.yaml",
        "sensitivity_book_train1.yaml",
        "train1_levers_presets.yaml",
    ]
    copied: list[str] = []
    digests: dict[str, str] = {}
    cfg = configs_dir()
    for name in config_names:
        src = cfg / name
        if src.exists():
            shutil.copy2(src, cfg_dst / name)
            copied.append(name)
            digests[name] = _file_sha256(cfg_dst / name)

    manifest_src = root / "data" / "processed" / "price_matrix_manifest.yaml"
    manifest_note = ""
    if manifest_src.exists():
        shutil.copy2(manifest_src, dest / "price_matrix_manifest.yaml")
        digests["price_matrix_manifest.yaml"] = _file_sha256(dest / "price_matrix_manifest.yaml")
        manifest_note = str(manifest_src.resolve())
    else:
        manifest_note = "(absent — régénérer la matrice avant un run officiel)"

    git_sha = ""
    try:
        r = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=root,
            capture_output=True,
            text=True,
            timeout=5,
            check=False,
        )
        if r.returncode == 0:
            git_sha = r.stdout.strip()
    except (OSError, subprocess.TimeoutExpired):
        pass

    ed_dir = Path(event_driven_dir) if event_driven_dir else (root / "results" / "event_driven")
    artifacts: list[str] = []
    if copy_latest_event_driven and ed_dir.is_dir():
        art_dst = dest / "event_driven_artifacts"
        art_dst.mkdir(exist_ok=True)
        stats_files = sorted(ed_dir.glob("stats_*.csv"))
        if stats_files:
            latest = stats_files[-1]
            ts = latest.stem.replace("stats_", "", 1)
            for pattern in (
                f"stats_{ts}.csv",
                f"rebal_diagnostics_{ts}.csv",
                f"regime_performance_effective_{ts}.csv",
                f"strategy_vs_benchmark_{ts}.html",
            ):
                p = ed_dir / pattern
                if p.exists():
                    shutil.copy2(p, art_dst / p.name)
                    artifacts.append(pattern)

    meta = {
        "archived_at_utc": datetime.now(timezone.utc).isoformat(),
        "python": sys.version.split()[0],
        "project_root": str(root.resolve()),
        "git_commit": git_sha or None,
        "configs_copied": copied,
        "sha256_configs": digests,
        "price_matrix_manifest_source": manifest_note,
        "example_full_backtest_command": (
            "mstrat event-backtest --data data/processed/price_matrix.csv "
            "--output results/event_driven"
        ),
        "example_train1_command": "mstrat event-backtest --train1 --skip-baseline",
        "example_oos1_command": "mstrat event-backtest --oos1 --skip-baseline",
        "event_driven_artifacts_copied": artifacts,
    }
    (dest / "run_metadata.yaml").write_text(
        yaml.safe_dump(meta, sort_keys=False, allow_unicode=True),
        encoding="utf-8",
    )
    return dest


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="Archiver configs + manifeste (+ optionnel derniers CSV/HTML event-driven)."
    )
    parser.add_argument(
        "--dest",
        type=Path,
        default=None,
        help="Dossier cible (défaut: results/archive/run_<timestamp_utc>)",
    )
    parser.add_argument(
        "--copy-latest-results",
        action="store_true",
        help="Copier le dernier run stats_*.csv et fichiers associés depuis results/event_driven",
    )
    parser.add_argument(
        "--event-driven-dir",
        type=Path,
        default=None,
        help="Dossier des résultats event-driven (défaut: <racine>/results/event_driven)",
    )
    args = parser.parse_args(argv)
    root = project_root()
    dest = args.dest
    if dest is None:
        ts = datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%SZ")
        dest = root / "results" / "archive" / f"run_{ts}"
    out = archive_reference_run(
        dest,
        copy_latest_event_driven=args.copy_latest_results,
        event_driven_dir=args.event_driven_dir,
    )
    print(f"Archive écrite : {out}")
    print(f"  → {out / 'run_metadata.yaml'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
