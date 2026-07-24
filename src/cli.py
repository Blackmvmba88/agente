from __future__ import annotations

import argparse
import json
import sys
from datetime import datetime, timezone
from pathlib import Path

from .indexer import index_text_source
from .reader.text_reader import SUPPORTED_SUFFIXES
from .registry.registry import SongRegistry


DEFAULT_REGISTRY = Path("data/registry.json")


def _registry_path(value: str | None) -> Path:
    return Path(value) if value else DEFAULT_REGISTRY


def _build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="bm-agent")
    parser.add_argument("--registry", help="registry JSON path")
    sub = parser.add_subparsers(dest="command", required=True)

    scan = sub.add_parser("scan", help="index text files from a file or directory")
    scan.add_argument("path")
    scan.add_argument("--artist", help="default artist for files without Artist: metadata")
    scan.add_argument("--report", help="write structured import report JSON")
    scan.add_argument("--no-backup", action="store_true", help="skip registry backup before save")

    sub.add_parser("list", help="list indexed songs")

    show = sub.add_parser("show", help="show one song by canonical ID")
    show.add_argument("song_id")

    search = sub.add_parser("search", help="search title, artist, lyrics, or ID")
    search.add_argument("query")

    sub.add_parser("validate", help="validate registry invariants")
    sub.add_parser("doctor", help="run catalog integrity diagnostics")
    sub.add_parser("duplicates", help="report duplicate lyrics groups")
    sub.add_parser("conflicts", help="emit structured catalog conflicts")
    sub.add_parser("stats", help="show catalog integrity statistics")
    return parser


def _discover_sources(path: Path) -> list[Path]:
    if path.is_file():
        return [path]
    if not path.is_dir():
        raise FileNotFoundError(path)
    return sorted(
        candidate
        for candidate in path.rglob("*")
        if candidate.is_file() and candidate.suffix.lower() in SUPPORTED_SUFFIXES
    )


def _write_import_report(path: Path, report: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(
        json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
    )


def _cmd_scan(args: argparse.Namespace) -> int:
    registry_path = _registry_path(args.registry)
    registry = SongRegistry.load(registry_path)
    sources = _discover_sources(Path(args.path))

    successes: list[dict[str, str]] = []
    failures: list[dict[str, str]] = []

    for source in sources:
        try:
            song = index_text_source(source, registry, default_artist=args.artist)
            print(f"indexed {song.song_id}  {song.title}")
            successes.append(
                {
                    "source": str(source),
                    "song_id": song.song_id,
                    "title": song.title,
                }
            )
        except (OSError, UnicodeError, ValueError) as exc:
            print(f"error {source}: {exc}", file=sys.stderr)
            failures.append(
                {
                    "source": str(source),
                    "error_type": type(exc).__name__,
                    "error": str(exc),
                }
            )

    registry.save(registry_path, backup=not args.no_backup)

    report = {
        "schema_version": 1,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "source_root": str(Path(args.path)),
        "registry": str(registry_path),
        "discovered": len(sources),
        "indexed": len(successes),
        "failed": len(failures),
        "successes": successes,
        "failures": failures,
    }
    if args.report:
        report_path = Path(args.report)
        _write_import_report(report_path, report)
        print(f"report={report_path}")

    print(
        f"indexed={len(successes)} failed={len(failures)} registry={registry_path}"
    )
    return 1 if failures else 0


def _cmd_list(args: argparse.Namespace) -> int:
    registry = SongRegistry.load(_registry_path(args.registry))
    for song in sorted(registry.songs, key=lambda item: item.song_id):
        print(f"{song.song_id}\t{song.title}\t{song.artist}")
    return 0


def _cmd_show(args: argparse.Namespace) -> int:
    registry = SongRegistry.load(_registry_path(args.registry))
    song = registry.get(args.song_id)
    if song is None:
        print(f"song not found: {args.song_id}", file=sys.stderr)
        return 1

    print(f"song_id: {song.song_id}")
    print(f"title: {song.title}")
    print(f"artist: {song.artist}")
    print(f"lyrics_id: {song.lyrics_id}")
    print(f"source: {song.source_path}")
    print("lyrics:")
    print(song.lyrics)
    return 0


def _cmd_search(args: argparse.Namespace) -> int:
    registry = SongRegistry.load(_registry_path(args.registry))
    matches = registry.search(args.query)
    for song in matches:
        print(f"{song.song_id}\t{song.title}\t{song.artist}")
    return 0


def _cmd_validate(args: argparse.Namespace) -> int:
    registry = SongRegistry.load(_registry_path(args.registry))
    errors = registry.validate()
    if not errors:
        print(f"ok: {len(registry.songs)} songs")
        return 0

    for error in errors:
        print(error, file=sys.stderr)
    return 1


def _cmd_doctor(args: argparse.Namespace) -> int:
    registry = SongRegistry.load(_registry_path(args.registry))
    findings = registry.doctor()
    if not findings:
        print(f"healthy: {len(registry.songs)} songs")
        return 0
    for finding in findings:
        print(finding)
    return 1


def _cmd_duplicates(args: argparse.Namespace) -> int:
    registry = SongRegistry.load(_registry_path(args.registry))
    groups = registry.duplicate_groups()
    if not groups:
        print("no duplicate lyrics groups")
        return 0
    for group in groups:
        ids = ", ".join(song.song_id for song in group)
        print(f"duplicate lyrics: {ids}")
    return 1


def _cmd_conflicts(args: argparse.Namespace) -> int:
    registry = SongRegistry.load(_registry_path(args.registry))
    report = registry.conflict_report()
    print(json.dumps(report, ensure_ascii=False, indent=2, sort_keys=True))
    return 1 if report else 0


def _cmd_stats(args: argparse.Namespace) -> int:
    registry = SongRegistry.load(_registry_path(args.registry))
    stats = registry.stats()
    for key in sorted(stats):
        print(f"{key}: {stats[key]}")
    return 0


def main(argv: list[str] | None = None) -> int:
    args = _build_parser().parse_args(argv)
    handlers = {
        "scan": _cmd_scan,
        "list": _cmd_list,
        "show": _cmd_show,
        "search": _cmd_search,
        "validate": _cmd_validate,
        "doctor": _cmd_doctor,
        "duplicates": _cmd_duplicates,
        "conflicts": _cmd_conflicts,
        "stats": _cmd_stats,
    }
    return handlers[args.command](args)


if __name__ == "__main__":
    raise SystemExit(main())
