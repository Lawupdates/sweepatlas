#!/usr/bin/env python3
"""Check published sponsor links and expiration without claiming legal/rules verification."""
import json,datetime,urllib.request,urllib.error
from pathlib import Path
SOURCE=Path("data/sweepstakes.json")
DEST=Path("data/feed-status.json")
records=json.loads(SOURCE.read_text(encoding="utf-8"))
now=datetime.datetime.now(datetime.timezone.utc)
today=now.date().isoformat()
results=[]
for item in records:
    status={"id":item["id"],"expires":item["endDate"],"expired":item["endDate"]<today,"checks":[]}
    for field in ("entryUrl","rulesUrl"):
        url=item[field]
        req=urllib.request.Request(url,headers={"User-Agent":"SweepAtlasLinkHealth/1.0 (+https://github.com/Lawupdates/sweepatlas)"})
        try:
            with urllib.request.urlopen(req,timeout=12) as response:
                status["checks"].append({"type":field,"http_status":response.status,"reachable":200<=response.status<400})
        except urllib.error.HTTPError as e:
            status["checks"].append({"type":field,"http_status":e.code,"reachable":False})
        except Exception as e:
            status["checks"].append({"type":field,"http_status":None,"reachable":False,"error":str(e)[:100]})
    results.append(status)
report={"checked_at":now.isoformat(),"records":len(records),"active_records":sum(not x["expired"] for x in results),"results":results,"disclaimer":"Connectivity checks are automated; a successful HTTP response does not verify legal eligibility or rules."}
DEST.write_text(json.dumps(report,indent=2)+"\n",encoding="utf-8")
print("Checked",len(records),"records; active",report["active_records"])
