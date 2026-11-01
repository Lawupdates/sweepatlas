#!/usr/bin/env python3
"""Audit all published sweepstakes entry/rules URLs. No unverified auto-replacements."""
import concurrent.futures, datetime, json, pathlib, re, urllib.request, urllib.error
ROOT=pathlib.Path(__file__).resolve().parents[1]
records=json.loads((ROOT/"data/sweepstakes.json").read_text())
UA="Mozilla/5.0 (compatible; SweepsTitanLinkAudit/1.0)"
def check(url):
    try:
        req=urllib.request.Request(url,headers={"User-Agent":UA,"Accept":"text/html,application/xhtml+xml"})
        with urllib.request.urlopen(req,timeout=22) as resp:
            content=resp.read(150000).decode("utf-8","ignore")
            final=resp.geturl()
            status=resp.status
            title=re.search(r"<title[^>]*>(.*?)</title",content,re.I|re.S)
            title=re.sub(r"\s+"," ",title.group(1)).strip() if title else ""
            return {"status":status,"finalUrl":final,"title":title[:150],"error":None}
    except Exception as exc:
        return {"status":None,"finalUrl":None,"title":"","error":str(exc)[:170]}
urls=sorted(set(u for x in records for u in [x.get("entryUrl"),x.get("rulesUrl")] if u))
with concurrent.futures.ThreadPoolExecutor(max_workers=16) as pool:
    scanned=dict(zip(urls,pool.map(check,urls)))
results=[]
for x in records:
    entry=x.get("entryUrl",""); rules=x.get("rulesUrl","")
    er=scanned.get(entry,{}); rr=scanned.get(rules,{})
    problems=[]
    if er.get("error"): problems.append("entry_request_failed")
    if rr.get("error"): problems.append("rules_request_failed")
    if re.search(r"/(?:official-rules|rules|terms|conditions|faq)(?:/|$|[?#])",entry,re.I):
        problems.append("entry_url_looks_like_rules")
    if not entry: problems.append("missing_entry_url")
    if re.fullmatch(r"https?://[^/]+/?",entry,re.I): problems.append("entry_is_generic_homepage")
    if re.search(r"/(?:official-rules|rules|terms|conditions|faq)(?:/|$|[?#])",entry,re.I): problems.append("entry_is_rules_not_entry")
    if entry==rules: problems.append("entry_and_rules_identical_review_manually")
    if entry and rules and entry.rstrip("/") == rules.rstrip("/"): problems.append("entry_and_rules_same_destination")
    if er.get("status") and er["status"] >= 400: problems.append("entry_http_error")
    if er.get("finalUrl") and any(host in er["finalUrl"].lower() for host in ("google.com/search", "bing.com/search")): problems.append("entry_redirects_to_search")
    if er.get("title") and re.search(r"404|not found|access denied|page unavailable|expired|promotion ended|contest closed",er["title"],re.I): problems.append("entry_page_unavailable_or_expired")
    if er.get("title") and re.search(r"official rules|terms and conditions|privacy policy",er["title"],re.I): problems.append("entry_page_title_looks_like_rules")
    if er.get("finalUrl") and re.search(r"/(?:products|collections|shop|store|news|blog|about|contact)/?$",er["finalUrl"],re.I): problems.append("entry_redirects_to_nonentry_section")
    if er.get("finalUrl") and re.search(r"/(?:official-rules|rules|terms|conditions)(?:/|$|[?#])",er["finalUrl"],re.I):
        problems.append("entry_redirects_to_rules")
    if er.get("finalUrl") and re.search(r"https?://[^/]+/?$",er["finalUrl"]):
        problems.append("entry_redirects_to_homepage")
    results.append({"id":x["id"],"name":x["name"],"entryUrl":entry,"rulesUrl":rules,"entry":er,"rules":rr,"flags":problems})
out=ROOT/"audit-results";out.mkdir(exist_ok=True)
report={"dateUTC":datetime.datetime.now(datetime.timezone.utc).isoformat(),"count":len(records),"uniqueUrls":len(urls),"flagged":sum(bool(x["flags"]) for x in results),"results":results}
(out/"link-audit.json").write_text(json.dumps(report,indent=2)+"\n")
lines=["# Sweeps Titan Link Audit","",f"Records: {len(records)}; unique URLs: {len(urls)}; records flagged for review: {report['flagged']}","",
"CRITICAL: HTTP success alone does NOT prove the correct contest entry form works. Every flagged entry must be repaired using the exact contest name and sponsor, and manually verified before claiming verified. Blocks, captchas, location restrictions and JavaScript forms require manual review.","","| Listing | Flags | Entry URL | Rules URL |","|---|---|---|---|"]
for x in results:
    if x["flags"]: lines.append(f"| {x['name'].replace('|','/')} | {', '.join(x['flags'])} | {x['entryUrl']} | {x['rulesUrl']} |")
(out/"link-audit.md").write_text("\n".join(lines)+"\n")
print(json.dumps({"records":len(records),"unique_urls":len(urls),"flagged":report["flagged"]},indent=2))
