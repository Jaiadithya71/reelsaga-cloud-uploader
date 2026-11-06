# ReelSaga stop investigation, 2026-11-06

## What actually happened

The November 5 third Soldier run released the existing draft, then lost verification while polling that same post. Its saved receipt says sending, exact Buffer post 6aec10813ddb81d22107892b, no link. The last original traceback identifies a post READ, not the release mutation. The old client's blanket exception discarded the original HTTP status/body, so that exact failed read's cause is unrecoverable from the traceback. Subsequent exact-post reads at 10:54 and 11:10 IST returned HTTP429; the latter recorded Retry-After1494130 seconds.

On November 6 at21:30IST, direct Instagram profile and video inspection found the third part already public:
https://www.instagram.com/reelsaga3000/reel/DfWQUDsFCEX/
The caption is Episode2 Part1/2, with Ad and AI content labels. DOM time is November5 05:14:32Z, matching the original run. Actual playback pixels show Soldier footage, readable captions,720x1280,44seconds. This is independent publication confirmation, NOT an exact Buffer-record mapping or a complete audio/frame/cover comparison certificate. Do not repost. The journal preserves those distinctions instead of adding a fully verified entry.

## API versus Instagram

Buffer's API rate limits count requests, not posts. Official docs distinguish them from daily channel posting limits. The public status page was fully operational at investigation time. Neither source proves Instagram account health or the exact exhausted window. A17-day wait is consistent with a30-day quota window, not proof without the original body/headers.

Sources:
- https://developers.buffer.com/guides/api-limits.html
- https://developers.buffer.com/guides/efficient-api-usage.html
- https://status.buffer.com/
- https://github.com/Jaiadithya71/reelsaga-cloud-uploader/actions/runs/41972510654

## Local causes and repairs

Earlier code discarded exception details and rate-limit telemetry. The November5 patch added sanitized evidence and bounded polling. November6 strengthens it:
- Preserve every repeated RateLimit and RateLimit-Policy header, not just the first.
- Honor a repository cooldown record before any request, including after process restart.
- Honor previous429 receipts in a new client instance.
- Fail closed on malformed saved cooldown evidence.
- Preserve non429 HTTP status class, without arbitrary response text, cookies or credentials.
- Offline tests exercise these guards with no real network requests.

The per-part publisher still performs up to three complete historical inventories, plus channel and post checks. That is a request-amplification risk, not measured proof of the exhausted quota's full cause. Server createdAt/dueAt filters alone do not prove completeness for actual sentAt, old drafts or deleted-public duplicates. Do not weaken duplicate/spacing guards merely to save requests. Further optimization needs a complete reconciliation model.

## Remaining constraints

All publication holds stay closed. The current publishing entry point checks the global pause before reaching its old reconciliation branch, and source review expires after48hours. Therefore it is NOT a safe status-only tool under current holds. Do not lift a hold to run it. Future exact-ID reconciliation needs a separate read-only entry point, after a provider-confirmed quota reset or cooldown expiry. It must not create, edit, release, clean up hosts or advance the queue.

The source relay for the unresolved post may remain staged; do not delete before confirming that publication no longer depends on it and checking its own cleanup contract. Existing batch deadline requires separate follow-through, not a silent retention extension.

No Buffer traffic, account change, spend, new upload or publication occurred in this investigation. Independent Instagram evidence is the first recovery fallback for an unknown write when available, without switching to Buffer UI to bypass its API restriction.

A separate `ig-recovery/read_soldier_pending.py` is now available for that future exact-ID read. It accepts only the existing saved post/channel identities, calls `post` once, inherits cooldown checks, and has no mutation or ledger/host imports. It has NOT been run against Buffer. It is not wired to a scheduled workflow or an automatic retry.

## Media QA follow-through21:34IST

The current S3 original matched58618023bytes and SHA4a7561df6173707ba640ca1b759af143531b5a257a3ed02ec87754c8a26a3507. Normal public embed retrieval succeeded. Served duration44.117seconds,720x1280, audio present, full decode passed. Four source/served frame correlations0.99866–0.99916; cover0.99882; caption exact. Actual cover and four frames were visually inspected. Journal now records these checks. Exact Buffer-record mapping and full spoken-word certification remain unverified.

Only one relay object currently exists, the original E2P1 uploaded November5 05:13:31Z. Exact encrypted batch deadline/host binding awaits access approval; no source object deleted. Conservative deadline-review checkpoint is November10 evening, before the code-derived six-day limit around November11 morning. Do not extend retention silently.
