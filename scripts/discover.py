#!/usr/bin/env python3
"""Find leads, not verified sweepstakes. RSS feeds may be incomplete or unreliable."""
import datetime, json, os, re, urllib.request, xml.etree.ElementTree as ET
from urllib.parse import quote
from html import unescape
from pathlib import Path

TERMS = [
    '"sweepstakes" "official rules" "2026" "November"',
    '"sweepstakes" "official rules" "2026" "December"',
    '"giveaway" "no purchase necessary" "2026"',
    '"daily entry" "sweepstakes" "2026"',
    '"weekly drawing" "sweepstakes" "2026"',
    '"grand prize" "official rules" "2026"',
    '"contest" "prize" "official rules" "2026"',
    '"travel sweepstakes" "official rules" "2026"',
    '"cash sweepstakes" "official rules" "2026"',
    '"vehicle sweepstakes" "official rules" "2026"',
    '"gift card sweepstakes" "official rules" "2026"',
    '"food sweepstakes" "official rules" "2026"',
    '"home makeover sweepstakes" "2026" official',
    '"electronics giveaway" "official rules" "2026"',
    '"holiday sweepstakes" "official rules" "2026"',
    'site:hallmarkchannel.com sweepstakes 2026',
    'site:foodnetwork.com sweepstakes 2026',
    'site:goldbelly.com sweepstakes 2026',
    'site:microsoftrewards.com sweepstakes 2026',
    'site:rewards.microsoft.com sweepstakes 2026'
]
MAX_PER_QUERY=40
def clean(s): return re.sub(r"\s+"," ",re.sub(r"<[^>]+>"," ",unescape(s or ""))).strip()[:600]
def get_feed(term):
    url="https://www.google.com/search?tbm=nws&output=rss&q="+quote(term)
    req=urllib.request.Request(url,headers={"User-Agent":"SweepAtlas-Research/1.0 (review-only; contact repository owner)"})
    with urllib.request.urlopen(req,timeout=15) as response:
        if response.status!=200: raise ValueError("Unexpected HTTP status")
        return response.read(1024*1024)
def main():
    leads={};errors=[]
    for term in TERMS:
        try:
            root=ET.fromstring(get_feed(term))
            for item in root.findall(".//item")[:MAX_PER_QUERY]:
                title=clean(item.findtext("title"));link=(item.findtext("link") or "").strip()
                if not link.startswith("https://") or not title:continue
                if link not in leads:
                    leads[link]={"title":title,"url":link,"query":term,"published":clean(item.findtext("pubDate")),"status":"UNVERIFIED — editor review required"}
        except Exception as ex:
            errors.append({"query":term,"error":str(ex)[:180]})
    out={"generated_utc":datetime.datetime.now(datetime.timezone.utc).isoformat(),"warning":"Discovery candidates only. These may be articles, inactive offers, or false positives. Never publish without manual rules verification.","candidates":list(leads.values()),"feed_errors":errors}
    dest=Path(os.environ.get("SWEEPATLAS_REPORT","discovery-candidates.json"))
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_text(json.dumps(out,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print("Candidates:",len(leads),"Feed errors:",len(errors),"Saved:",dest)
if __name__=="__main__":main()
