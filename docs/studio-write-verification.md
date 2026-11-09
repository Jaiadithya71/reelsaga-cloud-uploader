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
