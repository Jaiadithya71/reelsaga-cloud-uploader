# ReelSaga published-series history (canonical)

Single cross-series record so no future run re-proposes an already-published
title. Per-series detail lives in each series' *-release-journal.json /
*-public-catalog.json; the live index cards are at
https://reelsaga-index.vercel.app/ (21 cards as of 2026-11-05).

## Rule
Before proposing ANY "next series", check it against this file AND the live
Buffer sent-post history (organizationId 6adb4a329ef1e740831f7879, channel
6adb4d02778b240e2f9c6d48) by caption/character aliases. A missing memory is
not evidence of "not published".

## Completed / published runs (newest first)

| Series | Platform | Parts | Free eps | Run window (IST) | Evidence |
| --- | --- | --- | --- | --- | --- |
| The Star Princess He Betrayed (DramaCPS 807564) | IG | 23/23 | 8/8 | 2026-11-03 21:58 → 2026-11-04 22:24 | starprincess-release-journal.json (23 sent; 21 served-verified, E5P1/E5P2 served checks gated), starprincess-prepared-catalog.json; last https://www.instagram.com/reel/DfU7ksdAIqp/ |
| Frozen by My Fiancé, Adored by the Dragon King (DramaCPS 807545) | IG | 20/20 | 9/9 | 2026-11-02 23:44 → 2026-11-03 20:50 | frozen-release-journal.json (20 entries public_verified_cleaned), frozen-prepared-catalog.json |
| The Dragon King's True Heiress (DramaCPS 807565) | IG | 23 | 8 | 2026-11-01 → 2026-11-02 | heiress-release-journal.json, heiress-prepared-catalog.json |
| No One Gets Saved | IG | 18 | complete | → 2026-11-01 21:07 | Buffer captions "Betrayed after saving her classmates, Layla" |
| The Weakest Null Commands the Devil King! (DramaCPS 807571) | IG | 33/33 | 11/11 | 2026-10-29 15:51 → 2026-10-31 02:00 | null-release-journal.json instagram_run_closeout (parts_verified 33, last_actual_sent_at 2026-10-31T02:00:18.316+05:30); Buffer caption "At an academy where rank depends on the demon you command" (33 posts, 2026-10-29T10:21:49Z → 2026-10-30T20:30:18Z) |
| Call My Pups Bastards? They Are Royal Heirs! | IG | 34 | - | Oct 2026 | Buffer history |
| The Supreme Mage: This Time, I Choose My Family | IG | 17 | - | Oct 2026 | Buffer history |
| Beast Whisperer: I Hear Animals Talk | IG | 13 | - | Oct 2026 | Buffer history |
| Return of the Death's Ambassador | IG | ~26 | - | Oct 2026 | Buffer history |
| Always His Second Choice | IG | 18 (through E5P3) | partial, stopped | Oct 2026 | Buffer history |
| Stolen as a baby and raised by dragons (Caesar) | IG | 3 | - | Oct 2026 | Buffer history |
| The Blood Pact Game; Gone Before the Vows (31/31, complete Oct 6, both platforms); From F-Class Trash to Mech God; Wrong Door Right Girl; She Chose Her Lover. I Took Back My Empire.; Cast Me Out, Feed the Swarm; The Hidden Heiress; The Mute Heiress Speaks; My Robot Son will Save the World; A Love Left Unspoken; Don't Mess With That Airport Cleaner | IG | - | - | before/early Oct 2026 | index cards (pre-Buffer lane history) |

