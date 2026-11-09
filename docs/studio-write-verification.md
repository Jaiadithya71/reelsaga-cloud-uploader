# Studio write verification protocol (regression guard, added 2026-11-09)

YouTube Studio writes are TWO-STAGE. Treating a staged change as committed
caused two real incidents on 2026-11-09: the E3P1 visibility flip showed
"Public" after the dialog but was never published, and E2P2's 08:39
playlist-add was claimed in closeout while never committed.

Rules for EVERY Studio write (visibility, playlist, title, description,
thumbnail, audience):

1. Dialog buttons ("Done", "Select") only STAGE. The page-level Save
   commits. If the "Undo changes" button is ENABLED, there are uncommitted
   changes - the write has NOT landed.
2. After clicking Save, require the "Changes saved" toast AND a reload or
   re-read showing the new state with "Undo changes" DISABLED.
3. Visibility flips additionally require the anonymous check:
   fetch the watch page without cookies and read
   "playabilityStatus":{"status":...} - OK means public,
   LOGIN_REQUIRED means still private (calibrated 2026-11-09). Never trust
   the signed-in Studio label alone.
4. Playlist adds additionally require listing the playlist page and
   confirming the video id is present and the count incremented.
5. A closeout or report may only cite state verified by steps 2-4, with the
   verification method named. A screenshot showing an enabled "Undo changes"
   button is proof of an UNCOMMITTED state, not of success.

## Probe playlist-add pattern (added 2026-11-09 after 403 diagnosis)

playlistItems.insert requires the auth/youtube(/force-ssl) scope; the
upload-queue grant carries only youtube.upload + youtube.readonly, so the
API playlist add deterministically fails 403 insufficientPermissions
(diagnostic run 42615266141, 5/5). Decision (main 2026-11-09 17:51):
no OAuth widening. Probe scripts therefore:

1. Never call playlistItems.insert. Playlist membership is set at the
   Studio flip closeout (video-edit Playlists dialog + page Save) and
   verified per rules 2-4 above on every flip.
2. Checkpoint ready_for_review after a verified private upload and print
   an explicit upload success result with playlist_pending set.
3. On rerun, a channel title hit with a matching ledger record
   (private_locked/ready_for_review/published) prints an explicit
   already_uploaded result and exits 0; a title hit WITHOUT ledger proof
   still fails closed (reconcile only).

## Push and dispatch verification (added 2026-11-09 after masked-push incident)

A push is not done until read back from the remote:

1. Push with `GIT_SSH_COMMAND="ssh -i <deploy-key> -o IdentitiesOnly=yes"` set in
   the same shell; without it ssh fails with "Permission denied (publickey)"
   and piping to `tail` can mask the failure behind a harmless-looking line.
2. Verify the push landed: `git fetch origin main && git rev-parse origin/main`
   must equal the new local HEAD. Never trust exit codes piped through tail.
3. Dispatch workflows only AFTER the readback matches; a same-second dispatch can
   resolve main to the pre-push commit (run 42598177580 ran stale sha 8fc080f).
4. After dispatch, confirm the run's `head_sha` equals the expected commit
   before treating the run as evidence for the new code.
