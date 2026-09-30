"""Capacity plan, not a running schedule. Fail closed without live limits."""
PLANNED_YOUTUBE_UPLOADS=90
PLANNED_INSTAGRAM_POSTS=50
class CapacityError(RuntimeError):pass

def plan(platform,live_limit,used=0,attempts=0):
    if platform not in ('youtube','instagram') or not isinstance(live_limit,int) or live_limit<=0 or min(used,attempts)<0:
        raise CapacityError('Verified positive limit required')
    target=PLANNED_YOUTUBE_UPLOADS if platform=='youtube' else PLANNED_INSTAGRAM_POSTS
    remaining=max(0,live_limit-used-attempts)
    count=min(target,remaining)
    # Evenly spread a full plan; external state/checks still gate each item.
    return {'platform':platform,'target':target,'live_limit':live_limit,'remaining':remaining,'max_new_attempts':count,'spacing_seconds':86400//target,'active':False,'requires_live_identity':True,'requires_verified_canary':True}
