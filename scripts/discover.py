#!/usr/bin/env python3
"""Discover candidate sweepstakes for manual rules review, never automatic publication.

Uses Google News RSS search feeds as a research source. Feed availability is
best-effort. The rolling queue retains previously found leads when feeds fail.
"""
import datetime
import hashlib
import json
import os
import re
import urllib.request
import xml.etree.ElementTree as ET
from html import unescape
from pathlib import Path
from urllib.parse import quote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
DEST = Path(os.environ.get("SWEEPATLAS_REPORT", str(ROOT / "data/discovery-candidates.json")))
YEAR = datetime.datetime.now(datetime.timezone.utc).year
TERMS = [
    f'sweepstakes "official rules" {YEAR}',
    f'giveaway "no purchase necessary" {YEAR}',
    f'"daily entry" sweepstakes {YEAR}',
    f'"weekly" sweepstakes official rules {YEAR}',
    f'"travel sweepstakes" {YEAR}',
    f'"cash prize" sweepstakes {YEAR}',
    f'"vehicle sweepstakes" {YEAR}',
    f'"gift card" sweepstakes {YEAR}',
    f'"electronics giveaway" official rules {YEAR}',
    f'"holiday sweepstakes" {YEAR}',
    f'site:hallmarkchannel.com sweepstakes {YEAR}',
    f'site:foodnetwork.com sweepstakes {YEAR}',
    f'site:filson.com giveaway {YEAR}',
    f'site:chipotle.com giveaway {YEAR}',
]
CAP = 700
def clean(value):
    return re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", unescape(value or ""))).strip()[:350]
def source(term):
    # Public RSS search feed; no restricted login, cookies or scraping of competitors.
    query = quote(term)
    url = f"https://news.google.com/rss/search?q={query}&hl=en-US&gl=US&ceid=US:en"
    req = urllib.request.Request(url, headers={"User-Agent": "SweepAtlas/1.1 public-RSS research"})
    with urllib.request.urlopen(req, timeout=18) as response:
        if response.status != 200:
            raise ValueError("Unexpected feed response")
        return response.read(1500000)
def valid(url):
    try:
        p = urlsplit(url)
        return p.scheme == "https" and bool(p.netloc) and not p.username and not p.password
    except ValueError:
        return False
def main():
    DEST.parent.mkdir(parents=True, exist_ok=True)
    existing = {}
    if DEST.exists():
        try:
            old = json.loads(DEST.read_text(encoding="utf-8"))
            for item in old.get("candidates", []):
                if isinstance(item, dict) and valid(item.get("url", "")):
                    existing[item["url"]] = item
        except (OSError, ValueError, TypeError):
            pass
    errors = []
    found = 0
    now = datetime.datetime.now(datetime.timezone.utc).isoformat()
    for term in TERMS:
        try:
            feed = ET.fromstring(source(term))
            for item in feed.findall("./channel/item")[:50]:
                title = clean(item.findtext("title"))
                link = (item.findtext("link") or "").strip()
                if not title or not valid(link):
                    continue
                if link in existing:
                    continue
                found += 1
                existing[link] = {
                    "id": hashlib.sha256(link.encode()).hexdigest()[:16],
                    "title": title,
                    "url": link,
                    "query": term,
                    "published": clean(item.findtext("pubDate")),
                    "first_seen_utc": now,
                    "status": "UNVERIFIED - official sponsor rules review required",
                }
        except Exception as exc:
            errors.append({"query": term, "error": str(exc)[:180]})
    queue = sorted(existing.values(), key=lambda r: r.get("first_seen_utc", ""), reverse=True)[:CAP]
    report = {
        "generated_utc": now,
        "warning": "Research leads only; search stories are not official entry pages. Verify sponsor, rules, eligibility, frequency, end date, and free entry before publication.",
        "new_candidates": found,
        "candidates": queue,
        "feed_errors": errors,
    }
    DEST.write_text(json.dumps(report, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(f"Discovered {found} new leads; retained {len(queue)}; feed errors {len(errors)}")
    if len(errors) == len(TERMS) and not queue:
        raise SystemExit("All feeds failed and no prior candidate queue exists")
if __name__ == "__main__":
    main()
