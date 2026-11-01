#!/usr/bin/env python3
"""Read-only HTTPS and response-header health report for the public site."""
import datetime
import json
import pathlib
import re
import ssl
import urllib.error
import urllib.request

ROOT = pathlib.Path(__file__).resolve().parents[1]
TARGETS = ("https://sweepstitan.com/", "https://www.sweepstitan.com/", "http://sweepstitan.com/")
REQUIRED = ("strict-transport-security", "x-content-type-options", "referrer-policy", "x-frame-options")
results = []
for url in TARGETS:
    result = {"requested": url, "status": "unknown"}
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "SweepsTitanSecurityMonitor/1.0"})
        with urllib.request.urlopen(req, timeout=15, context=ssl.create_default_context()) as response:
            final = response.geturl()
            headers = {k.lower(): v for k, v in response.headers.items()}
            result.update({"status": "ok", "http_status": response.status, "final_url": final,
                           "final_https": final.startswith("https://"),
                           "missing_security_headers": [h for h in REQUIRED if h not in headers],
                           "hsts": headers.get("strict-transport-security"),
                           "content_security_policy": headers.get("content-security-policy")})
            if url == TARGETS[0]:
                html = response.read(500000).decode("utf-8", "ignore")
                result["insecure_asset_urls"] = sorted(set(re.findall(
                    r'(?:src|href)\s*=\s*["\x27](http://[^"\x27]+)', html, re.I)))[:30]
    except urllib.error.HTTPError as error:
        result.update({"status": "http_error", "http_status": error.code})
    except Exception as error:
        result.update({"status": "unconfirmed", "error": type(error).__name__ + ": " + str(error)[:160]})
    results.append(result)
report = {"checked_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
          "results": results,
          "limitations": "No browser Safe Browsing verdict, JavaScript execution, or complete TLS cipher scan. Vercel certificate/DNS settings must be inspected separately."}
out = ROOT / "audit-results"
out.mkdir(exist_ok=True)
(out / "site-security.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
print(json.dumps(report, indent=2))
