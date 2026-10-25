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
- Restored workflow triggers audited: only .github/workflows/queue.yml has a cron schedule ('17 */6 * * *'); it was absent from main during the broken window (no scheduled fires could occur while its file was missing - verify with runs API if needed).
