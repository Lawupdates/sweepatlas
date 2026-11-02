#!/usr/bin/env python3
"""Read-only Sweeps Titan release inventory; report evidence, never certify functionality."""
import json
import re
from datetime import datetime, timezone
from pathlib import Path

root = Path(__file__).resolve().parents[1]
page_names = ["index.html","entry-desk.html","radar.html","advertise.html",
              "advertising-rates.html","shop.html","get-started.html"]
pages = {}
for name in page_names:
    file = root / name
    if not file.exists():
        pages[name] = {"exists": False}
        continue
    body = file.read_text(encoding="utf-8", errors="replace")
    # Storage key and repository URLs are legacy internals, not public labels.
    text_only = re.sub(r"<script\\b[^>]*>.*?</script>|<style\\b[^>]*>.*?</style>",
                       "", body, flags=re.I|re.S)
    pages[name] = {
        "exists": True, "bytes":file.stat().st_size,
        "visible_old_brand_mentions":len(re.findall(r"(?i)sweep\\s*atlas",text_only)),
        "visible_titan_mentions":len(re.findall(r"(?i)sweeps titan",text_only)),
        "images":len(re.findall(r"<img\\b",body,re.I)),
        "external_scripts":len(re.findall(r"<script\\b[^>]*src=",body,re.I)),
    }
catalog = json.loads((root/"data/sweepstakes.json").read_text(encoding="utf-8"))
ids = [x.get("id") for x in catalog]
entry_links = [x.get("entryUrl","") for x in catalog]
rules_links = [x.get("rulesUrl","") for x in catalog]
report = {
    "generatedAt":datetime.now(timezone.utc).isoformat(),
    "note":"Static inventory only. Cannot verify browser UI, payment processing, real-world contest entry, or production domain.",
    "pages":pages,
    "catalog":{
        "records":len(catalog),"target":1500,"remaining_to_target":max(0,1500-len(catalog)),
        "duplicate_ids":len(ids)-len(set(ids)),
        "entry_equals_rules":sum(a==b for a,b in zip(entry_links,rules_links)),
        "missing_https_entry":sum(not a.startswith("https://") for a in entry_links),
        "missing_https_rules":sum(not a.startswith("https://") for a in rules_links),
    },
    "release_status":"NOT_CERTIFIED",
}
out = root/"data/titan-release-audit.json"
out.write_text(json.dumps(report,indent=2)+"\\n",encoding="utf-8")
print(json.dumps({"release_status":"NOT_CERTIFIED","catalog":report["catalog"],"pages":pages},indent=2))
