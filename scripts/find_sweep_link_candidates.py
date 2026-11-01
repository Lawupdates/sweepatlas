#!/usr/bin/env python3
"""Find possible replacement entry/rules pages for flagged contests.

Candidates are research leads, never auto-published or called verified.
"""
import concurrent.futures
import json
import pathlib
import re
import urllib.parse
import urllib.request
import xml.etree.ElementTree as ET

ROOT = pathlib.Path(__file__).resolve().parents[1]
AUDIT = ROOT / "audit-results/link-audit.json"
OUT = ROOT / "audit-results/link-candidates.json"
records = json.loads((ROOT / "data/sweepstakes.json").read_text(encoding="utf-8"))
by_id = {record["id"]: record for record in records}
audit = json.loads(AUDIT.read_text(encoding="utf-8"))
REVIEW = ("entry_url_looks_like_rules", "entry_is_rules_not_entry",
          "entry_is_generic_homepage", "entry_redirects_to_homepage",
          "entry_redirects_to_rules", "entry_page_title_looks_like_rules",
          "entry_and_rules_identical_review_manually", "entry_and_rules_same_destination",
          "entry_http_error", "entry_page_unavailable_or_expired",
          "rules_request_failed", "entry_request_failed")

def search(record, kind):
    name = record.get("name", "").strip()
    sponsor = record.get("sponsor", "").strip()
    phrase = "sweepstakes enter form no purchase" if kind == "entry" else "sweepstakes official rules"
    query = f'"{name}" {sponsor} {phrase}'
    url = "https://www.bing.com/search?" + urllib.parse.urlencode({"q": query, "format": "rss"})
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "Mozilla/5.0 (compatible; SweepsTitanResearch/1.0)"})
        with urllib.request.urlopen(req, timeout=12) as response:
            root = ET.fromstring(response.read(150000))
        matches = []
        for item in root.findall(".//item"):
            link = (item.findtext("link") or "").strip()
            title = re.sub(r"\\s+", " ", item.findtext("title") or "").strip()
            parsed = urllib.parse.urlsplit(link)
            if parsed.scheme != "https" or not parsed.netloc or parsed.username or parsed.password:
                continue
            if parsed.netloc.endswith(("bing.com", "google.com")):
                continue
            if link not in {match["url"] for match in matches}:
                matches.append({"title": title[:160], "url": link})
            if len(matches) >= 5:
                break
        return matches
    except Exception:
        return []

targets = []
for row in audit.get("results", []):
    if any(flag in REVIEW for flag in row.get("flags", [])):
        record = by_id.get(row["id"])
        if record:
            targets.append(record)

jobs = [(record, kind) for record in targets for kind in ("entry", "rules")]
with concurrent.futures.ThreadPoolExecutor(max_workers=8) as pool:
    found = list(pool.map(lambda job: search(*job), jobs))
result = {}
for (record, kind), candidates in zip(jobs, found):
    result.setdefault(record["id"], {"name": record["name"], "sponsor": record.get("sponsor", ""),
                                    "current_entry": record.get("entryUrl", ""),
                                    "current_rules": record.get("rulesUrl", ""),
                                    "candidate_entry": [], "candidate_rules": [],
                                    "status": "REVIEW_REQUIRED"})
    result[record["id"]]["candidate_" + kind] = candidates
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps({"records_scanned": len(records), "flagged_researched": len(targets),
                           "candidate_records": sum(bool(r["candidate_entry"] or r["candidate_rules"]) for r in result.values()),
                           "warning": "Search results are NOT verified contest entry forms or rules. Confirm sponsor, exact promotion, eligibility, dates and destination before replacing.",
                           "results": result}, indent=2) + "\n", encoding="utf-8")
print(f"Researched {len(targets)} flagged contests; candidate URLs found for {sum(bool(r['candidate_entry'] or r['candidate_rules']) for r in result.values())}.")
