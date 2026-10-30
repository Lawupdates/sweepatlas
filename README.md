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
- A submission-and-review workflow for official sponsor promotions. Automated discovery reports (where enabled) are research leads only, not published offers.

## Sourcing policy

Do not copy a competing directory's full database, editorial descriptions, branding, photos or creative selection. Do not bypass a website's access restrictions, ignore an explicit prohibition on scraping, or imply that a directory listing is sponsor verification. Publishers must source factual promotion information from official sponsor or authorized administrator pages, check relevant terms, and write original summaries. The former competitor-directory feed and its importer have been removed. Legal compliance depends on actual use, jurisdiction and platform terms; obtain professional review before monetized launch.

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

## Automation additions (October 30, 2026)

- `.github/workflows/discover.yml` requests six scheduled discovery runs daily at 00:11, 04:11, 08:11, 12:11, 16:11 and 20:11 UTC (GitHub may delay scheduled jobs). GitHub Actions must be enabled and the workflow must have permission to write the repository to persist the report.
- `radar.html` displays the latest `data/discovery-candidates.json` **unverified research leads** and provides a search/sort interface. Candidate links are not vetted entry pages. A fresh feed appears only after the workflow completes successfully.
- `extension/` contains a Chrome/Edge extension for **user-initiated** autofill on the active HTTPS page. Read `extension/README.md` for installation and limitations; the extension has not been store-published or end-to-end browser-tested.
- Automated contest submission, anti-bot bypass, CAPTCHA handling, paid account management and advertiser billing have **not** been implemented. Sponsoring sites' conditions must be respected.

### Getting the research scan running

1. In GitHub open **Actions**, and enable workflows if prompted.
2. Choose **Discover sweepstakes candidates** and select **Run workflow** to perform the first scan.
3. Open **Settings → Actions → General → Workflow permissions**, choose **Read and write permissions** if needed and permitted; otherwise the report update may fail.
4. Inspect the workflow run and the `data/discovery-candidates.json` report. The radar page will show it once GitHub Pages publishes the updated files.
5. Enable GitHub Pages under **Settings → Pages → Deploy from a branch → main → /(root)**. Test `https://lawupdates.github.io/sweepatlas/` and `https://lawupdates.github.io/sweepatlas/radar.html`.
