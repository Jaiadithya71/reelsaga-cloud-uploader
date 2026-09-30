# ReelSaga cloud uploader: unconnected adapter prototype

This is an unconnected, local prototype, not a working uploader or deployment.

## Implemented

- Validate source resolution, duration, complete-episode-part review and pixel/decode checks.
- Check exact issued, series-matched affiliate URLs and the disclosure in both descriptions and captions.
- Bind destinations to the intended YouTube channel and Instagram account.
- Block an unverified "link in bio" claim.
- Store per-platform job state and block duplicate starts or changed metadata.
- Verify downloaded bytes against SHA256.

Seventy-nine offline tests pass. Added injectable Drive queue/download, resumable Private YouTube and Instagram container/publish adapters. The adapter transport is deliberately not connected and has no credentials. A serialized six-hour GitHub Actions preflight workflow is gated OFF by default; it only runs tests/read-only validation, never publishing. The private repository and owner-approved repo-scoped write deploy key are set up. No publishing credentials, paid services, Drive files or account conversions have been created.

The durable-state CAS contract and six fault/resumption tests are now included, but no remote backend is connected.

An injectable one-item worker now connects validation, identity checks, hashes, saved-session recovery and canary gates. It is not called by the workflow or connected to real accounts.

## Proposed server-side design

1. Private Drive folder holds verified MP4 files and a versioned manifest.
2. Scheduled server worker validates manifest and hashes before every action.
3. Durable remote state stores session references, container IDs and platform video IDs. The included SQLite demonstration is NOT enough for ephemeral Actions runners. Every remote non-idempotent write must have a persisted claim/checkpoint first; state or checkpoint failure must stop the run.
4. YouTube uses resumable uploads. An unaudited API project is not a public-publishing solution: uploads are private-locked, and YouTube Help requires re-upload via an audited service or official app/site. Do not promise a manual Public flip.
5. Instagram uses Instagram Login for the owner's Creator/Business account. A Facebook Page is not required for that configuration. Media must be available at a public HTTPS URL during ingestion, so use an approved, short-lived signed media relay or object-store URL rather than publishing the Drive folder.
6. Resume processing by saved IDs after crashes. An uncertain publish stays paused until reconciled. Never blind-retry creation or publishing.
7. Inspect one canary per platform, including final pixels/playback, before enabling a scheduled batch. API processing success is not copyright clearance. The public YouTube run still needs a defined claims-verification route.

## Owner decisions and access still needed

- Repository destination is resolved: this private repository. The owner approved its repo-scoped SSH write key; the private key is stored securely and is not committed.
- Chosen Google Drive account and folder, then scoped OAuth authorization for the uploader. The uploader will authenticate separately from any existing assistant integrations.
- Hosting resolved: owner selected GitHub Actions. GitHub Free and a $0 Actions account budget with Stop usage Yes were verified live. Only standard Linux runners and bounded runtime are allowed; no overages. Durable remote state and HTTPS media relay remain to design/connect. No spend is approved.
- Google Cloud OAuth authorization for the exact YouTube channel and scoped Drive access; project audit for Public API uploads.
- Owner changes Instagram to Creator/Business and creates/authorizes the Meta app with instagram_business_basic and instagram_business_content_publish. No account changes have been made.
- Secure storage of all tokens and app secrets, with rotation/expiry handling. Never commit secrets or send them in messages.

Expected implementation time once these are settled: roughly 1-2 focused working days for code and tests, then account authorization and canary checks. External audit timing is unknown.

See [AUTHORIZATION.md](AUTHORIZATION.md) for exact pending taps, narrow Drive scope caveat, refresh expiry and canary gates. No auth taps or Drive folder creation have been performed.

## Official sources verified

- https://developers.facebook.com/docs/instagram-platform/overview
- https://developers.facebook.com/docs/instagram-platform/instagram-api-with-instagram-login/content-publishing/
- https://developers.google.com/youtube/v3/docs/videos/insert
- https://support.google.com/youtube/answer/7300965?hl=en
- https://render.com/docs/cronjobs

## Tests

Run `python3 -m unittest discover -s tests -v`.

Audit preparation drafts are in `audit/`. Injected operator-control tests now cover default-off, reviewed enablement and stop-before-revoke. No live disconnect/delete control or public policy is implemented yet.

An HTTPS transport now rejects foreign origins, redirects and authorization overrides, uses an injected token provider, and redacts uncertain network errors. It remains unconnected; no real credential flow or API calls have been run.

Google refresh/revoke lifecycle and form-only authorization transport are implemented with injected secure storage, grant checks, cached expiry, invalid-grant stop and disabled-on-revocation-failure behavior. These are not wired to production tokens or a durable control store.

A candidate Firestore REST CAS backend now uses create-only/exact-update-time preconditions and fails closed on read/update errors. This is not a selected or created database; IAM transport and billing-off/free-tier validation remain required.

`web/` now contains a responsive local development interface for metadata,
audience and content/quality acknowledgement review. Real connect/upload and
account/data controls are disabled and clearly labelled as unconnected.
No public website is deployed and this preview is not audit evidence.

Explicit runtime activation gate requires real canary, secure storage, live remote CAS and stop-control tests plus owner scope/policy evidence. It is not wired to scheduled execution.

PKCE S256, random state and one-use callback helpers are covered by offline tests. No client/callback type has been selected or registered; no authorization URL for a real app has been issued.

Desktop bootstrap accepts only installed-client config, binds a random loopback port, uses PKCE/state, verifies the exact channel and stores credentials only in a supported native OS keyring. No live Google test or Actions credential transfer exists yet; see DESKTOP-SETUP.md.

Offline integration exercises a real local loopback listener with mocked Google/keyring: successful channel verification stores once, wrong channel stops. No live Google grant has been tested.
