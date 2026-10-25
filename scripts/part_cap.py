"""ReelSaga canonical part-length cap. SINGLE enforcement point - every
render-probe / upload workflow must use these functions, never re-hardcode.

Approved scope (raw evidence, WhatsApp):
  2026-10-15 18:33:54 IST agent: "Root cause on the Pets block: parts were
    ~80s, over the ~60s music-claim threshold. Robot's ~55s parts only ever
    got partial claims. Going forward parts are hard-capped at ~55s. S to start?"
  2026-10-15 18:34:35 IST user: "S"

The approved cap is "~55s" - approximate in the user's approved text itself,
its purpose being to stay safely under the ~60s music-claim global-block
threshold. It is NOT a 55.00 invariant. Operationalized fail-closed as:
  TARGET      55.0   default split aims at or below this (n = ceil(D/55))
  HARD_GATE   56.0   any computed part above this fails (58.5s-class bug fails)
  MEASURED    56.05  ffprobe-measured rendered duration above this fails
  DRIFT        0.6   measured vs requested drift above this fails
The 56.0 hard gate is implementation tolerance for approx-55 parts (e.g.
55.397 s from equal-splitting), NOT a new limit to aim for. Splits always use
the target-55 default; no per-episode part-count overrides.
"""
import math

TARGET = 55.0
HARD_GATE = 56.0
MEASURED_GATE = 56.05
DRIFT = 0.6
FADE = 0.5


def compute_parts(dur):
    """Equal-split parts for episode duration dur (seconds).
    Returns [(part_no, ss_str, t_str), ...]; raises SystemExit on cap breach."""
    n = max(1, math.ceil(dur / TARGET))
    step = dur / n
    cuts = [round(i * step * 2) / 2 for i in range(n)]
    parts = []
    for i in range(n):
        ss = cuts[i]
        t = round(dur - ss, 3) if i == n - 1 else round(cuts[i + 1] - ss, 3)
        if t > HARD_GATE:
            raise SystemExit('Part length cap exceeded: ' + repr(t))
        if t - FADE <= 0:
            raise SystemExit('Invalid fade-out start for part ' + str(i + 1))
        parts.append((i + 1, repr(ss), repr(t)))
    return parts


def gate_measured(measured, requested):
    """Fail-closed check of one rendered part's ffprobe duration."""
    if measured > MEASURED_GATE:
        raise SystemExit('Measured part duration over cap: ' + repr(measured))
    if abs(measured - requested) > DRIFT:
        raise SystemExit('Measured duration drift vs requested: '
                         + repr(measured) + ' vs ' + repr(requested))
