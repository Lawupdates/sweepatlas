#!/usr/bin/env python3
"""Sweeps Titan public discovery, vetting and repair queue.
Does not bypass robots.txt, CAPTCHAs, access controls, or submit entries.
Automated HTTP checks cannot prove that an entry form accepts submissions.
"""
import argparse
import concurrent.futures
import datetime as dt
import email.utils
import hashlib
import html
import json
import os
import re
import socket
import time
import urllib.error
import urllib.parse
import urllib.request
import urllib.robotparser
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CATALOG = ROOT / "data" / "sweepstakes.json"
REPORT = ROOT / "data" / "vetting"
UA = "SweepsTitanPublicVetting/1.0 (+https://sweepstitan.com/help.html)"
TIMEOUT = 12
MAX_BYTES = 350000
RULE_PATTERN = re.compile(r"\b(official rules|no purchase necessary|eligib(?:le|ility)|sweepstakes|giveaway|contest|enter to win)\b", re.I)
ENTRY_PATTERN = re.compile(r"\b(submit entry|enter now|enter giveaway|entry form|enter sweepstakes|enter to win|gleam.io|sweepwidget|rafflecopter|woobox)\b", re.I)
ERROR_PATTERN = re.compile(r"\b(page not found|404 not found|contest has ended|sweepstakes closed|promotion has ended|giveaway has ended)\b", re.I)
SOURCES = [
    # Third-party directories are discovery clues only. Never copy their prose.
    "https://www.sweepstakesadvantage.com/",
    "https://www.contestgirl.com/",
    "https://www.sweepsatlas.com/",
    "https://www.sweetiessweeps.com/",
    "https://www.online-sweepstakes.com/",
    "https://www.thefreebieblogger.com/",
]
SEARCHES = [
    "site:gleam.io giveaway 2026 enter",
    "site:sweepwidget.com giveaways 2026",
    "site:woobox.com sweepstakes 2026",
    "official sweepstakes November 2026 enter",
    "no purchase necessary sweepstakes 2026 official rules",
]
robot_cache = {}
def allowed(url):
    p = urllib.parse.urlsplit(url)
    if p.scheme != "https" or not p.netloc or p.username or p.password:
        return False, "invalid_https_url"
    host = (p.hostname or "").lower()
    if host in {"localhost", "127.0.0.1", "::1"} or host.endswith((".local", ".internal")):
        return False, "unsafe_host"
    try:
        # No network calls to private IP addresses. DNS-rebinding protection also
        # requires network-layer outbound restrictions in the runner.
        import ipaddress
        ip = ipaddress.ip_address(host)
        if not ip.is_global: return False, "unsafe_address"
    except ValueError: pass
    origin = p.scheme + "://" + p.netloc
    if origin not in robot_cache:
        rp = urllib.robotparser.RobotFileParser()
        rp.set_url(origin + "/robots.txt")
        try: rp.read(); robot_cache[origin] = rp
        except Exception: return False, "robots_unavailable"
    if not robot_cache[origin].can_fetch(UA, url): return False, "robots_disallow"
    return True, ""
def fetch(url):
    ok, reason = allowed(url)
    if not ok: return {"status": "blocked", "reason": reason, "url": url}
    req = urllib.request.Request(url, headers={"User-Agent": UA, "Accept":"text/html,application/xhtml+xml"})
    try:
        with urllib.request.urlopen(req, timeout=TIMEOUT) as r:
            final = r.geturl()
            ok, reason = allowed(final)
            if not ok: return {"status":"blocked", "reason": "redirect_"+reason, "url":url}
            status=r.status
            typ=r.headers.get("Content-Type","")
            data=r.read(MAX_BYTES)
            text=data.decode("utf-8","ignore") if "html" in typ or "text" in typ else ""
            clean=re.sub(r"<(?:script|style)\b[^>]*>.*?</(?:script|style)>"," ",text,flags=re.I|re.S)
            clean=html.unescape(re.sub(r"<[^>]+>", " ", clean))
            return {"status":"reachable" if status<400 else "http_error","httpStatus":status,
                    "finalUrl":final,"contentType":typ,"sample":clean[:70000],"html":text[:MAX_BYTES]}
    except urllib.error.HTTPError as e:
        return {"status":"http_error","httpStatus":e.code,"reason":str(e)}
    except Exception as e:
        return {"status":"unreachable","reason":str(e)[:130]}
