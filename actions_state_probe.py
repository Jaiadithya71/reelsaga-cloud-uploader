"""One-time live encrypted checkpoint and stop-control test. No video operations."""
import json,os
from provision_actions import validated_record
from transport import Transport
from github_state import GitHubState
from controls import Controls,ControlError

def probe(backend,run_id):
    key='probe-'+run_id
    if not backend.compare_and_swap(key,None,{'value':1}):raise RuntimeError('Probe already claimed; stop')
    record,old=backend.get(key)
    if record!={'value':1}:raise RuntimeError('Probe readback mismatch')
    if not backend.compare_and_swap(key,old,{'value':2}):raise RuntimeError('Probe update failed')
    if backend.compare_and_swap(key,old,{'value':3}):raise RuntimeError('Stale write unexpectedly accepted')
    controls=Controls(backend,lambda:None)
    controls.set_access(False)
    try:controls.require_enabled()
    except ControlError:pass
    else:raise RuntimeError('Disabled control allowed access')
    try:
        controls.set_access(True,verified=True)
        controls.require_enabled()
    finally:
        controls.set_access(False)
    try:controls.require_enabled()
    except ControlError:pass
    else:raise RuntimeError('Stop control did not block access')
    return {'encrypted_state_readback':True,'stale_write_rejected':True,
            'stop_control_verified':True,'access_enabled':False,'video_uploaded':False}

def main():
    try:
        record=validated_record(os.environ.pop('REELSAGA_GOOGLE_CREDENTIALS',''))
        token=os.environ.pop('GH_TOKEN','')
        api=Transport(lambda:token,{'api.github.com'})
        backend=GitHubState(api,record['refresh_token'])
        backend.initialize()
        print(json.dumps(probe(backend,os.environ['GITHUB_RUN_ID']),sort_keys=True))
    except Exception:
        print('Live state/stop probe failed. No video uploaded. No automatic retry; secrets not shown.')
        raise SystemExit(1) from None
if __name__=='__main__':main()
