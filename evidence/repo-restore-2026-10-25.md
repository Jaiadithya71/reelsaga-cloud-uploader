# Repo restore plan and record (2026-10-25)

## Incident
Commit e0e0013fc4 ("Fix later-series probe pack URLs", Oct 24 07:55 UTC) was built from a sparse git index and silently replaced main's tree with only 2 files, dropping 820 files: all 56 root runtime .py modules, 366 workflows, docs, and config. Detected Oct 25 19:08 IST when the restored quota probe failed with ModuleNotFoundError: actions_canary.

## Pre-incident reference tree
81ee0f371f8c8b1dfb01a291d5d45ddbeb02e2f2 (822 files) - last full tree before e0e0013fc4.

## Recovery method
- Exact restore set computed as tree(81ee0f371f) minus tree(tip 558c32df): 819 files.
- Later additive work PRESERVED (tip wins, not in restore set): ambassador-rerender-ep-enc.yml, tigris-fetch-part-enc.yml, db670995/db671003 render probes (e0e0013f URL fixes), probe-db670995/671003-ep1p1-private.yml, yt-upload-quota-probe.yml, evidence/* (ledger, captions, screenshot), project/captions/*.
- Differing files NOT overwritten: .github/workflows/db670995-ep1-render-probes.yml and db671003-ep1-render-probes.yml keep their e0e0013f fixed versions.
- Every restored file content-verified against its pre-incident git blob SHA-1 before commit.

## Two-stage restore
1. Commit 8c3920c4: 11 runtime .py modules (import closure needed by live probes).
2. This commit: remaining 808 files (workflows, docs, configs, audit dir).

## Affected runs during broken window (Oct 24 07:55 UTC - Oct 25 13:37 UTC)
- Tigris fetch part (encrypted artifact, parameterized): 6 runs failed 17:07-17:10 UTC Oct 24 (ran on 1cdaa016, broken tree).
- Ambassador EP re-render: succeeded on 9476dd0f (self-contained workflow; no .py imports).
- YT upload quota probe run 40198499815 failed 13:38 UTC Oct 25 (ModuleNotFoundError) - the detection signal.
- DB670995/DB671003 private probes first dispatch: cancelled/failed pre-restore; redispatched post-restore (runs 40199440411, 40199442289).

## Deliberate exclusion: 189 staged-reel mp4s NOT restored
The pre-incident tree contained 189 .mp4 files in staging dirs (dramacps-wrongdoor-prepared 29, vows-prepared 31, hybrid-test 30, rsboost-mech-prepared 27, rsboost-beast-prepared 23, maid-prepared 17, rsboost-bitter-prepared 13, netshort-ice-prepared 12, heiress-probes 5, next-probes 2). These were committed by an earlier session contrary to the standing rule "never push mp4s to git / no public hosting of staged reel material outside IG". The accidental wipe removed them; they are intentionally NOT re-committed. Sources remain in the DramaBox distribution ZIPs and Tigris; parts are reproducible via the deterministic render recipe. This exclusion also keeps the repo lean.

## Verification
- 619 non-mp4 files restored (+ 11 runtime modules in 8c3920c4 = 630 of 819); each content-verified against its pre-incident blob SHA-1 before commit.
- Tip files preserved untouched: 19 additive files (evidence, captions, Ambassador workflows, new probes, quota probe) + 2 differing render-probe workflows kept at fixed versions.
## Operational consequences (evaluated 2026-10-25 19:29 IST)
- Scheduled-workflow audit over the FULL restored set (372 workflows): queue.yml is the ONLY schedule trigger; ZERO push/pull_request triggers, so no workflow can reactivate from pushes and no stale posting can resume on its own. Every publishing workflow is workflow_dispatch-only. All runs since the restore are manual dispatches.
- queue.yml ('ReelSaga queue preflight', cron 17 */6 * * *) is gated by vars.REELSAGA_PREFLIGHT_ENABLED == 'true'. Direct evidence it was NOT enabled pre-wipe: run 40062739954 (Oct 24 04:32 UTC, before e0e0013fc4) concluded 'skipped'. During the wipe window 5 scheduled fires (Oct 24 12:17/18:17, Oct 25 00:17/06:17/12:17 UTC) would have evaluated to the same skip; preflight.py is read-only ('No publishing performed'; no-op without QUEUE_MANIFEST_PATH). Operational consequence of the window: none. Left restored and enabled-gated as designed; no stale schedule disabled because none is active outside the approved workload.
- mp4 exclusion rule verified from the recorded task contract (user/parent do-not: 'no public hosting of staged/held reel material outside IG'); repo is public by user decision 2026-10-20 (reelsaga-uploader-repo-public), so committing staged mp4s would be public hosting of staged reel material - exclusion stands.
- Reproducibility of the 189 excluded mp4s: Tigris does NOT retain them (Oct 17 purge deleted all 101 staged files with user S). All 189 belong to completed/dropped/probe-only series (wrongdoor 29/29 complete, vows/beast/bitter/maid/ice complete or dropped, NetShort excluded, heiress/next probes finished); rules forbid repeating uploaded series, so nothing operational depends on them. If a re-upload is ever S'd, parts re-render from the DramaCPS source packs via the deterministic recipe (byte-exact reproduction proven Oct 24 Ambassador recovery). Pack host serving verified 2026-10-25 (range GET 206 on the new-series packs, which are sha-pinned in workflows).
