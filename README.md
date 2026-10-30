# SweepAtlas ✦

Mobile-first sweepstakes discovery and entry tracking **interactive preview**.

## Test the preview
Open `index.html` through GitHub Pages, or download and open the file in a modern browser. Once GitHub Pages is enabled for the default `main` branch, visit:

https://lawupdates.github.io/sweepatlas/

## Features implemented
- Responsive, accessible landing page and listing catalog
- Search, categories, region filters, sorting
- Favorites, local entry log, daily entry routine and checklist
- Personal profile saved locally on the user's device
- CSV exports, advertiser placement preview, sample listing detail dialogs
- No third-party scripts or server required for the preview

## Important limitations
The seed listings are **fictional samples**; none can be entered and there are no live verified URLs or sweepstakes rules. There is **no website-wide live crawler**, official-rule validation engine, production database, user accounts, automated form submissions, reminders, email, billing, authentication, admin workflow, or advertiser booking system. Browser storage is not encrypted and is not a safe place to keep highly sensitive data. Avoid entering SSNs, payment card details or passwords.

## Production roadmap
1. Establish a verified sweepstakes source database and permission-aware discovery pipeline. Collect official rules, sponsor, eligibility, start/end times, AMOE, entry frequency and last-seen verification.
2. Build authenticated backend and rate-limited ingestion, staff moderation, audit history, abuse/report mechanisms and safe link checks.
3. Implement subscriptions and advertiser billing through a payment processor with webhook verification, refunds, taxes and clear sponsored labeling.
4. Provide optional autofill for third-party sites **only with user permission**, respecting site rules and never circumventing CAPTCHA or anti-bot protections. Do not promise universal auto-entry.
5. Add verified expiration updates, filtering by state and age, reminder schedules, newsletter and privacy/terms documentation.

## Privacy
The preview stores profile details, checklists, favorites and logs in `localStorage` on the browser/device. Clearing site data deletes them. No data is intentionally transmitted to a server by this preview.

## Deploy
Repository Settings → Pages → Build and deployment → Deploy from a branch → `main` / `/ (root)` → Save. The preview then appears at https://lawupdates.github.io/sweepatlas/ after GitHub finishes publishing.