## Active run
- The Soldier's Journey Home (DramaCPS 807559, book 42000030015): IG
  3/26 parts public (E1P1, E1P2, E2P1; latest
  https://www.instagram.com/reelsaga3000/reel/DfWQUDsFCEX/).
  11 supplied free episodes; ordered hourly no-skip run.
  Evidence: soldier-release-journal.json and soldier-prepared-catalog.json.
  Per-series IG/skip-YT-check approval Nov5 08:31:38, original WhatsApp
  wamid.HBgMOTE3MzU4MjU4MjE2FQIAEhggQUMzQkMwRUJGMkM5RkQ2NEM4MUY1MTI5RENFOUNFREQA.
  YouTube hold lifted Nov9 00:22:58 ("Yes and s",
  wamid.HBgMOTE3MzU4MjU4MjE2FQIAEhggQUNFNTUyQUNCMDdBMTU2Q0U5QTVFNTQ5N0MwNkVBRDYA),
  restart approved both lanes.
  Pacing rule (owner, WhatsApp 2026-11-01 22:16:22 IST: "Upload much slower
  from now on, 1 per hour"; agent ack 22:16:31 "one post per hour, measured
  from each actual post"): at most ONE ReelSaga public post per hour across
  BOTH lanes, measured from the newest actual public post on either lane.
  Executable guard: release_spacing.py + release_preflight.py +
  .github/workflows/release-spacing-preflight.yml; tests
  tests/test_release_spacing.py. No newer owner instruction narrows it
  (user-message sweep Nov1-Nov9 2026-11-09).
  CORRECTION 2026-11-09: the restart below applied a stale >=30min guard;
  E1P1->E1P2 was +32min and E1P2->E2P1 +47min, breaching the 1/hour rule.
  Posts stay public unchanged (deleting/reposting would not undo the
  intervals); all future releases require >=60min from the newest actual
  public post on either lane.
  YT 3/26 parts public, all private-first probes with clean Studio claims,
  signed-in playback verified on each:
  E1P1 public 2026-11-09 02:02 IST
  https://www.youtube.com/shorts/TwCni7ipeKs ;
  E1P2 public 02:34 IST https://www.youtube.com/shorts/eqZxi4i5VaY ;
  E2P1 public 03:21 IST https://www.youtube.com/shorts/dPCcGLXUzdQ .
  E2P2 public 2026-11-09 08:35 IST (YT 4/26): ORIGINAL wording
  https://www.youtube.com/shorts/x-7dMTTpUns (item ep2-part2-v2, pinned
  original render sha 09155eb03c9a...9499). User approved the shown
  ORIGINAL version ("This is ok, post" 2026-11-09 08:07:49 IST,
  wamid.HBgMOTE3MzU4MjU4MjE2FQIAEhggQUM0M0MxRjY0MEVGNTc1RUNCQUQ0QTVBRDE0NDkzOTIA,
  replying to the original-clip question). Studio claims clean,
  playlist-added, signed-in playback verified (44.28s advancing).
  Superseded patched v1 candidate (BsS-sYfc9lg) retitled "(SUPERSEDED
  caption patch, do not publish)", kept private, never published.
  Spacing preflight: graph reader endpoint returned HTTP 502 x3
  (endpoint failure only); Buffer API untouched (saved provider cooldown
  until 2026-11-22). Manual equivalent live reads per main 08:29 ruling:
  YT last actual public E2P1 03:21 IST (API), IG last actual public E2P1
  2026-11-05T05:14:32Z (owner-profile time element) -> 60min shared floor
  satisfied before flip. Workflow preflight stays mandatory once the
  reader endpoint recovers.
  Playlist https://www.youtube.com/playlist?list=PLD5vEa-35ZMU (Date
  published oldest; 4 videos in story order). Late-claims recheck 03:21:
  all three clean.
  IG lane: E2P2 PUBLIC 2026-11-09 09:35 IST (IG 4/26):
  https://www.instagram.com/reelsaga3000/reel/Dfgbo9DAF3j/ via
  SocialChamp Bulk CSV (link-referenced media from Tigris presigned <=3h,
  deleted after landing; bucket clean). Same approved ORIGINAL render as
  YT. Verified live: AI-content label ON, Show-on-Feed ON, cover = real
  frame (not black), caption template matches E2P1 (affiliate link
  auto-shortened champ.ly -> 302 to r.reelsgo.tv/GFBBQsIQ1FBz, correct),
  playback advancing (44.2s). 60-min cross-lane guard kept (YT 08:35 ->
  IG 09:35).
  YT lane: E3P1 PRIVATE 2026-11-09 ~09:50 IST (video CYAKA8ESnC0, item
  ep3-part1-v1, pinned repaired render sha ffc5cc796bb6...c6e4d1,
  47473972 bytes; caption-defect repair under user repair authority
  2026-11-05 14:16 IST, observation-verified). Probe run 42561023158
  success on ubuntu-22.04 (ffmpeg-version-sensitive pins; 24.04 ffmpeg
  6.x produces different x264 bytes - staging pinned to 22.04).
  Studio claims check pending; public flip earliest >=60min after the
  latest actual post and only with clean claims + preflight.
  YT lane: E3P1 PUBLIC 2026-11-09 11:49:37 IST (YT 5/26):
  https://www.youtube.com/shorts/CYAKA8ESnC0 (publishDate
  2026-11-08T22:19:37-08:00). Claims re-verified clean immediately
  before flip. Signed-in playback verified (0.27->2.77s, dur 42.56);
  signed-OUT playback verified on a no-login browser profile
  (0.24->2.74s). Flip commit required the page-level Save after the
  visibility dialog (Done alone stages only); verified via anonymous
  playabilityStatus OK (calibrated: private = LOGIN_REQUIRED).
  60-min floor respected: IG actual 10:37:11 -> 11:49:37 = 72m26s.
  CORRECTION: E2P2 (x-7dMTTpUns) was found ABSENT from playlist
  PLD5vEa-35ZMU during the E3P1 flip (the 08:39 playlist-add had a
  visible "Undo changes" dirty state in its proof screenshot; the add
  never committed). Re-added and saved 11:52; playlist verified at 5
  videos (E1P1, E1P2, E2P1, E2P2, E3P1), sort Date published oldest.
  Next-post floor (both lanes): >= 12:49:37 IST (60min after exact
  YT actual 11:49:37).
  IG lane: E3P1 PUBLIC 2026-11-09 10:37:11 IST (IG 5/26):
  https://www.instagram.com/reelsaga3000/reel/DfgipZhDdCr/ via
  SocialChamp Bulk CSV (Tigris presigned <=3h, keys deleted after
  landing; bucket xfer/ empty). Scheduled 10:36 (moved +1min from 10:35:
  exact E2P2 actual taken_at=1794197150 = 09:35:50 IST, so 10:35:00
  would have shortened the 60-min floor to 59m10s). Verified live
  (taken_at=1794200831 = 10:37:11 IST): AI-content label ON, caption
  verified in composer and on live reel (Ad, hook, Episode 3 Part 1/2,
  affiliate champ.ly/XGRsxm9N -> 302 r.reelsgo.tv/GFBBQsIQ1FBz,
  hashtags), cover = real frame, playback advancing (42.52s duration,
  currentTime 6.75->9.25). Next-post floor: >=11:37:11 IST (60min after
  exact actual). Repair boundary respected: only 33.0-34.4s caption
  overlay; footage and original audio untouched (audio-preservation
  sha check passed in-runner).
  Story-order ceiling: no E3+ public release until E2P2 resolves.
  Zero spend, no paid unlocks.
  IG lane: E3P2 PUBLIC 2026-11-09 12:52:50 IST (IG 6/26):
  https://www.instagram.com/reelsaga3000/reel/DfgyHpNGZP6/ via
  SocialChamp Bulk CSV (Tigris presigned <=3h, keys xfer/e3p2.mp4 +
  xfer/e3p2-cover.jpg deleted after landing; bucket xfer/ verified
  empty). Scheduled 12:51 (floor: YT actual 11:49:37 + 60min =
  12:49:37). Verified live (taken_at=1794208970 = 12:52:50 IST,
  page time element 2026-11-09T07:22:50Z): AI-content label visible
  under username, caption verified on live reel (Ad, hook, Episode 3
  Part 2/2, affiliate champ.ly/XGRsxm9N -> 302 r.reelsgo.tv/GFBBQsIQ1FBz,
  hashtags), cover = real 2s frame, playback OK (video readyState 4,
  frames advancing). Composer switches persisted post-save re-open
  [Feed=true, Trial=false, MobileNotif=false, AI-generated=true].
  Next-post floor (both lanes): >=13:52:50 IST (60min after exact
  IG actual 12:52:50). Repair boundary respected: subtitle overlay
  only; footage and original audio untouched (pin-verified byte-exact
  57516662 bytes sha eb6567e6).
  YT lane: E3P2 PUBLIC 2026-11-09 13:56:44 IST (YT 6/26):
  https://www.youtube.com/shorts/z-_m8dmdtg8 (publishDate
  2026-11-09T00:26:44-08:00). Probe run 42582482305 success (full
  channel inventory 457 checked, no duplicate part, stop-control
  readback verified). Claims CLEAN re-verified immediately before flip
  (13:30 and 13:55:35, "No claims were found in this video"). Flip
  committed 13:56 via two-stage Studio write (visibility dialog Public
  + Done stages; page-level Save commits) and verified per
  docs/studio-write-verification.md: saved toast + reload (Undo changes
  disabled), anonymous playabilityStatus OK (calibration: private =
  LOGIN_REQUIRED), signed-OUT playback on no-login profile advancing
  (0 -> 2.43s, dur 42.5). 60-min floor respected: IG actual 12:52:50
  -> 13:56:44 = 63m54s. Playlist PLD5vEa-35ZMU: video was NOT
  auto-added by the probe upload; added via video-edit Playlists
  dialog + page Save, verified on the playlist page = 6 videos in
  story order (E1P1..E3P2). Next-post floor (both lanes): >=14:56:44
  IST (60min after exact YT actual 13:56:44).

  IG lane: E4P1 PUBLIC 2026-11-09 15:00:41 IST (IG 7/26):
  https://www.instagram.com/reelsaga3000/reel/DfhA1piFmjM/ via
  SocialChamp Bulk CSV (Tigris presigned <=3h; keys xfer/e4p1.mp4 +
  xfer/e4p1-cover.jpg retained until the E4P1 YT probe consumes the
  presigned URL, then deleted). Scheduled 14:46 (floor: YT actual
  13:56:44 + 60min = 14:56:44; slot 15:00). Subtitle gate: per-part
  check done (faster-whisper base.en transcript vs tesseract OCR of
  subtitle band fps=4 crop=880:320:100:1300, weak spots
  pixel-confirmed), soldier-subtitle-quality-gates.json ep4-part1
  approved, render pin byte-exact (52799456 bytes sha ad8eb6f5).
  Verified live (page time element 2026-11-09T09:30:41Z = 15:00:41
  IST): AI-content label visible under username, caption verified on
  live reel (Ad, hook, Episode 4 Part 1/2, affiliate
  champ.ly/XGRsxm9N -> 302 r.reelsgo.tv/GFBBQsIQ1FBz, hashtags),
  cover = real 2s subway frame, playback OK (video readyState 4).
  Composer switches persisted post-save re-open
  [Feed=true, Trial=false, MobileNotif=false, AI-generated=true].
  Composer note: bulk-created posts re-upload media from the URL on
  first Edit; Save during that upload fails with an "Oops... Please
  wait while we upload the media file" toast and nothing persists -
  save only after the upload completes and read the toast text.
  Next-post floor (both lanes): >=16:00:41 IST (60min after exact
  IG actual 15:00:41).
  YT lane: E4P1 PUBLIC 2026-11-09 16:20:31 IST (YT 7/26):
  https://www.youtube.com/shorts/oN2vHr4iQgU (publishDate
  2026-11-09T02:50:31-08:00). Recovery path, no re-upload: probe run
  42601314865 uploaded the private video then failed at playlist add
  (safe-failure scrubbed the step; instrumented re-run 42603076713
  proved the duplicate guard fail-closed: "Existing episode part,
  reconcile only", ledger resume do_not_create). Studio evidence:
  exactly one E4P1 video, Private, correct metadata, Claims CLEAN
  ("No claims were found in this video"). Playlist PLD5vEa-35ZMU add
  via video-edit Playlists dialog + page Save (committed 16:19,
  reload-verified chip persisted, Undo changes disabled). Flip Public
  16:20:31 via two-stage Studio write, verified per
  docs/studio-write-verification.md: "Changes saved" toast + reload
  (Visibility Public, Undo disabled), anonymous playabilityStatus OK,
  oembed 200. Playlist page verified = 7 videos E1P1..E4P1 story
  order. 60-min floor respected: IG actual 15:00:41 -> 16:20:31 =
  79m50s. Earlier probe failures: run 42595396867 stale duration
  assert (85.018 was Episode3's; Episode4.mp4 is 75.46s, fixed
  ad4e867), run 42598177580 raced an unlanded push (masked SSH
  failure; see docs/studio-write-verification.md push guard).
  Ledger reconcile to published via workflow pending (claim held
  from failed run 42601314865). Next-post floor (both lanes):
  >=17:20:31 IST (60min after exact YT actual 16:20:31).
## Dropped / blocked (do not revive without explicit user direction)
- Daddy's Regret - stopped (claims wave).
- The Divorced Billionaire Heiress - dropped, global block.
- Superhuman Maid - dropped by user.
- Soulbound by the Dark Lord - withdrawn (explicit content; two-pass screen).
- Golden Dragon - removed from index, never restored.

## Screened candidates
- (Frozen and Star Princess moved out: both screened, waived and started;
  see Completed table above.))

## Resolved decisions
- 2026-11-02 22:47 approval covered ONLY Weakest Null conditional on
  not-yet-published; the condition failed (already complete), so NO push
  happened and the approval is spent.
- Frozen start: own per-series waiver; published 2026-11-02 → 2026-11-03.
- Star Princess start: per-series waiver granted 2026-11-03 17:36:58 IST
  (series-only skip of private YT checks); supplied free run complete.
