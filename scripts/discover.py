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
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import quote, urlsplit, urljoin

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
    f'"home makeover" sweepstakes {YEAR}',
    f'"vacation giveaway" official rules {YEAR}',
    f'"trip for two" sweepstakes {YEAR}',
    f'"win a car" official rules {YEAR}',
    f'"win a truck" sweepstakes {YEAR}',
    f'"win a camper" giveaway {YEAR}',
    f'"win an RV" sweepstakes {YEAR}',
    f'"win a motorcycle" sweepstakes {YEAR}',
    f'"win a boat" giveaway {YEAR}',
    f'"win a cruise" official rules {YEAR}',
    f'"win a laptop" sweepstakes {YEAR}',
    f'"win a phone" official rules {YEAR}',
    f'"gaming giveaway" official rules {YEAR}',
    f'"sports tickets" sweepstakes {YEAR}',
    f'"concert tickets" sweepstakes {YEAR}',
    f'"cash giveaway" "no purchase necessary" {YEAR}',
    f'"daily sweepstakes" enter {YEAR}',
    f'"monthly sweepstakes" enter {YEAR}',
    f'"weekly giveaway" official rules {YEAR}',
    f'"instant win" game official rules {YEAR}',
    f'"grand prize" contest rules {YEAR}',
    f'"gift basket" sweepstakes {YEAR}',
    f'"shopping spree" official rules {YEAR}',
    f'"home appliances" giveaway {YEAR}',
    f'"kitchen makeover" sweepstakes {YEAR}',
    f'"beauty giveaway" official rules {YEAR}',
    f'"pet giveaway" official rules {YEAR}',
    f'"outdoor gear" sweepstakes {YEAR}',
    f'"national sweepstakes" official rules {YEAR}',
    f'"Arizona sweepstakes" official rules {YEAR}',
    f'site:hgtv.com/sweepstakes "enter" {YEAR}',
    f'site:hgtv.com/sweepstakes "giveaway" {YEAR}',
    f'site:tlc.com/giveaways "giveaway" {YEAR}',
    f'site:tlc.com/sweepstakes "enter" {YEAR}',
    f'site:foodnetwork.com/features/articles/sweepstakes-and-contests {YEAR}',
    f'site:foodnetwork.com/sponsored/sweepstakes "enter" {YEAR}',
    f'site:food.com "sweepstakes" {YEAR}',
    f'site:travelchannel.com/sweepstakes {YEAR}',
    f'site:hallmarkchannel.com/sweepstakes {YEAR}',
    f'site:foodnetwork.com "sweepstakes" {YEAR}',
    f'site:hgtv.com "sweepstakes" {YEAR}',
    f'site:travelchannel.com "sweepstakes" {YEAR}',
    f'site:mlb.com "sweepstakes" {YEAR}',
    f'site:nfl.com "sweepstakes" {YEAR}',
    f'site:nhl.com "sweepstakes" {YEAR}',
    f'site:espn.com "sweepstakes" {YEAR}',
    f'site:goodhousekeeping.com "sweepstakes" {YEAR}',
    f'site:countryliving.com "sweepstakes" {YEAR}',
    f'site:hearst.com "sweepstakes" {YEAR}',
]
CAP = 2500  # Retain older research leads while new titles are discovered; do not silently drop backlog.
DATE_PATTERN = re.compile(r'(?:ends?|expires?|expiration date|deadline|closes?)\s*(?:on|at|:)?\s*(?P<date>(?:January|February|March|April|May|June|July|August|September|October|November|December|Jan|Feb|Mar|Apr|Jun|Jul|Aug|Sep|Oct|Nov|Dec)\.?\s+\d{1,2},?\s+20\d{2}|\d{1,2}/\d{1,2}/20\d{2}|20\d{2}-\d{2}-\d{2})', re.I)
def extract_end_date(text):
    match = DATE_PATTERN.search(text or "")
    if not match:
        return None
    raw = match.group("date").replace(".", "")
    for fmt in ("%B %d, %Y", "%B %d %Y", "%b %d, %Y", "%b %d %Y", "%m/%d/%Y", "%Y-%m-%d"):
        try:
            d = datetime.datetime.strptime(raw, fmt).date()
            return d.isoformat() if YEAR-1 <= d.year <= YEAR+2 else None
        except ValueError:
            pass
    return None

VALUE_PATTERN = re.compile(r'(?i)(?:approx(?:imate)?(?: retail)? value|(?:total )?prize value|(?:grand )?prize|worth|valued at|win|for a chance to win)\s*(?:of|is|:|-)?\s*\$\s*([0-9][0-9,]*(?:\.[0-9]{1,2})?)')
def extract_prize_value(text):
    values=[]
    for m in VALUE_PATTERN.finditer(text or ""):
        try:
            amount=float(m.group(1).replace(",",""))
            if 1<=amount<=100000000:values.append(amount)
        except ValueError:pass
    return max(values) if values else None

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
def fetch_public_end_date(url):
    # Only direct public HTTPS pages are eligible; no bypasses or logins.
    host = (urlsplit(url).hostname or "").lower()
    if host == "news.google.com" or host.endswith(".google.com"):
        return None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SweepAtlas/1.1"})
        with urllib.request.urlopen(req, timeout=5) as response:
            if response.status != 200 or "text/html" not in response.headers.get("Content-Type", ""):
                return None
            raw = response.read(150000).decode("utf-8", "replace")
        raw = re.sub(r"<(?:script|style)\\b[^>]*>.*?</(?:script|style)>", " ", raw, flags=re.I|re.S)
        return extract_end_date(clean(raw) + " " + unescape(re.sub(r"<[^>]+>", " ", raw))[:80000])
    except (OSError, ValueError, UnicodeError):
        return None

