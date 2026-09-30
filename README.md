# ReelSaga cloud uploader: validation prototype

This is an unconnected, local prototype, not a working uploader or deployment.

## Implemented

- Validate source resolution, duration, complete-episode-part review and pixel/decode checks.
- Check exact issued, series-matched affiliate URLs and the disclosure in both descriptions and captions.
- Bind destinations to the intended YouTube channel and Instagram account.
- Block an unverified "link in bio" claim.
- Store per-platform job state and block duplicate starts or changed metadata.
- Verify downloaded bytes against SHA256.

Ten offline tests pass. The private repository and owner-approved repo-scoped write deploy key are set up. No publishing credentials, paid services, Drive files or account conversions have been created.

## Proposed server-side design

1. Private Drive folder holds verified MP4 files and a versioned manifest.
2. Scheduled server worker validates manifest and hashes before every action.
3. Durable database stores claims, session references, container IDs and platform video IDs. The included SQLite demonstration must be replaced with durable storage for Render cron, whose local filesystem is ephemeral.
4. YouTube uses resumable uploads. An unaudited API project is not a public-publishing solution: uploads are private-locked, and YouTube Help requires re-upload via an audited service or official app/site. Do not promise a manual Public flip.
5. Instagram uses Instagram Login for the owner's Creator/Business account. A Facebook Page is not required for that configuration. Media must be available at a public HTTPS URL during ingestion, so use an approved, short-lived signed media relay or object-store URL rather than publishing the Drive folder.
6. Resume processing by saved IDs after crashes. An uncertain publish stays paused until reconciled. Never blind-retry creation or publishing.
7. Inspect one canary per platform, including final pixels/playback, before enabling a scheduled batch. API processing success is not copyright clearance. The public YouTube run still needs a defined claims-verification route.

## Owner decisions and access still needed

- Repository destination is resolved: this private repository. The owner approved its repo-scoped SSH write key; the private key is stored securely and is not committed.
- Chosen Google Drive account and folder, then scoped OAuth authorization for the uploader. The uploader will authenticate separately from any existing assistant integrations.
- Hosting cost approval. Render cron minimum is $1 per service monthly plus runtime. Durable storage and media relay costs remain to quote. No spend is approved.
- Google Cloud OAuth authorization for the exact YouTube channel and scoped Drive access; project audit for Public API uploads.
- Owner changes Instagram to Creator/Business and creates/authorizes the Meta app with instagram_business_basic and instagram_business_content_publish. No account changes have been made.
- Secure storage of all tokens and app secrets, with rotation/expiry handling. Never commit secrets or send them in messages.

Expected implementation time once these are settled: roughly 1-2 focused working days for code and tests, then account authorization and canary checks. External audit timing is unknown.

## Official sources verified

- https://developers.facebook.com/docs/instagram-platform/overview
- https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/content-publishing/
- https://developers.google.com/youtube/v3/docs/videos/insert
- https://support.google.com/youtube/answer/7300965?hl=en
- https://render.com/docs/cronjobs

## Tests

Run `python3 -m unittest discover -s tests -v`.
