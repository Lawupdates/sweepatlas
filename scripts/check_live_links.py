#!/usr/bin/env python3
"""Concurrent link-health checks. Reachability is not entry-form verification."""
import concurrent.futures
import datetime
import json
import re
import urllib.error
import urllib.request
from pathlib import Path
from urllib.parse import urlsplit

ROOT = Path(__file__).resolve().parents[1]
SOURCE = ROOT / "data/sweepstakes.json"
DEST = ROOT / "data/feed-status.json"
records = json.loads(SOURCE.read_text(encoding="utf-8"))
now = datetime.datetime.now(datetime.timezone.utc)
today = now.date().isoformat()
USER_AGENT = "Mozilla/5.0 (compatible; SweepsTitanLinkHealth/2.0)"
RULE_PATH = re.compile(r"/(?:official-rules|rules|terms|conditions|faq)(?:/|$|[?#])", re.I)

def inspect(url):
    try:
        req = urllib.request.Request(url, headers={"User-Agent": USER_AGENT, "Accept": "text/html,application/xhtml+xml"})
        with urllib.request.urlopen(req, timeout=10) as response:
            final = response.geturl()
            body = response.read(90000).decode("utf-8", "ignore")
            title = re.search(r"<title[^>]*>(.*?)</title>", body, re.I | re.S)
            title = re.sub(r"\s+", " ", title.group(1)).strip()[:120] if title else ""
            return {"http_status": response.status, "reachable": 200 <= response.status < 400,
                    "final_url": final, "title": title}
    except urllib.error.HTTPError as error:
        return {"http_status": error.code, "reachable": False, "error": "http_error"}
    except Exception as error:
        return {"http_status": None, "reachable": False, "error": type(error).__name__}

urls = sorted({item[field] for item in records for field in ("entryUrl", "rulesUrl") if item.get(field)})
with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
    checked = dict(zip(urls, pool.map(inspect, urls)))

results = []
for item in records:
    entry, rules = item.get("entryUrl", ""), item.get("rulesUrl", "")
    flags = []
    if entry == rules:
        flags.append("entry_and_rules_same_url_review")
    if RULE_PATH.search(urlsplit(entry).path):
        flags.append("entry_url_looks_like_rules")
    if urlsplit(entry).path in ("", "/"):
        flags.append("entry_is_homepage_review")
    if entry and not entry.startswith("https://"):
        flags.append("entry_insecure")
    if rules and not rules.startswith("https://"):
        flags.append("rules_insecure")
    checks = []
    for field, url in (("entryUrl", entry), ("rulesUrl", rules)):
        response = checked.get(url, {"http_status": None, "reachable": False, "error": "missing_url"})
        check = {"type": field, **response}
        checks.append(check)
        code = response.get("http_status")
        if code in (404, 410):
            flags.append(field + "_not_found")
        elif code in (401, 403, 429) or code is None:
            flags.append(field + "_unconfirmed_or_blocked")
        final = response.get("final_url") or ""
        if field == "entryUrl" and final:
            if RULE_PATH.search(urlsplit(final).path):
                flags.append("entry_redirects_to_rules")
            if urlsplit(final).path in ("", "/"):
                flags.append("entry_redirects_to_homepage")
        title = response.get("title", "")
        if field == "entryUrl" and re.search(r"official rules|privacy policy|terms and conditions", title, re.I):
            flags.append("entry_title_looks_like_rules")
    results.append({"id": item["id"], "expires": item["endDate"],
                    "expired": item["endDate"] < today, "checks": checks,
                    "flags": sorted(set(flags)), "verified_entry_form": False})

report = {
    "checked_at": now.isoformat(), "records": len(records),
    "unique_urls": len(urls),
    "active_records": sum(not x["expired"] for x in results),
    "flagged_records": sum(bool(x["flags"]) for x in results),
    "results": results,
    "disclaimer": "Automated URL checks do not verify that an actual contest entry form or the correct official rules are present. HTTP 403 may be bot blocking, not a dead link."
}
DEST.parent.mkdir(parents=True, exist_ok=True)
DEST.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(f"Checked {len(records)} records / {len(urls)} unique URLs; flagged {report['flagged_records']}; active {report['active_records']}")
