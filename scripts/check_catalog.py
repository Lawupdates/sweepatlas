#!/usr/bin/env python3
"""Validate curated public directory; fail closed on suspicious entries."""
import json, re, sys, datetime
from pathlib import Path
from urllib.parse import urlsplit
p=Path(__file__).resolve().parents[1]/"data"/"sweepstakes.json"
try:
    data=json.loads(p.read_text(encoding="utf-8"))
    assert isinstance(data,list),"Catalog must be an array"
    seen=set()
    for i,entry in enumerate(data):
        assert isinstance(entry,dict),f"Record {i} must be an object"
        for k in ("id","name","sponsor","desc","category","cadence","place","endDate","reviewedAt","entryUrl","rulesUrl"):
            assert isinstance(entry.get(k),str) and entry[k].strip(),f"Record {i}: missing {k}"
        assert re.fullmatch(r"[a-z0-9-]{3,80}",entry["id"]),f"Record {i}: bad ID"
        assert entry["id"] not in seen, f"Duplicate ID {entry['id']}"
        seen.add(entry["id"])
        assert entry["cadence"] in {"Daily","Weekly","Monthly","One-time","See rules","Up to 10 total"}, f"Record {i}: invalid cadence"
        assert len(entry["place"]) <= 120, f"Record {i}: unreasonable eligibility region"
        assert isinstance(entry.get("value"),(int,float)) and 0<=entry["value"]<=10**12
        for k in ("entryUrl","rulesUrl"):
            u=urlsplit(entry[k])
            assert u.scheme=="https" and bool(u.netloc) and not u.username and not u.password, f"Record {i}: unsafe {k}"
        for k in ("endDate","reviewedAt"):
            assert datetime.date.fromisoformat(entry[k]).isoformat()==entry[k]
    print(f"VALID: {len(data)} curated sweepstakes")
except Exception as e:
    print(f"INVALID CATALOG: {e}",file=sys.stderr)
    sys.exit(1)
