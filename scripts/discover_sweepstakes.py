#!/usr/bin/env python3
"""Import public discovery leads, not verified sweepstakes entries.
Uses public pages responsibly, records links for human checking and does not
copy competitor text as listings. Source sites may block access."""
import json,re,datetime,urllib.parse,urllib.request,html,hashlib
from html.parser import HTMLParser
from pathlib import Path
TODAY=datetime.datetime.now(datetime.timezone.utc).date().isoformat()
SOURCES=[
("GiveOwl US","https://giveowl.com/c/us/"),
("FreebieShark","https://www.freebieshark.com/sweepstakes"),
("Sweepstakes Radar","https://www.sweepstakesradar.com/no-purchase-necessary"),
("Gleam Giveaways","https://gleamgiveaways.com/"),
("SweepsToday","https://www.sweepstoday.com/sweepstakes"),
("Sweepstakes Advantage","https://www.sweepsadvantage.com/"),
("SweepFeed","https://www.sweepfeed.com/sweepstakes"),
("I Love Giveaways","https://ilovegiveaways.com/sweepstakes/"),
]
class Links(HTMLParser):
 def __init__(self):super().__init__();self.a=None;self.data=[]
 def handle_starttag(self,tag,attrs):
  if tag=="a":self.a={"href":dict(attrs).get("href",""),"name":""}
 def handle_data(self,data):
  if self.a:self.a["name"]+=data
 def handle_endtag(self,tag):
  if tag=="a" and self.a:self.data.append(self.a);self.a=None
def gather(source,url):
 req=urllib.request.Request(url,headers={"User-Agent":"SweepsTitanDiscovery/1.0 (+https://sweepstitan.com/; public research index)"})
 with urllib.request.urlopen(req,timeout=18) as response:
  if response.status!=200:raise RuntimeError(str(response.status))
  raw=response.read(2000000).decode("utf-8","replace")
 p=Links();p.feed(raw);host=urllib.parse.urlsplit(url).netloc
 items=[]
 for a in p.data:
  link=urllib.parse.urljoin(url,html.unescape(a["href"]))
  parsed=urllib.parse.urlsplit(link)
  name=" ".join(html.unescape(a["name"]).split())[:180]
  if parsed.scheme!="https" or not name or len(name)<9 or len(name)>175:continue
  # Category indexes, forums, navigation and advertising pages are not contests.
  if re.search(r"/(?:category|categories|forum|forums|tag|tags|page|search)(?:/|$)",parsed.path,re.I):continue
  if re.search(r"^<.*>$|^(?:see more|view all|browse|next|previous)$",name,re.I):continue
  if "/amember/page/" in parsed.path:continue
  if parsed.netloc==host and ("/giveaway" in parsed.path or "/sweepstake" in parsed.path or "/contest" in parsed.path or "/promotion" in parsed.path or "/win-" in parsed.path):
   if parsed.path.rstrip("/")==urllib.parse.urlsplit(url).path.rstrip("/"):continue
   items.append({"name":name,"url":link.split("#")[0],"source":source,"found_at":TODAY,"status":"research-only"})
 return items
def main():
 existing=Path("data/discovery-candidates.json")
 try:old=json.loads(existing.read_text());old=old.get("candidates",[]) if isinstance(old,dict) else []
 except:old=[]
 leads={c["url"]:c for c in old if isinstance(c,dict) and c.get("url","").startswith("https://")}
 # Normalize legacy source records without discarding historical metadata.
 for c in leads.values():
  c["title"]=c.get("title") or c.get("name") or "Unidentified promotion source"
  c["id"]=c.get("id") or hashlib.sha256(c["url"].encode()).hexdigest()[:16]
  c["validation_status"]=c.get("validation_status") or "research_only"
 results=[]
 for name,url in SOURCES:
  try:
   found=gather(name,url)
   for lead in found:
    link=lead["url"]
    if link in leads:
     # Preserve prior verification, expiry, source titles and candidate IDs.
     record=leads[link]
     record.setdefault("research_source",lead["source"])
     record.setdefault("found_at",lead["found_at"])
    else:
     leads[link]={**lead,"id":hashlib.sha256(link.encode()).hexdigest()[:16],
                  "title":lead["name"],"research_source":lead["source"],
                  "validation_status":"research_only","end_date":None}
   results.append({"source":name,"found":len(found),"status":"fetched"})
  except Exception as exc:results.append({"source":name,"status":"unavailable","reason":str(exc)[:150]})
 published=Path("data/sweepstakes.json")
 try:
  records=json.loads(published.read_text())
  live={str(x.get("entryUrl","")).split("#")[0] for x in records}
  live|={str(x.get("rulesUrl","")).split("#")[0] for x in records}
 except:live=set()
 candidates=[v for k,v in leads.items() if k not in live and v.get("url","").startswith("https://")]
 candidates.sort(key=lambda x:(x.get("validation_status",""),x.get("title","")))
 existing.write_text(json.dumps({"generated_at":TODAY,"notice":"Unverified research links only; not confirmed entry forms or eligible/active sweepstakes.","sources":results,"candidates":candidates[:10000]},separators=(",", ":"))+"\n")
 print(json.dumps({"sources":results,"research_candidates":len(candidates),"published_records_unchanged":True}))
if __name__=="__main__":main()
