#!/usr/bin/env python3
"""Sponsor-link importer. Uses U.S. public directory as discovery only.
Publish only records with an explicit sponsor entry link and future deadline;
otherwise leave them as research candidates for review."""
import concurrent.futures, datetime as dt, hashlib, html, json, re, time
from html.parser import HTMLParser
from pathlib import Path
from urllib.parse import urljoin,urlsplit
from urllib.request import Request,urlopen
TODAY=dt.datetime.now(dt.timezone.utc).date()
ROOT="https://giveowl.com/c/us/"
class LinkParser(HTMLParser):
 def __init__(self): super().__init__();self.links=[];self.a=None
 def handle_starttag(self,tag,attrs):
  if tag=="a":self.a={"url":dict(attrs).get("href",""),"name":""}
 def handle_data(self,s):
  if self.a:self.a["name"]+=s
 def handle_endtag(self,tag):
  if tag=="a" and self.a:self.links.append(self.a);self.a=None
def fetch(url):
 req=Request(url,headers={"User-Agent":"Mozilla/5.0 (compatible; SweepsTitanIndexer/1.0; +https://sweepstitan.com/)"})
 with urlopen(req,timeout=14) as f:return f.read(1500000).decode("utf-8","replace")
def links(src,base):
 p=LinkParser();p.feed(src)
 return [{"url":urljoin(base,x["url"]),"name":" ".join(html.unescape(x["name"]).split())} for x in p.links]
def clean(raw):
 return " ".join(html.unescape(re.sub("<[^>]+>"," ",raw)).split())
def group(name):
 n=name.lower()
 for pat,cat in [(r"car|vehicle|truck|motorcycle|ford|tesla|jeep|boat|bronco|mercedes|scooter","Vehicles"),(r"trip|vacation|resort|travel|cruise|flight|hotel|flyaway|stay","Travel"),(r"computer|headphone|gaming|monitor|phone|playstation|xbox|sony|electronic|apple watch","Electronics"),(r"cash|check|money|card|spree|scholarship","Cash"),(r"food|burger|dinner|meal|coffee|chocolate|snack","Food"),(r"home|kitchen|furniture|appliance|decor|garden","Home")]:
  if re.search(pat,n):return cat
 return "Lifestyle"
def detail(link):
 url=link["url"]
 try:
  page=fetch(url)
  text=clean(re.sub(r"<(script|style)\b[^>]*>.*?</\1>"," ",page,flags=re.I|re.S))
  if "Open No purchase necessary" not in text and "Open" not in text:return None
  m=re.search(r"Deadline\s+([A-Za-z]+\s+\d{1,2},\s+20\d{2})",text)
  if not m:return None
  end=dt.datetime.strptime(m.group(1),"%B %d, %Y").date()
  if end<TODAY:return None
  m2=re.search(r"Prize\s+(.{20,260}?)\s+Deadline",text)
  description=(m2.group(1) if m2 else "Prize information on organizer website.")[:230]
  anchors=links(page,url)
  sponsor=[a for a in anchors if "Enter at organizer" in a["name"] and urlsplit(a["url"]).scheme=="https"]
  if not sponsor:return None
  dest=sponsor[0]["url"]
  if urlsplit(dest).netloc.endswith("giveowl.com"):return None
  title=link["name"][:150]
  if not title:return None
  sid="sourced-"+hashlib.sha256((title.lower()+dest).encode()).hexdigest()[:16]
  return {"id":sid,"name":title,"sponsor":title.split(" Sweepstakes")[0][:100],"desc":"Sponsor promotion: "+description,"category":group(title+" "+description),"cadence":"See rules","icon":"🎁","value":0,"place":"US","minAge":"See rules","endDate":str(end),"addedAt":str(TODAY),"reviewedAt":str(TODAY),"entryUrl":dest,"rulesUrl":url,"entryReviewStatus":"Official organizer link found through public index; verify sponsor eligibility and form before entering","source":"GiveOwl"}
 except Exception:return None
def main():
 records_file=Path("data/sweepstakes.json");records=json.loads(records_file.read_text())
 result_file=Path("data/discovery-candidates.json")
 try:existing=json.loads(result_file.read_text())
 except:existing={}
 raw=fetch(ROOT)
 page_links=[a for a in links(raw,ROOT) if urlsplit(a["url"]).netloc=="giveowl.com" and urlsplit(a["url"]).path.startswith("/e/")]
 unique={a["url"]:a for a in page_links}
 candidates=list(unique.values())
 # Always preserve research candidates even if sponsor details cannot be parsed.
 with concurrent.futures.ThreadPoolExecutor(max_workers=10) as ex:
  fetched=list(ex.map(detail,candidates))
 existing_names={re.sub(r"\W+","",str(x.get("name","")).lower()) for x in records}
 existing_urls={x.get("entryUrl","").rstrip("/") for x in records}
 added=0
 for x in fetched:
  if not x:continue
  k=re.sub(r"\W+","",x["name"].lower())
  if k in existing_names or x["entryUrl"].rstrip("/") in existing_urls:continue
  records.append(x);existing_names.add(k);existing_urls.add(x["entryUrl"].rstrip("/"));added+=1
 records_file.write_text(json.dumps(records,ensure_ascii=False,indent=2)+"\n")
 result_file.write_text(json.dumps({"generated_at":str(TODAY),"notice":"Research-only directory links; cannot be treated as verified entry forms.","candidates":[{"name":x["name"],"url":x["url"],"source":"GiveOwl US","status":"research-only"} for x in candidates],"imported_this_run":added},ensure_ascii=False,indent=2)+"\n")
 print(json.dumps({"directory_links_found":len(candidates),"sponsor_links_parsed":sum(bool(x) for x in fetched),"added":added,"total":len(records)}))
if __name__=="__main__":main()
