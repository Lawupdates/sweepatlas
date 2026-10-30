#!/usr/bin/env python3
"""Import directory-indexed sweepstakes as UNVERIFIED leads.
Uses a single public index page, modest access, no login/bypass and no personal data.
Never labels these entries 'verified' or claims direct official rules links.
"""
import datetime,json,re,urllib.request
from bs4 import BeautifulSoup
from pathlib import Path
from urllib.parse import urljoin,urlparse
SOURCE="https://www.freebieshark.com/sweepstakes"
DEST=Path("data/directory-leads.json")
def text(tag):return " ".join(tag.stripped_strings) if tag else ""
def get():
    request=urllib.request.Request(SOURCE,headers={"User-Agent":"SweepAtlasListingResearch/1.0 (+https://github.com/Lawupdates/sweepatlas; editorial leads only)"})
    with urllib.request.urlopen(request,timeout=30) as r:
        if r.status!=200:raise RuntimeError("Bad status")
        return r.read(4_000_000)
def main():
    soup=BeautifulSoup(get(),"html.parser")
    # Find only entries with a linked headline followed by a visible cadence/end date.
    found={}
    pattern=re.compile(r"Prizes?:\s*(.*?)\s*\|\s*Enter\s+(Daily|Weekly|Monthly|Once)\s*\|\s*Ends\s*(\d\d/\d\d/\d{4})",re.I)
    for a in soup.select("a[href]"):
        name=text(a).strip()
        if not (12<=len(name)<=180) or not re.search(r"sweepstakes|instant win game",name,re.I):continue
        href=urljoin(SOURCE,a.get("href",""))
        p=urlparse(href)
        if p.scheme!="https" or p.netloc not in {"www.freebieshark.com","freebieshark.com"}:continue
        context=[]
        for node in (a.parent,a.parent.parent if a.parent else None):
            if node:context.append(text(node)[:600])
        match=next((m for c in context if (m:=pattern.search(c))),None)
        if not match:continue
        prize,frequency,ends=match.groups()
        date=datetime.datetime.strptime(ends,"%m/%d/%Y").date()
        if date<datetime.datetime.now(datetime.timezone.utc).date():continue
        if href in found:continue
        low=(name+" "+prize).lower()
        if any(k in low for k in ("vacation","travel","trip","resort","cruise","flight")):cat="Travel"
        elif any(k in low for k in ("car","jeep","ford","motorcycle","vehicle","truck")):cat="Vehicles"
        elif any(k in low for k in ("laptop","phone","speaker","tv","tech","electronics")):cat="Electronics"
        elif any(k in low for k in ("cash","venmo","check","gift card","mastercard")):cat="Cash"
        elif any(k in low for k in ("food","snack","pizza","grocery","deli","coffee")):cat="Food"
        elif any(k in low for k in ("kitchen","home","furniture","appliance")):cat="Home"
        else:cat="Lifestyle"
        sponsor=name.split("“")[0].split('"')[0].strip()[:90]
        found[href]={"id":"lead-"+str(len(found)+1).zfill(4),"name":name,"sponsor":sponsor,"desc":prize[:180],"category":cat,"cadence":"One-time" if frequency.lower()=="once" else frequency.title(),"icon":"🎁","value":0,"place":"US","endDate":date.isoformat(),"sourceUrl":href,"sourceName":"FreebieShark","status":"unverified","reviewedAt":datetime.datetime.now(datetime.timezone.utc).date().isoformat()}
    records=list(found.values())[:250]
    if len(records)<150:raise RuntimeError(f"Parsed only {len(records)} records; refusing to replace good catalog")
    DEST.parent.mkdir(parents=True,exist_ok=True)
    DEST.write_text(json.dumps(records,ensure_ascii=False,indent=2)+"\n",encoding="utf-8")
    print(f"Imported {len(records)} source-listed opportunities for review")
if __name__=="__main__":main()
