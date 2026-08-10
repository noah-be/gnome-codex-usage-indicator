"""Command-line interface used by the GNOME Shell extension."""

from __future__ import annotations

import argparse
from datetime import datetime
import json
import sys
from typing import Sequence

from .app_server import (
    DEFAULT_LIMIT_ID,
    DEFAULT_TIMEOUT_SECONDS,
    CodexUsageError,
    fetch_usage,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Read the current Codex weekly usage window.")
    parser.add_argument(
        "--codex",
        metavar="PATH",
        help="path to the Codex CLI executable")
    parser.add_argument(
        "--limit-id",
        default=DEFAULT_LIMIT_ID,
        help=f"rate-limit identifier (default: {DEFAULT_LIMIT_ID})")
    parser.add_argument(
        "--timeout",
        type=float,
        default=DEFAULT_TIMEOUT_SECONDS,
        help=f"app-server timeout in seconds (default: {DEFAULT_TIMEOUT_SECONDS:g})")
    parser.add_argument(
        "--format",
        choices=("json", "text"),
        default="text",
        help="output format (default: text)")
    parser.add_argument(
        "--pretty",
        action="store_true",
        help="pretty-print JSON output")
    return parser


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)

    try:
        snapshot = fetch_usage(
            codex_binary=args.codex,
            limit_id=args.limit_id,
            timeout=args.timeout,
        )
    except CodexUsageError as error:
        if args.format == "json":
            print(json.dumps({"ok": False, "error": str(error)}))
        else:
            print(f"codex-usage: {error}", file=sys.stderr)
        return 1

    if args.format == "json":
        indent = 2 if args.pretty else None
        print(json.dumps(snapshot.to_dict(), indent=indent, sort_keys=args.pretty))
    else:
        reset = datetime.fromtimestamp(snapshot.resets_at).astimezone()
        print(
            f"Codex {snapshot.remaining_percent:.0f}% remaining "
            f"· resets {reset:%a %Y-%m-%d %H:%M %Z}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
