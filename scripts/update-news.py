#!/usr/bin/env python3
"""note・PR TIMES の公式RSSからお知らせデータを生成する。"""

from __future__ import annotations

import html
import json
import os
import re
import tempfile
import urllib.request
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from urllib.parse import urlparse


ROOT = Path(__file__).resolve().parents[1]
OUTPUT = ROOT / "data" / "news.json"
NOTE_RSS = "https://note.com/miraiz_t/rss"
PRTIMES_RSS = "https://prtimes.jp/companyrdf.php?company_id=189122"
USER_AGENT = "MIRAIZ-News-Updater/1.0 (+https://miraiz.sofi-school.com)"
MAX_ITEMS_PER_SOURCE = 12


def fetch(url: str) -> bytes:
    request = urllib.request.Request(url, headers={"User-Agent": USER_AGENT})
    with urllib.request.urlopen(request, timeout=25) as response:
        return response.read()


def text_of(node: ET.Element, name: str, default: str = "") -> str:
    child = node.find(name)
    return (child.text or "").strip() if child is not None else default


def clean_description(value: str, limit: int = 150) -> str:
    value = re.sub(r"<br\s*/?>", " ", value, flags=re.IGNORECASE)
    value = re.sub(r"<[^>]+>", "", value)
    value = html.unescape(value)
    value = re.sub(r"\s+", " ", value).strip()
    value = re.sub(r"続きをみる\s*$", "", value).strip()
    return value if len(value) <= limit else value[: limit - 1].rstrip() + "…"


def iso_date(value: str) -> str:
    try:
        parsed = parsedate_to_datetime(value)
    except (TypeError, ValueError, OverflowError):
        parsed = datetime.fromisoformat(value)
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.isoformat()


def safe_source_url(value: str, hosts: tuple[str, ...]) -> str:
    parsed = urlparse(value)
    if parsed.scheme != "https" or parsed.hostname not in hosts:
        return ""
    return value


def parse_note(payload: bytes) -> list[dict[str, str]]:
    root = ET.fromstring(payload)
    namespace = {"media": "http://search.yahoo.com/mrss/"}
    items: list[dict[str, str]] = []
    for node in root.findall("./channel/item")[:MAX_ITEMS_PER_SOURCE]:
        url = safe_source_url(text_of(node, "link"), ("note.com",))
        if not url:
            continue
        thumbnail_node = node.find("media:thumbnail", namespace)
        thumbnail = (thumbnail_node.text or "").strip() if thumbnail_node is not None else ""
        items.append({
            "source": "note",
            "title": text_of(node, "title"),
            "url": url,
            "published": iso_date(text_of(node, "pubDate")),
            "description": clean_description(text_of(node, "description")),
            "image": safe_source_url(thumbnail, ("assets.st-note.com",)),
        })
    return items


def prtimes_og_image(url: str) -> str:
    try:
        page = fetch(url).decode("utf-8", errors="replace")
    except Exception as error:  # 画像だけ取得できない場合も記事自体は掲載する
        print(f"warning: PR TIMES image fetch failed: {error}")
        return ""
    match = re.search(
        r'<meta[^>]+property=["\']og:image["\'][^>]+content=["\']([^"\']+)',
        page,
        flags=re.IGNORECASE,
    )
    if not match:
        match = re.search(
            r'<meta[^>]+content=["\']([^"\']+)["\'][^>]+property=["\']og:image["\']',
            page,
            flags=re.IGNORECASE,
        )
    if not match:
        return ""
    image = html.unescape(match.group(1))
    return safe_source_url(image, ("prcdn.freetls.fastly.net", "prtimes.jp"))


def parse_prtimes(payload: bytes) -> list[dict[str, str]]:
    root = ET.fromstring(payload)
    ns = {
        "rss": "http://purl.org/rss/1.0/",
        "dc": "http://purl.org/dc/elements/1.1/",
    }
    items: list[dict[str, str]] = []
    for node in root.findall("rss:item", ns)[:MAX_ITEMS_PER_SOURCE]:
        url = safe_source_url(text_of(node, "{http://purl.org/rss/1.0/}link"), ("prtimes.jp",))
        if not url:
            continue
        items.append({
            "source": "prtimes",
            "title": text_of(node, "{http://purl.org/rss/1.0/}title"),
            "url": url,
            "published": iso_date(text_of(node, "{http://purl.org/dc/elements/1.1/}date")),
            "description": clean_description(text_of(node, "{http://purl.org/rss/1.0/}description")),
            "image": prtimes_og_image(url),
        })
    return items


def read_previous() -> dict:
    try:
        return json.loads(OUTPUT.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError):
        return {"items": []}


def main() -> None:
    previous = read_previous()
    collected: list[dict[str, str]] = []
    errors: list[str] = []

    for name, url, parser in (
        ("note", NOTE_RSS, parse_note),
        ("PR TIMES", PRTIMES_RSS, parse_prtimes),
    ):
        try:
            collected.extend(parser(fetch(url)))
        except Exception as error:
            errors.append(f"{name}: {error}")
            collected.extend(item for item in previous.get("items", []) if item.get("source") == name.lower().replace(" ", ""))

    if not collected:
        raise RuntimeError("No news items could be fetched: " + "; ".join(errors))

    unique: dict[str, dict[str, str]] = {}
    for item in collected:
        if item.get("title") and item.get("url") and item.get("published"):
            unique[item["url"]] = item
    items = sorted(unique.values(), key=lambda item: item["published"], reverse=True)
    if items == previous.get("items", []):
        print(f"no changes: {len(items)} items")
        for error in errors:
            print(f"warning: {error}")
        return

    result = {
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "sources": {"note": NOTE_RSS, "prtimes": PRTIMES_RSS},
        "items": items,
    }

    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    with tempfile.NamedTemporaryFile("w", encoding="utf-8", dir=OUTPUT.parent, delete=False) as temp:
        json.dump(result, temp, ensure_ascii=False, indent=2)
        temp.write("\n")
        temp_path = temp.name
    os.replace(temp_path, OUTPUT)

    print(f"updated {OUTPUT.relative_to(ROOT)}: {len(items)} items")
    for error in errors:
        print(f"warning: {error}")


if __name__ == "__main__":
    main()
