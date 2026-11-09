"""ReelSaga cross-lane public-release pacing guard. Fail closed.

Owner rule, verbatim (WhatsApp, 2026-11-01 22:16:22 IST):
    user:  "Upload much slower from now on, 1 per hour"
    agent: "I'll slow ReelSaga to one post per hour, measured from each actual post."

=> At most ONE ReelSaga public post per hour across BOTH lanes (youtube and
instagram). Spacing is measured from the most recent ACTUAL public post on
either lane, whichever is newest. A lane whose last actual public time is
unknown blocks the release; a lane live-verified to have no public posts yet
does not.

2026-11-09 correction: the YT restart applied a stale 30-minute guard and
breached this rule (E1P1 public 02:02 IST, E1P2 02:34 IST +32min, E2P1
03:21 IST +47min). Existing public posts stay unchanged; this module is the
executable 60-minute guard for every release from now on.
"""
import datetime

MIN_PUBLIC_SPACING = datetime.timedelta(hours=1)
LANES = ('youtube', 'instagram')


class SpacingError(RuntimeError):
    pass


def _aware(t, lane):
    if not isinstance(t, datetime.datetime) or t.tzinfo is None or t.tzinfo.utcoffset(t) is None:
        raise SpacingError('Unusable %s timestamp' % lane)
    return t


def evaluate(now, last_public_at):
    """Decide whether a public release may happen at ``now``.

    ``last_public_at`` maps each lane to an aware datetime of its last actual
    public post, or None when a live read verified the lane has no public
    posts. A missing lane key is unknown state and fails closed.
    """
    _aware(now, 'now')
    missing = [lane for lane in LANES if lane not in last_public_at]
    if missing:
        raise SpacingError(
            'Last actual public time unknown for %s; live read required before any release'
            % ','.join(missing))
    known = [(lane, _aware(t, lane)) for lane, t in last_public_at.items() if t is not None]
    if not known:
        return {'allowed': True, 'earliest': None, 'newest_last_public': None, 'newest_lane': None}
    lane, newest = max(known, key=lambda p: p[1])
    if newest > now:
        raise SpacingError('Last public time is in the future; clock disagreement')
    earliest = newest + MIN_PUBLIC_SPACING
    return {'allowed': now >= earliest, 'earliest': earliest,
            'newest_last_public': newest, 'newest_lane': lane}


def require_release(now, last_public_at):
    decision = evaluate(now, last_public_at)
    if not decision['allowed']:
        raise SpacingError(
            'Minimum 1-hour cross-lane spacing unmet; earliest %s'
            % decision['earliest'].isoformat())
    return decision
