#!/usr/bin/env python3
"""Extract inline JavaScript for Node syntax validation."""
from html.parser import HTMLParser
from pathlib import Path
class S(HTMLParser):
    def __init__(self):
        super().__init__();self.inside=False;self.scripts=[]
    def handle_starttag(self,tag,attrs):
        if tag=="script":
            attr=dict(attrs)
            kind=(attr.get("type") or "text/javascript").lower()
            self.inside=not attr.get("src") and kind in {"text/javascript","application/javascript","module"}
    def handle_endtag(self,tag):
        if tag=="script":self.inside=False
    def handle_data(self,data):
        if self.inside:self.scripts.append(data)
p=S();p.feed(Path("index.html").read_text(encoding="utf-8"))
assert p.scripts,"No inline JS found"
Path("/tmp/sweepatlas-site.js").write_text("\n".join(p.scripts),encoding="utf-8")
print("JavaScript extracted for Node syntax check")
