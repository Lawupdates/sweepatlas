#!/usr/bin/env python3
"""Conservative public entry-page checker; never submits a form or solves a CAPTCHA."""
import datetime as dt
import json, re, urllib.request
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urlsplit

ROOT=Path(__file__).resolve().parents[1]
CAND=ROOT/"data/discovery-candidates.json"
CURATED=ROOT/"data/sweepstakes.json"
REPORT=ROOT/"data/entry-audit.json"
LOOKUPS=ROOT/"data/entry-lookup-results.json"
BLOCK={"news.google.com","google.com","www.google.com"}
class Page(HTMLParser):
    def __init__(self):
        super().__init__();self.form=False;self.inputs=set();self.buttons=[];self.in_button=False
    def handle_starttag(self,tag,attrs):
        a=dict(attrs)
        if tag=="form":self.form=True
        if tag=="input":self.inputs.add((a.get("type") or "text").lower())
        if tag=="button":self.in_button=True
    def handle_data(self,data):
        if self.in_button:self.buttons.append(data.strip().lower())
    def handle_endtag(self,tag):
        if tag=="button":self.in_button=False

def check(url):
    try:
        p=urlsplit(url)
        if p.scheme!="https" or not p.hostname or p.hostname.lower() in BLOCK:return "invalid_or_news_url"
        req=urllib.request.Request(url,headers={"User-Agent":"Mozilla/5.0 (compatible; SweepAtlasEntryAudit/1.0)"})
        with urllib.request.urlopen(req,timeout=9) as r:
            if r.status!=200:return "http_error"
            if "html" not in r.headers.get("Content-Type","").lower():return "not_html"
            final=urlsplit(r.geturl())
            if final.scheme!="https" or final.hostname in BLOCK:return "redirected_to_nonentry"
            html=r.read(250000).decode("utf-8","replace")
        page=Page();page.feed(html)
        # A form alone may be a login/search/newsletter; require entry-related context.
        text=re.sub(r"<[^>]+>"," ",html).lower()
        context=bool(re.search(r"enter to win|sweepstakes entry|giveaway entry|submit (your )?entry|official entry form",text))
        fields=bool(page.inputs & {"email","text","tel"})
        if page.form and context and fields:return "form_detected_review_required"
        if context:return "entry_page_possible_review_required"
        return "no_entry_form_detected"
    except Exception:return "unreachable_or_blocked"

def main():
    candidates=json.loads(CAND.read_text()).get("candidates",[])
    try: lookup_results=json.loads(LOOKUPS.read_text()).get("results",{})
    except (OSError,ValueError): lookup_results={}
    if not isinstance(lookup_results,dict):lookup_results={}
    for x in candidates:
        result=lookup_results.get(x.get("id"),{})
        options=result.get("possible",[]) if isinstance(result,dict) else []
        for option in options:
            if option.get("destination_check") in ("entry_form_possible","promotion_page") and option.get("url","").startswith("https://"):
                x["entry_url"]=option["url"]
                x["entry_source"]="automated_title_lookup"
                break
    curated=json.loads(CURATED.read_text())
    checks=[];count=0
    lead_checks=[]
    today=dt.datetime.now(dt.timezone.utc).date()
    counts=Counter()
    seen=set()
    for x in candidates:
        u=x.get('entry_url') or x.get('url') or ''
        canonical=u.split('?')[0].rstrip('/').lower()
        expiry=x.get('end_date')
        if canonical in seen:
            counts['duplicates']+=1
            x['validation_status']='duplicate_research_lead'
        elif expiry and expiry < today.isoformat():
            counts['expired']+=1
            x['validation_status']='expired'
        elif not x.get('entry_url'):
            counts['research_only_no_entry_url']+=1
            x['validation_status']='research_only'
        else:
            counts['entry_url_pending_review']+=1
            x['validation_status']='pending_manual_review'
        seen.add(canonical)
        lead_checks.append({"id":x.get("id"),"url":u,"status":x.get("validation_status"),"entry_url":x.get("entry_url"),"end_date":expiry})
    for x in curated:
        if x.get('endDate') and x['endDate'] < today.isoformat():counts['expired_curated']+=1
    # Always inspect curated pages; inspect discoverer-found direct URLs only, never news articles.
    for x in curated:
        u=x.get("entryUrl")
        if u:checks.append({"id":x.get("id"),"title":x.get("name"),"url":u,"result":check(u),"kind":"curated","expiry":x.get("endDate")})
    for x in candidates:
        u=x.get("entry_url")
        if not u:continue
        outcome=check(u)
        x["entry_check_status"]="needs_manual_form_confirmation"
        x["entry_audit_result"]=outcome
        checks.append({"id":x.get("id"),"title":x.get("title"),"url":u,"result":outcome,"kind":"discovered"})
        count+=1
        # Inspect every discovered candidate with an actual entry destination.
    CAND.write_text(json.dumps({**json.loads(CAND.read_text()),"candidates":candidates},ensure_ascii=False,indent=2)+"\n")
    REPORT.write_text(json.dumps({"checked_at_utc":dt.datetime.now(dt.timezone.utc).isoformat(),"notice":"Automated detection is not proof a form works. No record becomes confirmed without manual review.","candidate_counts":dict(counts),"total_research_leads":len(candidates),"curated_count":len(curated),"automatically_confirmed_forms":0,"lead_checks":lead_checks,"results":checks},ensure_ascii=False,indent=2)+"\n")
    print("Inspected",len(checks),"potential entry pages; none automatically certified.")
if __name__=="__main__":main()
