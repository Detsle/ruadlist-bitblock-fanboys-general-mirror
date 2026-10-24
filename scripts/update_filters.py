#!/usr/bin/env python3
"""Refresh the combined EasyList + RU AdList filter and the existing BitBlock mirror."""
from __future__ import annotations

from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
import sys
import urllib.request

ROOT = Path(".")
COMBINED_OUT = ROOT / "ruadlist+easylist.txt"
BITBLOCK_OUT = ROOT / "main" / "bitblock.txt"
USER_AGENT = "Detsle-Adblock-Mirror/1.0 (GitHub Actions)"
MAX_AGE_DAYS = 30
FUTURE_TOLERANCE_DAYS = 1

PRIMARY_COMBINED = "https://easylist-downloads.adblockplus.org/ruadlist+easylist.txt"
EASYLIST_SOURCES = [
    "https://easylist.to/easylist/easylist.txt",
    "https://raw.githubusercontent.com/thedoggybrad/easylist-mirror/main/easylist.txt",
]
RUADLIST_SOURCES = [
    "https://easylist-downloads.adblockplus.org/advblock.txt",
    "https://raw.githubusercontent.com/thedoggybrad/easylist-mirror/main/advblock.txt",
]
BITBLOCK_SOURCES = [
    "https://easylist-downloads.adblockplus.org/bitblock.txt",
    "https://raw.githubusercontent.com/thedoggybrad/easylist-mirror/main/bitblock.txt",
]

HEAD = "[Adblock Plus 2.0]"
MIN_COMBINED_BYTES = 500_000
MIN_COMBINED_LINES = 50_000
MIN_COMPONENT_BYTES = 100_000
MIN_COMPONENT_LINES = 10_000
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


def combine(easylist: str, ruadlist: str, easy_url: str, ru_url: str) -> str:
    now = datetime.now(timezone.utc).strftime("%d %b %Y %H:%M UTC")
    output = [
        HEAD,
        "! Title: RU AdList + EasyList (automatically mirrored)",
        f"! Last modified: {now}",
        "! Expires: 1 days (mirror refreshes every 6 hours)",
        f"! Source: {PRIMARY_COMBINED}",
        "! Fallback sources:",
        f"! - EasyList: {easy_url}",
        f"! - RU AdList: {ru_url}",
        "! Exact duplicate lines are removed; filter rules are otherwise preserved.",
        "!",
        "! ==================== EasyList ====================",
    ]
    seen = set(output)
    metadata_prefixes = (
        "! checksum:", "! version:", "! title:", "! last modified:",
        "! expires:", "! homepage:", "! license:", "! description:",
        "! redirect:", "! syntax:",
    )

    def append_body(text: str) -> None:
        for line in text.splitlines()[1:]:
            if line.lower().startswith(metadata_prefixes):
                continue
            if line not in seen:
                output.append(line)
                seen.add(line)

    append_body(easylist)
    marker = "! ==================== RU AdList ===================="
    output.extend(["!", marker])
    seen.add("!")
    seen.add(marker)
    append_body(ruadlist)
    result = "\n".join(output).rstrip() + "\n"
    validate(result, "fallback-combined EasyList + RU AdList", MIN_COMBINED_BYTES, MIN_COMBINED_LINES)
    return result


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
        try:
            text = fetch(PRIMARY_COMBINED, MIN_COMBINED_BYTES, MIN_COMBINED_LINES)
            print(f"Combined filter obtained directly from {PRIMARY_COMBINED}")
        except Exception as primary_error:
            print(f"Primary combined source failed; trying component sources: {primary_error}", file=sys.stderr)
            easylist, easy_url = fetch_first(
                "EasyList", EASYLIST_SOURCES, MIN_COMPONENT_BYTES, MIN_COMPONENT_LINES
            )
            ruadlist, ru_url = fetch_first(
                "RU AdList", RUADLIST_SOURCES, MIN_COMPONENT_BYTES, MIN_COMPONENT_LINES
            )
            text = combine(easylist, ruadlist, easy_url, ru_url)
            print("Successfully assembled fallback filter from current components")
        # Verify the exact content before replacing a prior good version.
        validate(text, "combined filter final validation", MIN_COMBINED_BYTES, MIN_COMBINED_LINES)
        return atomic_write(COMBINED_OUT, text)
    except Exception as exc:
        print(f"ERROR updating combined filter; previous file is preserved: {exc}", file=sys.stderr)
        if not COMBINED_OUT.exists():
            return False
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
    updated_combined = update_combined()
    updated_bitblock = update_bitblock()
    if not COMBINED_OUT.exists() and not BITBLOCK_OUT.exists():
        print("No valid filter could be downloaded and no previous copies exist.", file=sys.stderr)
        return 1
    print(f"Update run complete. Combined changed={updated_combined}; BitBlock changed={updated_bitblock}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
