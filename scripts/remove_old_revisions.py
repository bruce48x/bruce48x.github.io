from __future__ import annotations

import datetime as dt
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional

import yaml

CONTENT_DIR = Path("content/posts")


@dataclass
class PostInfo:
    path: Path
    title: str
    date: Optional[dt.datetime]
    raw_date: Optional[str]


def parse_front_matter(path: Path) -> Optional[PostInfo]:
    text = path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        return None
    parts = text.split("---", 2)
    if len(parts) < 3:
        return None
    front_matter = yaml.safe_load(parts[1]) or {}
    title = front_matter.get("title")
    if not title:
        return None
    raw_date = front_matter.get("date")
    parsed_date = parse_date(raw_date)
    return PostInfo(path=path, title=str(title).strip(), date=parsed_date, raw_date=raw_date)


def parse_date(value: Optional[str]) -> Optional[dt.datetime]:
    if not value:
        return None
    if isinstance(value, dt.datetime):
        return value
    if isinstance(value, dt.date):
        return dt.datetime.combine(value, dt.time.min)
    if isinstance(value, str):
        candidate = value.strip()
        if not candidate:
            return None
        try:
            if candidate.endswith("Z"):
                candidate = candidate[:-1] + "+00:00"
            return dt.datetime.fromisoformat(candidate)
        except ValueError:
            pass
        try:
            return dt.datetime.strptime(candidate, "%Y-%m-%d %H:%M:%S")
        except ValueError:
            pass
        try:
            return dt.datetime.strptime(candidate, "%Y-%m-%d")
        except ValueError:
            return None
    return None


def main() -> int:
    if not CONTENT_DIR.exists():
        print(f"[error] directory not found: {CONTENT_DIR}")
        return 1

    by_title: Dict[str, List[PostInfo]] = {}

    for path in sorted(CONTENT_DIR.glob("*.md")):
        info = parse_front_matter(path)
        if not info:
            continue
        by_title.setdefault(info.title, []).append(info)

    removed: List[Path] = []

    for title, items in by_title.items():
        if len(items) < 2:
            continue
        items.sort(key=lambda x: (x.date or dt.datetime.min, x.path.name))
        keep = items[-1]
        to_remove = [item for item in items if item.path != keep.path]

        print(f"[keep] {title!r} -> {keep.path} (date={keep.raw_date})")

        for item in to_remove:
            print(f"[remove] {item.path} (date={item.raw_date})")
            item.path.unlink()
            removed.append(item.path)

    if not removed:
        print("No duplicate posts found.")
    else:
        print(f"Removed {len(removed)} older post(s).")

    return 0


if __name__ == "__main__":
    sys.exit(main())

