"""One-time live encrypted checkpoint and stop-control test. No video operations."""
import json,os
from provision_actions import validated_record
from transport import Transport
from github_state import GitHubState,StateError
from controls import Controls,ControlError

def probe(backend,run_id):
    key='probe-'+run_id
    if not backend.compare_and_swap(key,None,{'value':1}):raise RuntimeError('Probe already claimed; stop')
    print('State stage: create acknowledged')
    record,old=backend.get(key)
    print('State stage: encrypted readback received')
    if record!={'value':1}:raise RuntimeError('Probe readback mismatch')
    if not backend.compare_and_swap(key,old,{'value':2}):raise RuntimeError('Probe update failed')
    print('State stage: update acknowledged')
    if backend.compare_and_swap(key,old,{'value':3}):raise RuntimeError('Stale write unexpectedly accepted')
    print('State stage: stale write rejected')
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
        if os.environ.get('STATE_READ_DIAGNOSTIC')=='true':
            value,version=backend.get('diagnostic-36699697319')
            if value!={'diagnostic':True}:raise RuntimeError('Diagnostic missing or mismatch')
            print('Existing encrypted record readback passed. No writes or controls changed.')
            return
        backend.initialize()
        if os.environ.get('STATE_DIAGNOSTIC_ONLY')=='true':
            key='diagnostic-'+os.environ['GITHUB_RUN_ID']
            if not backend.compare_and_swap(key,None,{'diagnostic':True}):raise RuntimeError('Diagnostic already claimed')
            print('State stage: diagnostic create acknowledged')
            value,version=backend.get(key)
            if value!={'diagnostic':True}:raise RuntimeError('Diagnostic mismatch')
            print('Diagnostic encrypted readback passed. No controls or videos changed.')
        else:
            print(json.dumps(probe(backend,os.environ['GITHUB_RUN_ID']),sort_keys=True))
    except StateError as exc:
        print('Safe state diagnostic: '+str(exc))
        print('No video uploaded; stopped without retry.')
        raise SystemExit(1) from None
    except Exception:
        print('Live state/stop probe failed. No video uploaded. No automatic retry; secrets not shown.')
        raise SystemExit(1) from None
if __name__=='__main__':main()
