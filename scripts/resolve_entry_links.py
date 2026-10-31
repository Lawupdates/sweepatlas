#!/usr/bin/env python3
"""Find possible official entry links for each named contest.

Only consult public search results, preserve per-record progress, and never assert
that a search hit proves a contest is currently accepting entries.
"""
import concurrent.futures as cf
import datetime as dt
import json
import os
import re
import time
import urllib.parse as up
import urllib.request as ur
import xml.etree.ElementTree as ET
from pathlib import Path

ROOT=Path(__file__).resolve().parents[1]
SRC=ROOT/"data/discovery-candidates.json"
OUT=ROOT/"data/entry-lookup-results.json"
BATCH=max(1,min(int(os.environ.get("LOOKUP_BATCH","120")),1500))
WORKERS=12
EXCLUDE=("news.google.com","google.com","bing.com","yahoo.com","reddit.com","facebook.com","instagram.com","pinterest.com","youtube.com","sweepstakesadvantage.com","contestgirl.com","sweepstakesfanatics.com","sweepstakeslovers.com","sweepstake.com","thefreebieguy.com","contestbee.com","ultracontest.com")
ENTRY_HINT=re.compile(r"(sweepstakes|giveaway|enter.to.win|contest|promotion|win.a|gleam.io)",re.I)
def fetch(url):
    req=ur.Request(url,headers={"User-Agent":"Mozilla/5.0 (compatible; SweepsTitanResearch/1.0)"})
    with ur.urlopen(req,timeout=9) as response:
        if response.status!=200: raise ValueError("HTTP "+str(response.status))
        return response.read(180000),response.geturl()
def clean_title(title):
    title=re.split(r"\s+[-–|]\s+",title or "")[0].strip()
    return re.sub(r"[^\w\s&'-]"," ",title)[:110]
def eligible(url):
    try:
        p=up.urlsplit(url)
        host=(p.hostname or "").lower()
        return p.scheme=="https" and host and not any(host==x or host.endswith("."+x) for x in EXCLUDE) and not p.username and not p.password
    except ValueError:return False
def inspect_potential(url):
    try:
        body,landing=fetch(url)
        if not eligible(landing):return "redirected_outside_entry_site"
        page=body.decode("utf-8","replace").lower()
        form=bool(re.search(r'<form\b|type=["\'](?:email|submit)["\']',page))
        text=bool(re.search(r"enter to win|sweepstakes|giveaway|official rules|enter now",page))
        if form and text:return "entry_form_possible"
        if text:return "promotion_page"
        return "no_contest_context"
    except Exception:
        return "page_blocked_or_unreachable"

def lookup(item):
    title=clean_title(item.get("title",""))
    if len(title)<8:return {"status":"insufficient_title"}
    words=list(dict.fromkeys(w for w in re.findall(r"[a-z0-9]{4,}",title.lower()) if w not in {"official","rules","2026","2027","sweepstakes","giveaway","contest","promotion","enter","the","with","from"}))
    if len(words)<2:return {"status":"insufficient_title"}
    queries=['"'+title.replace('"',"")+'" entry', " ".join(words[:7])+" sweepstakes enter official", " ".join(words[:7])+" giveaway entry rules"]
    possible=[]; errors=[]; used=set()
    for query in queries:
        try:
            data,_=fetch("https://www.bing.com/search?format=rss&q="+up.quote(query))
            for e in ET.fromstring(data).findall("./channel/item"):
                url=(e.findtext("link") or "").strip()
                label=(e.findtext("title") or "")
                if not eligible(url) or url in used:continue
                used.add(url)
                combined=(label+" "+up.urlsplit(url).path).lower()
                overlap=sum(w in combined for w in words)
                if overlap<2 or overlap/max(1,len(words))<.65:continue
                if not ENTRY_HINT.search(url+" "+label):continue
                check=inspect_potential(url)
                if check not in ("entry_form_possible","promotion_page"):continue
                possible.append({"url":url,"title":label[:180],"overlap":overlap,"destination_check":check})
                if len(possible)>=3:break
            if possible:break
        except Exception as err:errors.append(str(err)[:120])
    result={"looked_up_at":dt.datetime.now(dt.timezone.utc).isoformat(),"search_queries":queries,"search_version":3}
    if possible:return {**result,"status":"possible_entry_pages","possible":possible}
    if len(errors)==len(queries):return {**result,"status":"search_failed","errors":errors}
    return {**result,"status":"entry_page_not_found"}
def main():
    feed=json.loads(SRC.read_text(encoding="utf-8"))
    records=feed.get("candidates",[])
    try: report=json.loads(OUT.read_text(encoding="utf-8"))
    except (OSError,ValueError):report={}
    results=report.get("results",{})
    if not isinstance(results,dict):results={}
    # Every record is present in output even if not yet searched.
    active={x["id"] for x in records if x.get("id")}
    results={k:v for k,v in results.items() if k in active}
    todo=[x for x in records if x.get("id") and (x["id"] not in results or (results[x["id"]].get("status")=="search_failed" and results[x["id"]].get("search_version",0)<3))][:BATCH]
    with cf.ThreadPoolExecutor(max_workers=WORKERS) as pool:
        for item,res in zip(todo,pool.map(lookup,todo)):
            results[item["id"]]={"contest_title":item.get("title"),"original_article":item.get("url"),**res}
    counts={}
    for record in results.values():
        name=record.get("status","unknown")
        counts[name]=counts.get(name,0)+1
    payload={"generated_utc":dt.datetime.now(dt.timezone.utc).isoformat(),"total_source_records":len(records),"searched":len(results),"remaining":len(records)-len(results),"results_by_status":counts,"notice":"Candidate links from public web search, not certified active entry forms. Human review required before publishing.","results":results}
    OUT.write_text(json.dumps(payload,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Searched",len(todo),"this run;",len(results),"with records;",len(records)-len(results),"remaining",counts)
if __name__=="__main__":main()
