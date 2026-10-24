#!/usr/bin/env python3
"""Refresh the official RU AdList + EasyList mirror and the BitBlock mirror."""
from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
import sys
import urllib.request

ROOT = Path(".")
COMBINED_OUT = ROOT / "ruadlist+easylist.txt"
BITBLOCK_OUT = ROOT / "main" / "bitblock.txt"
USER_AGENT = "Detsle-Adblock-Mirror/1.1 (GitHub Actions)"
MAX_AGE_DAYS = 30
FUTURE_TOLERANCE_DAYS = 1

# Use only the official combined list. Do not rebuild it from advblock or other
# components; if the combined source is unavailable, preserve the last good copy.
PRIMARY_COMBINED = "https://easylist-downloads.adblockplus.org/ruadlist+easylist.txt"
BITBLOCK_SOURCES = [
    "https://easylist-downloads.adblockplus.org/bitblock.txt",
    "https://raw.githubusercontent.com/thedoggybrad/easylist-mirror/main/bitblock.txt",
]

HEAD = "[Adblock Plus 2.0]"
MIN_COMBINED_BYTES = 500_000
MIN_COMBINED_LINES = 50_000
MIN_BITBLOCK_BYTES = 100_000
MIN_BITBLOCK_LINES = 10_000


def parse_last_modified(lines: list[str]) -> datetime | None:
    for line in lines:
        if not line.lower().startswith("! last modified:"):
            continue
        value = line.split(":", 1)[1].strip()
        for fmt in ("%d %b %Y %H:%M UTC", "%d %b %Y %H:%M:%S UTC"):
            try:
                return datetime.strptime(value, fmt).replace(tzinfo=timezone.utc)
            except ValueError:
                pass
        try:
            dt = parsedate_to_datetime(value)
            if dt.tzinfo is None:
                dt = dt.replace(tzinfo=timezone.utc)
            return dt.astimezone(timezone.utc)
        except (TypeError, ValueError, OverflowError):
            return None
    return None


def validate(text: str, url: str, min_bytes: int, min_lines: int) -> None:
    if not text.startswith(HEAD):
        raise RuntimeError(f"Unexpected Adblock Plus header from {url}")
    lines = text.splitlines()
    size = len(text.encode("utf-8"))
    if size < min_bytes:
        raise RuntimeError(f"Suspiciously small file from {url}: {size} bytes")
    if len(lines) < min_lines:
        raise RuntimeError(f"Too few lines from {url}: {len(lines)}")
    if not any(x.lower().startswith("! title:") for x in lines[:40]):
        raise RuntimeError(f"Missing list title in {url}")
    modified = parse_last_modified(lines[:40])
    if modified is None:
        raise RuntimeError(f"Missing or invalid last-modified timestamp in {url}")
    age_days = (datetime.now(timezone.utc) - modified).total_seconds() / 86400
    if age_days > MAX_AGE_DAYS:
        raise RuntimeError(f"Upstream list metadata is {age_days:.1f} days old: {url}")
    if age_days < -FUTURE_TOLERANCE_DAYS:
        raise RuntimeError(f"Upstream timestamp is unexpectedly in the future: {url}")


def fetch(url: str, min_bytes: int, min_lines: int) -> str:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": USER_AGENT, "Accept": "text/plain,*/*;q=0.8"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        if getattr(response, "status", 200) != 200:
            raise RuntimeError(f"HTTP {response.status}")
        raw = response.read()
    text = raw.decode("utf-8-sig").replace("\r\n", "\n").replace("\r", "\n").rstrip() + "\n"
    validate(text, url, min_bytes, min_lines)
    return text


def fetch_first(label: str, urls: list[str], min_bytes: int, min_lines: int) -> tuple[str, str]:
    errors = []
    for url in urls:
        try:
            return fetch(url, min_bytes, min_lines), url
        except Exception as exc:
            errors.append(f"{url}: {exc}")
    raise RuntimeError(f"All sources failed for {label}:\n  " + "\n  ".join(errors))


def atomic_write(path: Path, text: str) -> bool:
    path.parent.mkdir(parents=True, exist_ok=True)
    if path.exists() and path.read_text(encoding="utf-8", errors="replace") == text:
        print(f"Unchanged: {path}")
        return False
    temp = path.with_suffix(path.suffix + ".tmp")
    temp.write_text(text, encoding="utf-8", newline="\n")
    temp.replace(path)
    print(f"Updated {path}: {len(text.splitlines()):,} lines, {len(text.encode('utf-8')):,} bytes")
    return True


def update_combined() -> bool:
    try:
        text = fetch(PRIMARY_COMBINED, MIN_COMBINED_BYTES, MIN_COMBINED_LINES)
        print(f"Combined filter obtained from official source: {PRIMARY_COMBINED}")
        # Validate again before replacing the previous known-good file.
        validate(text, PRIMARY_COMBINED, MIN_COMBINED_BYTES, MIN_COMBINED_LINES)
        return atomic_write(COMBINED_OUT, text)
    except Exception as exc:
        print(f"ERROR updating combined filter; previous file is preserved: {exc}", file=sys.stderr)
        return False


def update_bitblock() -> bool:
    try:
        text, source = fetch_first(
            "BitBlock", BITBLOCK_SOURCES, MIN_BITBLOCK_BYTES, MIN_BITBLOCK_LINES
        )
        print(f"BitBlock source: {source}")
        return atomic_write(BITBLOCK_OUT, text)
    except Exception as exc:
        print(f"ERROR updating BitBlock; previous file is preserved: {exc}", file=sys.stderr)
        return False


def main() -> int:
    COMBINED_OUT.parent.mkdir(parents=True, exist_ok=True)
    update_combined()
    update_bitblock()
    if not COMBINED_OUT.exists() and not BITBLOCK_OUT.exists():
        print("No valid filter could be downloaded and no previous copies exist.", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
