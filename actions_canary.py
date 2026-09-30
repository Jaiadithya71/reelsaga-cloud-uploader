"""Exactly one synthetic PRIVATE canary. Owner approval Sep30 Run.

No batch, public switch, existing series media, Drive, artifact or retry.
"""
import json,os
from pathlib import Path
from desktop_setup import CHANNEL,SCOPES
from provision_actions import validated_record
from credentials import GoogleCredentials
from transport import Transport,GoogleTokenForms
from github_state import GitHubState
from durable_state import DurableLedger
from controls import Controls,ControlError
from adapters import YouTube,checked
from actions_state_probe import probe

ITEM={'id':'owner-private-canary-20260930-v1',
      'title':'ReelSaga private upload test - 2026-09-30',
      'description':'Private technical upload test. Synthetic test pattern only. Not a story episode.'}
class Store:
    def __init__(self,record):self.record=record
    def read(self):return self.record

def run(backend,api,path):
    controls=Controls(backend,lambda:None)
    ledger=DurableLedger(backend)
    # Reruns only report/reconcile state; never a second video or silent enable.
    state=ledger.resume(ITEM['id'],'youtube')
    if state!='unclaimed':raise RuntimeError('Canary already claimed; reconcile only')
    controls.require_enabled()  # Enabled solely for this dispatched, approved canary.
    if not ledger.claim(ITEM,'youtube'):raise RuntimeError('Canary claim conflict')
    youtube=YouTube(api)
    checkpoint=lambda state,**kw:ledger.checkpoint(ITEM['id'],'youtube',state,**kw)
    controls.require_enabled()
    checkpoint('uncertain')  # Persist uncertainty BEFORE creating a session.
    session=youtube.start(ITEM,Path(path).stat().st_size,checkpoint)
    controls.require_enabled()
    result=youtube.send_chunk(session,path,0,checkpoint)
    if 'video_id' not in result:raise RuntimeError('Canary incomplete; saved session, no retry')
    video=checked(api('GET','https://www.googleapis.com/youtube/v3/videos',params={
        'part':'snippet,status,processingDetails','id':result['video_id']})).data
    rows=video.get('items',[])
    if len(rows)!=1 or rows[0].get('snippet',{}).get('channelId')!=CHANNEL or rows[0].get('status',{}).get('privacyStatus')!='private':
        raise RuntimeError('Canary readback mismatch')
    return {'video_id':result['video_id'],'privacy':'private','channel_id':CHANNEL,
            'processing_status':rows[0].get('processingDetails',{}).get('processingStatus','unknown'),
            'public_publishing_enabled':False}

def main():
    backend=None;controls=None
    try:
        record=validated_record(os.environ.pop('REELSAGA_GOOGLE_CREDENTIALS',''))
        gh=os.environ.pop('GH_TOKEN','')
        backend=GitHubState(Transport(lambda:gh,{'api.github.com'}),record['refresh_token'])
        backend.initialize()
        controls=Controls(backend,lambda:None)
        # Live probe must have completed this session before enabling the canary.
        probe(backend,os.environ['GITHUB_RUN_ID'])
        credential=GoogleCredentials(Store(record),GoogleTokenForms(),SCOPES)
        token=credential.access_token()
        api=Transport(lambda:token,{'www.googleapis.com'})
        identity=checked(api('GET','https://www.googleapis.com/youtube/v3/channels',params={'part':'id','mine':'true'}))
        if {x.get('id') for x in identity.data.get('items',[])}!={CHANNEL}:raise RuntimeError('Identity mismatch')
        if DurableLedger(backend).resume(ITEM['id'],'youtube')!='unclaimed':raise RuntimeError('Canary already claimed')
        controls.set_access(True,verified=True)
        result=run(backend,api,'canary.mp4')
        controls.set_access(False)
        try:controls.require_enabled()
        except ControlError:pass
        else:raise RuntimeError('Stop readback did not block access')
        saved,_=backend.get(DurableLedger.key(ITEM['id'],'youtube'))
        if not saved or saved.get('external_id')!=result['video_id']:
            raise RuntimeError('Saved video checkpoint mismatch')
        result['checkpoint_video_id_verified']=True
        result['stop_control_readback_verified']=True
        result['access_enabled']=False
        print(json.dumps(result,sort_keys=True))
    except Exception:
        print('Private canary stopped. Check encrypted ledger; no automatic retry; secrets not shown.')
        raise SystemExit(1) from None
    finally:
        if controls is not None:
            try:controls.set_access(False)
            except Exception:
                print('STOP control write was not confirmed. Do not rerun; operator action required.')
                raise SystemExit(2) from None
if __name__=='__main__':main()
