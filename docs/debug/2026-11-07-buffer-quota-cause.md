# Buffer request budget diagnosis, 2026-11-07

Live read-only Settings > API at 15:10 IST confirmed Personal Access usage: 0/150 per15min, 0/600 per24h, 3000/3000 per30days, Usage limit reached. Free plan, three connected channels. One listed personal key, reelsaga-automation, expires Oct23 2027; account:read, posts:read, posts:write. No credential values retained.

This confirms the currently exhausted shared 30-day API request budget, not a per-channel posting cap or queue-size limit. It is consistent with the Nov5 HTTP429 exact-post read and long Retry-After, but the original response body/RateLimit headers were not saved. The exact first failed read before that429 is unrecoverable. The third reel was independently confirmed public, so do not treat the failed verification as failed publication.

Our code contributes: a new part uses two full channel inventories, each100rows/page, plus2channel reads, draft creation/read, release, and1–3status reads: 2P+6 to2P+8 requests at P pages before diagnostic/resume reads. A resumed draft also scans history. No complete historical request ledger exists, so neither all3000calls nor a numerical retry fraction can be assigned. Official docs say429responses do not consume quota/extend lockout; other reads/writes/errors can consume it.

## Prevention and recovery

Existing durable cooldown remains unchanged. No API request was made in this investigation. New offline-tested guards stop subsequent requests while any recorded successful response shows10%or less remaining in a policy; policy name joins quota/window to remaining/reset. They survive fresh client instances using sanitized receipts. A25request per-client-run cap also bounds pagination amplification when headers are absent. Per-run request indexes improve future attribution without saving request text, keys, cookies or response bodies.

Do not remove complete duplicate scans using an unproved createdAt/dueAt filter: historical sent rows survive deletions and arbitrary older drafts can conflict. A cache alone becomes stale during rendering/hosting. Existing read_soldier_pending.py is the separate exact-ID status-only route with no history scan; use only after permitted quota recovery. It never releases a post. Broader publisher scan reduction needs a complete verified reconciliation/index model, not dropping safety checks.

Zero-spend path: honor the cooldown, await rolling capacity or an explicit free reset from Buffer. Original Retry-After is earliest allowed check, not guaranteed enough continuous budget. Existing support email already requests a free reset review; no duplicate followup, upgrade, newkey, newaccount, channel change or posting occurred. All publication/quality holds remain.

A channel-settings metrics-refresh notice also affects all3IG connections. It has not been acted on and is not evidence that it caused the API429 or that all publishing is broken.

Sources:
- https://publish.buffer.com/settings/api (authenticated live dashboard)
- https://publish.buffer.com/settings/channels
- https://developers.buffer.com/guides/api-limits.html
- https://developers.buffer.com/guides/efficient-api-usage.html
- https://support.buffer.com/en-us/articles/troubleshooting-buffers-api-VgBuQXUCDI
- https://status.buffer.com/ (currently operational, not account health proof)
