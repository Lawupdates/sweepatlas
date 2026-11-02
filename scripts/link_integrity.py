#!/usr/bin/env python3
"""Sweeps Titan link integrity: non-destructive reports, no speculative publishing."""
import concurrent.futures, datetime, json, os, re, ssl, time, urllib.error, urllib.parse, urllib.request
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
CATALOG=ROOT/"data/sweepstakes.json"
REPORT=ROOT/"data/link-integrity.json"
NOW=datetime.datetime.now(datetime.timezone.utc)
UA="SweepsTitanLinkIntegrity/1.0 (+https://sweepstitan.com/)"
MAX_WORKERS=int(os.getenv("TITAN_LINK_WORKERS","6"))
TIMEOUT=int(os.getenv("TITAN_LINK_TIMEOUT","12"))
LIMIT=int(os.getenv("TITAN_LINK_LIMIT","0"))
RULE_HINT=re.compile(r"(?:official[ -]?rules|sweepstakes[ -]?rules|/rules(?:/|$|\?)|terms[ -]?and[ -]?conditions)",re.I)
DEAD_HINT=re.compile(r"(?:404 not found|page not found|this giveaway has ended|promotion has ended|sweepstakes has ended|contest is closed)",re.I)
FORM_HINT=re.compile(r"<form\b|gleam\.io/|sweepwidget\.com/|viralsweep\.com/|woobox\.com/|king sumo",re.I)

def check(item):
    entry=item.get("entryUrl","")
    rules=item.get("rulesUrl","")
    result={"id":item.get("id"),"name":item.get("name"),"entryUrl":entry,"rulesUrl":rules,
            "checkedAt":NOW.isoformat(),"status":"needs_review","issues":[]}
    try:
        end=datetime.date.fromisoformat(item.get("endDate",""))
        if end < NOW.date():result["issues"].append("expired_by_listed_end_date")
    except ValueError:result["issues"].append("invalid_end_date")
    if entry==rules:result["issues"].append("entry_matches_rules_link")
    if not entry.startswith("https://"):result["issues"].append("invalid_entry_scheme");return result
    parts=urllib.parse.urlsplit(entry)
    if parts.username or parts.password or not parts.hostname:result["issues"].append("unsafe_url");return result
    if RULE_HINT.search(parts.path) or RULE_HINT.search(parts.query):result["issues"].append("likely_rules_page_not_entry")
    # Public URL check; never submit entry form and never claim an actual user entry.
    try:
        req=urllib.request.Request(entry,headers={"User-Agent":UA,"Accept":"text/html,application/xhtml+xml"},method="GET")
        with urllib.request.urlopen(req,timeout=TIMEOUT,context=ssl.create_default_context()) as response:
            result["httpStatus"]=response.status
            result["finalUrl"]=response.url
            body=response.read(150000).decode("utf-8","replace")
            title=re.search(r"<title[^>]*>(.*?)</title>",body,re.I|re.S)
            result["pageTitle"]=re.sub(r"\s+"," ",title.group(1)).strip()[:180] if title else ""
            if DEAD_HINT.search(result["pageTitle"]) or DEAD_HINT.search(body[:60000]):result["issues"].append("expired_or_not_found_page")
            if not FORM_HINT.search(body):result["issues"].append("no_form_detected_manual_check")
            final=urllib.parse.urlsplit(response.url)
            if final.hostname!=parts.hostname:result["issues"].append("redirected_to_other_host")
            if final.scheme!="https":result["issues"].append("insecure_redirect")
            if RULE_HINT.search(final.path) or RULE_HINT.search(final.query):result["issues"].append("redirected_to_rules_page")
            if final.path in ("","/") and parts.path not in ("","/"):result["issues"].append("redirected_to_homepage")
            if final.hostname==parts.hostname and final.path in ("","/") and not final.query and not FORM_HINT.search(body):result["issues"].append("possible_homepage_not_entry")
    except urllib.error.HTTPError as error:
        result["httpStatus"]=error.code
        result["issues"].append("access_restricted_unconfirmed" if error.code in (401,403,429) else "http_error")
    except Exception as error:
        result["issues"].append("network_check_failed")
        result["error"]=type(error).__name__
    if not result["issues"]:result["status"]="reachable_needs_human_confirmation"
    else:result["status"]="needs_review"
    return result

def main():
    records=json.loads(CATALOG.read_text())
    records=records[:LIMIT] if LIMIT>0 else records
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1,min(MAX_WORKERS,12))) as pool:
        results=list(pool.map(check,records))
    summary={}
    for item in results:
        for issue in item["issues"]:summary[issue]=summary.get(issue,0)+1
    payload={"generatedAt":NOW.isoformat(),"checked":len(results),
             "warning":"Automated checks cannot prove a sweepstakes form accepts entries. Do not label links verified solely from this report.",
             "summary":dict(sorted(summary.items())),"results":results}
    REPORT.parent.mkdir(parents=True,exist_ok=True)
    REPORT.write_text(json.dumps(payload,indent=2,ensure_ascii=False)+"\n")
    print(json.dumps({"checked":len(results),"issues":summary,"report":str(REPORT)}))
if __name__=="__main__":main()
