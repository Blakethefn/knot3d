"""Discover and print the runtime APIs used by the knot engine."""

from __future__ import annotations

from pathlib import Path

from src.api_discovery import build_discovery_markdown


def main() -> int:
    report = build_discovery_markdown()
    print(report.markdown)
    decisions_path = Path("DECISIONS.md")
    if decisions_path.exists():
        existing = decisions_path.read_text(encoding="utf-8")
        if "# Runtime API Discovery" not in existing:
            decisions_path.write_text(existing.rstrip() + "\n\n" + report.markdown + "\n", encoding="utf-8")
    else:
        decisions_path.write_text(report.markdown + "\n", encoding="utf-8")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