class EntryPageParser(HTMLParser):
    def __init__(self):
        super().__init__()
        self.form = False
        self.links = []
        self.current = None
    def handle_starttag(self, tag, attrs):
        attrs = dict(attrs)
        if tag == "form":
            self.form = True
        if tag == "a" and attrs.get("href"):
            self.current = [attrs["href"], ""]
        if tag == "input" and attrs.get("type", "").lower() in ("email", "text") and self.form:
            self.form = True
    def handle_data(self, data):
        if self.current:
            self.current[1] += data
    def handle_endtag(self, tag):
        if tag == "a" and self.current:
            self.links.append(tuple(self.current))
            self.current = None

def locate_entry_form(url):
    """Conservative: only return clearly labeled entry links on public HTTPS pages."""
    host = (urlsplit(url).hostname or "").lower()
    if host == "news.google.com" or host.endswith(".google.com"):
        return None
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SweepAtlas/1.1 public entry discovery"})
        with urllib.request.urlopen(req, timeout=6) as response:
            if response.status != 200 or "text/html" not in response.headers.get("Content-Type", ""):
                return None
            landing = response.geturl()
            body = response.read(180000).decode("utf-8", "replace")
        p = EntryPageParser()
        p.feed(body)
        for href, label in p.links:
            if re.search(r"\b(enter (now|here|sweepstakes|giveaway)|entry form|submit entry|enter to win)\b", label, re.I):
                entry = urljoin(landing, href)
                if valid(entry) and urlsplit(entry).hostname == urlsplit(landing).hostname:
                    return entry
    except (OSError, ValueError, UnicodeError):
        return None
    return None
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
            for item in feed.findall("./channel/item")[:80]:
                title = clean(item.findtext("title"))
                link = (item.findtext("link") or "").strip()
                if not title or not valid(link):
                    continue
                if link in existing:
                    # Preserve historical records but recover a real RSS headline when
                    # a prior migration replaced it with a generic numbered label.
                    saved = existing[link]
                    if saved.get("title", "").startswith("Sweepstakes source "):
                        saved["title"] = title
                        saved["query"] = term
                        saved["published"] = clean(item.findtext("pubDate"))
                        saved["end_date"] = saved.get("end_date") or extract_end_date(title + " " + clean(item.findtext("description")))
                        saved["prize_value_candidate"] = saved.get("prize_value_candidate") or extract_prize_value(title + " " + clean(item.findtext("description")))
                    continue
                found += 1
                existing[link] = {
                    "id": hashlib.sha256(link.encode()).hexdigest()[:16],
                    "title": title,
                    "url": link,
                    "query": term,
                    "published": clean(item.findtext("pubDate")),
                    "end_date": extract_end_date(title + " " + clean(item.findtext("description"))),
                    "prize_value_candidate": extract_prize_value(title + " " + clean(item.findtext("description"))),
                    "prize_value_status": "unverified_search_excerpt",
                    "first_seen_utc": now,
                    "status": "UNVERIFIED - official sponsor rules review required",
                }
        except Exception as exc:
            errors.append({"query": term, "error": str(exc)[:180]})
    queue = sorted(existing.values(), key=lambda r: r.get("first_seen_utc", ""), reverse=True)[:CAP]
    for item in queue:
        if item.get("prize_value_candidate") is None:
            amount=extract_prize_value(item.get("title","")+" "+item.get("description",""))
            if amount is not None:
                item["prize_value_candidate"]=amount
                item["prize_value_status"]="unverified_search_excerpt"
        if not item.get("end_date"):
            item["end_date"] = extract_end_date(item.get("title", ""))
    checked_pages = 0
    for item in queue:
        if item.get("end_date") or checked_pages >= 30:
            continue
        host = (urlsplit(item["url"]).hostname or "").lower()
        if host != "news.google.com" and not host.endswith(".google.com"):
            checked_pages += 1
            item["end_date"] = fetch_public_end_date(item["url"])
    # Candidates are never automatically confirmed as working entry forms.
    # Every candidate requires manual form submission testing before being marked confirmed.
    # A reachable article is not an entry form; no automated verification claim is made.
    forms_checked = 0
    for item in queue:
        if item.get("entry_url"):
            if not valid(item["entry_url"]):
                item.pop("entry_url", None)
                item.pop("entry_source", None)
            else:
                item["entry_check_status"] = "needs_manual_form_confirmation"
        if item.get("entry_url") or forms_checked >= 100:
            continue
        host = (urlsplit(item["url"]).hostname or "").lower()
        if host != "news.google.com" and not host.endswith(".google.com"):
            forms_checked += 1
            found_entry = locate_entry_form(item["url"])
            if found_entry:
                item["entry_url"] = found_entry
                item["entry_source"] = "public_page_entry_link"
                item["entry_check_status"] = "needs_manual_form_confirmation"
    dates_found = sum(bool(item.get("end_date")) for item in queue)
    report = {
        "generated_utc": now,
        "warning": "Research leads only; search stories are not official entry pages. Verify sponsor, rules, eligibility, frequency, end date, and free entry before publication.",
        "new_candidates": found,
        "expiration_dates_found": dates_found,
        "entry_links_found": sum(bool(item.get("entry_url")) for item in queue),
        "candidates": queue,
        "feed_errors": errors,
    }
    DEST.write_text(json.dumps(report, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    print(f"Discovered {found} new leads; retained {len(queue)}; feed errors {len(errors)}")
    if len(errors) == len(TERMS) and not queue:
        raise SystemExit("All feeds failed and no prior candidate queue exists")
if __name__ == "__main__":
    main()