def inspect(item):
    url=item.get("entryUrl","")
    result=fetch(url)
    status=result["status"]
    content=result.get("sample","")
    if status=="reachable" and ERROR_PATTERN.search(content[:10000]): status="possible_closed"
    if status=="reachable" and not RULE_PATTERN.search(content): status="unclear_promotion"
    if status=="reachable" and RULE_PATTERN.search(content):
        status="promotion_page_found" if ENTRY_PATTERN.search(content) else "rules_or_promotion_found"
    if status=="reachable" and "entry" in url.lower(): status="promotion_page_found"
    return {"id":item["id"],"name":item.get("name",""),"entryUrl":url,"status":status,
       "httpStatus":result.get("httpStatus"),"finalUrl":result.get("finalUrl"),
       "checkedAt":dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
       "formSubmissionTested":False,"reason":result.get("reason",""),
       "needsHumanReview": status not in ("promotion_page_found","rules_or_promotion_found"),
       "warning":"Page access is not proof of successful contest entry"}
def discoveries():
    # Search engine RSS is an index of possible leads, not a source of validated prizes.
    leads=[]
    for query in SEARCHES:
        rss="https://www.bing.com/search?format=rss&q="+urllib.parse.quote(query)
        resp=fetch(rss)
        if resp.get("status") not in ("reachable","unclear_promotion","promotion_page_found","rules_or_promotion_found"): continue
        try:
            root=ET.fromstring(resp.get("html",""))
            for elem in root.findall(".//item")[:20]:
                title=(elem.findtext("title") or "").strip()
                link=(elem.findtext("link") or "").strip()
                if not title or not link.startswith("https://"): continue
                host=urllib.parse.urlsplit(link).hostname or ""
                if any(z in host for z in ("bing.com","google.com","sweepsatlas.com")): continue
                leads.append({"title":title,"candidateUrl":link,"sourceQuery":query,
                 "status":"research_needed","entryVerified":False})
        except ET.ParseError: pass
        time.sleep(1.0)
    unique={x["candidateUrl"]:x for x in leads}
    return list(unique.values())[:100]
def main():
    parser=argparse.ArgumentParser()
    parser.add_argument("--discover",action="store_true")
    parser.add_argument("--max-checks",type=int,default=350)
    args=parser.parse_args()
    REPORT.mkdir(parents=True,exist_ok=True)
    catalog=json.loads(CATALOG.read_text(encoding="utf-8"))
    prior_path=REPORT/"latest.json"
    prior={}
    if prior_path.exists():
        try: prior={r["id"]:r for r in json.loads(prior_path.read_text()).get("results",[])}
        except Exception: pass
    checked=[]
    # Serial checks: respect target sites and avoid overwhelming sponsor infrastructure.
    for item in catalog[:max(0,args.max_checks)]:
        checked.append(inspect(item))
        time.sleep(.35)
    queue=[]
    for r in checked:
        previous=prior.get(r["id"],{})
        if r["needsHumanReview"] or (previous.get("finalUrl") and previous["finalUrl"]!=r.get("finalUrl")):
            queue.append({**r,"previousFinalUrl":previous.get("finalUrl"),"repairAction":"investigate_official_sponsor_source"})
    ts=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    payload={"generatedAt":ts,"totalCatalog":len(catalog),"checked":len(checked),
      "statusCounts":{s:sum(r["status"]==s for r in checked) for s in sorted(set(x["status"] for x in checked))},
      "results":checked,"disclaimer":"HTTP checks only; forms and eligibility are not certified."}
    (REPORT/"latest.json").write_text(json.dumps(payload,indent=2)+"\n")
    (REPORT/"repair-queue.json").write_text(json.dumps({"generatedAt":ts,"items":queue},indent=2)+"\n")
    if args.discover:
        leads=discoveries()
        (REPORT/"discovery-queue.json").write_text(json.dumps({"generatedAt":ts,"candidates":leads},indent=2)+"\n")
    print(json.dumps({"catalog":len(catalog),"checked":len(checked),"repairQueue":len(queue),
                       "discoveryEnabled":args.discover,"statusCounts":payload["statusCounts"]},indent=2))
if __name__=="__main__": main()
