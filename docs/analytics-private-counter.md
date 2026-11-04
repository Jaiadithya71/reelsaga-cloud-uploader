# ReelSaga index - private analytics counter

Privacy-bounded first-party analytics for https://reelsaga-index.vercel.app/ .
No third-party trackers, no cookies, no IPs, no user agents, no raw identifiers stored.

## Components

1. **Beacon** - inline `<script>` in the generated index page. Source: `build.py`
   in the `Jaiadithya71/reelsaga-index` repo (the `h.append("""<script>...` block
   right after the SERIES data append). Emits GET events via `fetch(...,
   {mode:'no-cors', credentials:'omit'})`. Do NOT revert to `(new Image()).src=`:
   image-pixel GETs to script.google.com are silently dropped by some browsers.
2. **Endpoint** - Google Apps Script web app (source archived beside this file:
   `docs/analytics-endpoint.gs`). Apps Script project "ReelSaga index analytics",
   id `1283Czjaz0hD3G-w_PJ9AjJjuraa94Z-pTDH1d1xK2jtnw0nGPSUrp3eJ`, SASTRA account.
   Deployed as Web app, Execute as Me, access Anyone (ingest-only, returns "ok",
   no read API). Deployment URL:
   https://script.google.com/macros/s/AKfycbxS5eDDDtFY5QtfHk5kaD1KpRA9lmskt7XZCAh2yx9MgdkBNEGxaEDIxekaKQ4WeqK0Dw/exec
   IMPORTANT: after editing the Apps Script source, create a NEW deployment
   version - the live /exec keeps running the version it was deployed with.
3. **Sheet (the only view)** - "ReelSaga analytics (private)":
   https://docs.google.com/spreadsheets/d/1mFJaysmS6J27HzlT3fGkZqwkAQ2Sb1cfeERIg7Wa7uY/edit
   Tabs: `Events` (raw real events), `Hashes` (rolling 35-day visitor hash set),
   `QA` (isolated test events; never aggregated), `Summary` (formula dashboard).

## Events

GET params: `t` = view|time|tap, `v` = random browser id (localStorage `rv_id`,
16 random bytes hex), `s` = series key from `#s=` hash, `x` = tap label (24 chars
max), `ms` = active milliseconds for time pings, `src` = source tag passthrough
(e.g. `?src=ig`, pending approval), `qa=1` = client test label (no trust: routed
to the QA tab and excluded from all real aggregates).

Visitor key = SHA-256(server salt + ':' + v), truncated to 24 hex chars. Salt
rotation resets new/returning state.

## Bounds (fail closed)

- EVENTS_HARD_CAP 90000 rows total; EVENTS_PER_DAY_CAP 5000;
  EVENTS_PER_HASH_DAY 300; RATE_MIN_MS 1000 between accepted events per visitor.
- Active time: client accumulates only while tab visible AND last interaction
  (pointerdown/keydown/scroll/touchstart, passive listeners, no content) within
  60s; pings every 15s accumulated; server clamps 60s/ping and 3600s/browser-day.
- One `view` per visitor per series per day (duplicates dropped).
- DAILY_HASH_CAP 2000 new hashes/day; hashes older than 35 days pruned.

## Definitions (Summary tab mirrors these)

- Page/series views: one view event = a page load or a series open. Not sessions.
- Unique browsers: distinct visitor hashes. Browsers, NOT people.
- Returning: hash also seen on an earlier day within the rolling 35-day window.
- Engaged browser-day: a tap or >=15s interaction-aware active time that day.
- Episode taps: clicks on a.part / a.btn.ig / a.btn.orig (label in `x`;
  affiliate clicks labeled "affiliate").

## Known quirks / maintenance

- Sheets `COUNTUNIQUE(FILTER(...))` counts the FILTER #N/A as 1 when empty -
  Summary formulas guard with ROWS()>0.
- `day_ist` cells auto-convert to real dates; QUERY over them needs `date '...'`
  literals, and QUERY date output needs a yyyy-mm-dd cell number format.
- Unattributed deploy-correlated landing-view pairs (see Summary note) are
  retained with uncertainty; not confirmed audience, not our own traffic.
- QA testing: load the site with `?qa=1`; all events land in the QA tab only.
