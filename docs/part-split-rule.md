# Part split rule (standing user rule, do not weaken)

Parts are capped at about 55 seconds each. This is the user's standing rule
("~37-55 s parts"; "Long episodes get 4-5 parts capped ~55 s", 2026-09-28/29).
The 60 s figure is only YouTube's hard Shorts ceiling plus the music-claim
global-block risk above 60 s - it is NOT the approved part length.

Split algorithm for episode duration D seconds:
  n = ceil(D / 55)          # never round(D / 50.5); that produced 58.5 s parts
  part_len = D / n          # equal parts; first n-1 cuts rounded to 0.5 s,
                            # last part takes the remainder (see EP1 render probes)
  0.5 s fade in/out at every cut; fade-out st = part_len - 0.5 for that part.

Every per-part render must be sha-gated against the episode's render-probe
measurements before any upload, and the fade-out st must be recomputed per
part length (a cloned workflow with a stale st fails the gate - seen on
670982 EP1P5, 2026-10-25).
