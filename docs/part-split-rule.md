# Part split rule (standing user rule, do not weaken)

Parts are capped at about 55 seconds each. Approved scope, raw evidence
(WhatsApp):

  2026-10-15 18:33:54 IST agent: "Root cause on the Pets block: parts were
    ~80s, over the ~60s music-claim threshold. Robot's ~55s parts only ever
    got partial claims. Going forward parts are hard-capped at ~55s. S to
    start?"
  2026-10-15 18:34:35 IST user: "S"

The cap is "~55s" - approximate in the approved text itself. Its purpose is to
stay safely under the ~60s music-claim global-block threshold; it is NOT a
55.00-second invariant. (Earlier doc versions quoted "~37-55 s parts" and
"4-5 parts capped ~55 s" dated 2026-09-28/29; those strings are not
recoverable as user originals and are no longer cited.)

The 60 s figure is only YouTube's hard Shorts ceiling plus the music-claim
global-block risk near it - it is NOT the approved part length.

Split algorithm for episode duration D seconds:
  n = ceil(D / 55)          # default; never round(D / 50.5) - that produced
                            # 58.5 s parts
  part_len = D / n          # equal parts; first n-1 cuts rounded to 0.5 s,
                            # last part takes the remainder
  A per-episode user-approved caption that fixes the part count (e.g. an
  approved "Part N/3" template) may override n; the resulting parts must
  still pass the hard gate below. Example: 670995 EP1 (166.191 s, approved
  Part N/3 caption) renders 3 x 55.397 s - inside the approved approx cap.

  0.5 s fade in/out at every cut; fade-out st = part_len - 0.5 for that part.

Every per-part render must be sha-gated against the episode's render-probe
measurements before any upload, and the fade-out st must be recomputed per
part length (a cloned workflow with a stale st fails the gate - seen on
670982 EP1P5, 2026-10-25).

Executable enforcement (fail-closed, docs alone are not prevention):
- SINGLE enforcement point: scripts/part_cap.py (TARGET 55.0, HARD_GATE 56.0,
  MEASURED_GATE 56.05, DRIFT 0.6). Every render-probe workflow imports
  compute_parts()/gate_measured() from it; never re-hardcode thresholds in a
  workflow. A computed part above 56.0 s or an ffprobe-measured render above
  56.05 s aborts the workflow. 55.4 s-class approx-55 parts pass; 58.5 s-class
  violations fail.
- Private-upload workflows must never be generated for a split that has not
  passed those gates; wrong-split workflow files are removed, not kept.
