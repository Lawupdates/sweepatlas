# Sweeps Titan™ — Master delivery checklist
Updated: 2026-11-01. **Source of truth:** check a box only after implementation AND a successful production test. Code presence alone is not completion.

## Product requirements and acceptance criteria
### Publishing, security, performance
- [x] GitHub Pages Actions builds have previously succeeded; GitHub is the chosen publisher. Keep Vercel project available as fallback.
- [ ] Confirm sweepstitan.com points to the latest GitHub Pages version over HTTPS (including www); preserve DNS until verified.
- [ ] Confirm no insecure/mixed-content assets or broken local links on the live website.
- [ ] Measure Core Web Vitals (mobile LCP, INP, CLS) and actual network payload. Improve based on measurements, not just CSS patches.
- [ ] Reduce very large inline homepage HTML (~600 KB in repository), remove unused/duplicated styles and scripts without changing approved visuals.
- [ ] Evaluate repository privacy and never commit API keys, customer data, or credentials.

### Brand and visual experience
- [ ] Verify the approved premium Sweeps Titan™ logo is used on ALL pages, navigation, favicon, store, promotional artwork, and merchandise; remove obsolete visible Sweep Atlas branding. Do not change internal storage keys until migrated safely.
- [ ] Audit and test colorful multi-hued theme (no neon yellow or white buttons), generous typography, bold readable text, rounded buttons, exciting banners.
- [ ] Test responsive iPhone and desktop viewports for overlap, clipping, touch sizes, scrolling, and accessible motion controls.
- [ ] Test 1-second metallic confetti blast with reduced-motion support and acceptable mobile performance.
- [ ] Test floating cracking fortune cookie and 25–100 readable fortunes, dismiss / delete behavior.
- [ ] Add distinct context-appropriate imagery to published contests without misrepresenting prize photographs.
- [ ] Test Discover, My Entries, Planner, My Profile, Newest (three-day placement), Mail-ins, browser extension, Get Started, and Advertise with us across all pages.
- [ ] Preserve humorous, playful but respectful copy; avoid misleading winner, earnings or urgency claims.

### Sweepstakes catalog and reliability
- [ ] Grow from **331 catalog records observed on 2026-11-01** toward 1,500 only with legitimate, unique sponsor-supported contests, accurate eligibility, dates, prizes, cadence, free-entry methods, official entry and rules URLs.
- [ ] Audit each published entry link. A reachable landing page is not proof of a working entry form.
- [ ] Keep internal vetting states out of public card labels, but provide honest rules/entry distinctions, exclusions, and problem reporting.
- [ ] Enforce expiration, deduplication, newest-three-day grouping, accurate visible counts and categories.
- [ ] Run automated sponsor discovery and link-quality checks every six hours; review failures and write back reports safely without git push conflicts.
- [ ] Never copy another directory's editorial text, creative content, brand or database indiscriminately; respect site rules and access restrictions.
- [ ] Investigate AI-assisted official source extraction and prioritization, with human review before publication.

### Visitor tools / admin
- [ ] Test browser-local favorites, profile, planner, daily/weekly/monthly tracking, JSON backup/restore and extension end-to-end.
- [ ] Build a securely authenticated private visitor/admin analytics dashboard with privacy policy and appropriate consent/cookie practices if needed.
- [ ] For cross-device syncing and personalized AI, select a real secure backend (GitHub Pages alone is static). Do not claim backend features work without one.
- [ ] Add meaningful AI search/recommendations without fabricating eligibility or entry success.

### Store, monetization and promotion
- [ ] Audit shop.html storefront, merchandise images, item descriptions, variants, prices, availability and cart arithmetic.
- [ ] Use the approved Sweeps Titan™ logo on ALL products; preserve existing Printify draft/published product IDs and distinguish mockups from live listings.
- [ ] Test mobile checkout only when payment provider is explicitly activated; payments currently on hold.
- [ ] Test advertising/rates pages, prominent Advertise with us navigation, and sponsor placement disclosure.
- [ ] Test MegaBonanza promotional link/logo with appropriate disclosure and separate it from free sweepstakes entry results.
- [ ] Audit sitemap, metadata, structured data, search console verification, robots.txt and analytics.

## Release gate
1. Confirm files changed and commit SHAs.
2. GitHub directory validation, quality checks and Pages deployment must pass.
3. Verify deployed site on domain, mobile/desktop, navigation, screenshots, representative links and storefront.
4. Record evidence, known blockers, and test date in this document. **Never mark untested code as complete.**

## Current known status
- GitHub Pages publishing workflows and quality checks have succeeded on earlier commits.
- Main index, entry-desk, radar, advertising pages and scripts exist. Presence does not prove functional correctness.
- Existing sweepstakes catalog contains 331 records (2026-11-01 inspection).
- Browser-local tracking works in code, but cross-device account infrastructure is not implemented.
- Store and Printify integration are not verified complete; payments deliberately on hold.
- Vercel is preserved, but GitHub Pages is the preferred publishing route.
