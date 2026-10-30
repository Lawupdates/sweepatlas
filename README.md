# SweepAtlas ✦

A responsive sweepstakes discovery and personal entry-tracking website. The site pulls **reviewed** promotions from `data/sweepstakes.json`, shows the sponsor’s official entry and rules pages, and stores favorites, personal information, and entry history locally in the browser.

## Where to open

Repository: https://github.com/Lawupdates/sweepatlas

Expected Pages URL, **once GitHub Pages is enabled**: https://lawupdates.github.io/sweepatlas/

Under repository **Settings → Pages**, set **Deploy from a branch → main → /(root)**. We cannot infer the live site is published merely from successful GitHub commits.

## Features

- Mobile-friendly search, category and geographic eligibility filters, sorting and accessible tab navigation.
- Review-gated live directory with source rules, sponsor, estimated prize value, expiration date and entry cadence.
- Personal favorites, daily planner, manual entry tracking, CSV exports and local JSON backup/restore.
- Optional personal entry profile that remains in this device’s browser storage.
- Sponsor listing request form in GitHub Issues; submitted promotions undergo independent verification.
- Python catalog validator (on each push, pull request and nightly schedule).
- Scheduled RSS-based discovery of *potential* giveaways, creating a review report artifact; no unsourced sweepstakes are automatically promoted.

## Publishing a real giveaway

Edit `data/sweepstakes.json`. Example data format (this is an **illustrative dummy**, not a real entry and must not be published):

```json
[
  {
    "id":"example-2026-promotion",
    "name":"Official promotion title",
    "sponsor":"Legal sponsor",
    "desc":"Factual prize description",
    "category":"Travel",
    "cadence":"Daily",
    "icon":"🎁",
    "value":1500,
    "place":"US",
    "minAge":"18+",
    "endDate":"2026-12-31",
    "reviewedAt":"2026-10-30",
    "entryUrl":"https://example.org/official-entry",
    "rulesUrl":"https://example.org/official-rules"
  }
]
```

Required cadence: Daily, Weekly, Monthly or One-time. Region filters currently support US, AZ and CA. Both URLs must be HTTPS and directly linked to the legitimate sponsor or authorized administrator. Ensure both are verified and the date is accurate; real listing records cannot merely use the example URLs. `scripts/check_catalog.py` checks formatting and duplicates. The browser excludes expired offers.

## Curator workflow

Review every candidate's official sponsor pages, complete rules, free-entry method, geography, age eligibility, entry limits, start/end time zone and registration requirements before publishing. Recheck promotions periodically. A candidate found by an automated news search is **not** automatically verified or entered.

Run the validator locally: `python scripts/check_catalog.py`.

## Important limits

GitHub Pages has no secure server-side database, authentication, payment processing, ad billing, automated sitewide scraping, scheduled personalized messages or third-party form submission capability. These are **not** represented as enabled. A paid multi-user platform would require a separate hosted backend and infrastructure. Automated entry may violate individual contest rules or anti-bot measures; SweepAtlas currently requires manual entry on the sponsor site.

Personal data saved in local storage is accessible to anyone using that browser profile; do not store passwords, SSNs or payment card details. Advertiser placements are a demonstration and do not collect payments.
