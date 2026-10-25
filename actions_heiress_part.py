"""One owner-approved real part, PRIVATE only, then stop for Studio review.

Manual dispatch only. Reruns never recreate a claimed upload.
"""
import hashlib,json,os
from pathlib import Path
from actions_canary import Store
from desktop_setup import CHANNEL,SCOPES
from provision_actions import validated_record
from credentials import GoogleCredentials
from transport import Transport,GoogleTokenForms
from github_state import GitHubState
from durable_state import DurableLedger
from controls import Controls,ControlError
from adapters import YouTube,checked
from actions_state_probe import probe

EP=os.environ.get('REELSAGA_EP','1')
PART=os.environ.get('REELSAGA_PART','1')
if EP not in tuple(str(n) for n in range(1,11)) or PART not in ('1','2') or (EP=='3' and PART!='1'):raise RuntimeError('Unexpected Heiress part')
MANIFEST=f'heiress-prepared/ep{EP}-part{PART}.json'

def validate(item,path):
    import re
    match=re.fullmatch(r'heiress-ep(10|[1-9])-part([12])-v1',item.get('id',''))
    if not match:raise RuntimeError('Unexpected bounded Heiress item')
    ep,part=match.groups();total=1 if ep=='3' else 2
    if int(part)>total or item.get('title')!=f"The Divorced Billionaire Heiress - Episode {ep} Part {part}/{total} | ReelShort":
        raise RuntimeError('Unexpected bounded title')
    if Path(path).stat().st_size!=item['bytes'] or hashlib.sha256(Path(path).read_bytes()).hexdigest()!=item['sha256']:
        raise RuntimeError('Media integrity mismatch')
    if not item['description'].endswith(f'Full episode part {part} of {total}.\nAffiliate links: I may earn a commission if you use them.'):
        raise RuntimeError('Disclosure mismatch')
    for link in ('https://r.reelsgo.tv/rTaSSpI2PZUP','https://r.reelsgo.tv/2M0nZm8Nvp0A'):
        if link not in item['description']:raise RuntimeError('Affiliate mismatch')

def run(backend,api,item,path):
    validate(item,path)
    controls=Controls(backend,lambda:None);ledger=DurableLedger(backend)
    if ledger.resume(item['id'],'youtube')!='unclaimed':raise RuntimeError('Item already claimed; reconcile only')
    controls.require_enabled()
    if not ledger.claim(item,'youtube'):raise RuntimeError('Claim conflict')
    checkpoint=lambda state,**kw:ledger.checkpoint(item['id'],'youtube',state,**kw)
    checkpoint('uncertain');controls.require_enabled()
    youtube=YouTube(api);session=youtube.start(item,item['bytes'],checkpoint)
    offset=0
    while offset<item['bytes']:
        controls.require_enabled()
        result=youtube.send_chunk(session,path,offset,checkpoint)
        if 'video_id' in result:break
        new_offset=result.get('offset',0)
        if not offset<new_offset<=item['bytes']:raise RuntimeError('Invalid server offset')
        offset=new_offset
    if 'video_id' not in result:raise RuntimeError('Saved session incomplete; no retry')
    video=checked(api('GET','https://www.googleapis.com/youtube/v3/videos',params={'part':'snippet,status,processingDetails','id':result['video_id']})).data
    rows=video.get('items',[])
    if len(rows)!=1:raise RuntimeError('Video readback missing')
    row=rows[0]
    if row['snippet']['channelId']!=CHANNEL or row['status']['privacyStatus']!='private' or row['snippet']['title']!=item['title'] or row['snippet']['description']!=item['description'] or row['status'].get('selfDeclaredMadeForKids') is not False:
        raise RuntimeError('Private metadata readback mismatch')
    return {'item_id':item['id'],'video_id':result['video_id'],'privacy':'private','channel_id':CHANNEL,'processing_status':row.get('processingDetails',{}).get('processingStatus','unknown'),'claims_verified':False,'studio_review_required':True,'public_publishing_enabled':False}

def main():
    controls=None
    try:
        item=json.loads(Path(MANIFEST).read_text());path=f'heiress-prepared/ep{EP}-part{PART}.mp4';validate(item,path)
        record=validated_record(os.environ.pop('REELSAGA_GOOGLE_CREDENTIALS',''));gh=os.environ.pop('GH_TOKEN','')
        backend=GitHubState(Transport(lambda:gh,{'api.github.com'}),record['refresh_token']);backend.initialize()
        controls=Controls(backend,lambda:None);probe(backend,os.environ['GITHUB_RUN_ID'])
        credential=GoogleCredentials(Store(record),GoogleTokenForms(),SCOPES);token=credential.access_token()
        api=Transport(lambda:token,{'www.googleapis.com'})
        identity=checked(api('GET','https://www.googleapis.com/youtube/v3/channels',params={'part':'id','mine':'true'})).data
        if {x.get('id') for x in identity.get('items',[])}!={CHANNEL}:raise RuntimeError('Identity mismatch')
        if DurableLedger(backend).resume(item['id'],'youtube')!='unclaimed':raise RuntimeError('Item already claimed')
        controls.set_access(True,verified=True)
        result=run(backend,api,item,path)
        controls.set_access(False)
        try:controls.require_enabled()
        except ControlError:pass
        else:raise RuntimeError('Stop did not block access')
        saved,_=backend.get(DurableLedger.key(item['id'],'youtube'))
        if saved.get('external_id')!=result['video_id']:raise RuntimeError('Checkpoint mismatch')
        result.update(checkpoint_video_id_verified=True,stop_control_readback_verified=True,access_enabled=False)
        print(json.dumps(result,sort_keys=True))
    except Exception:
        print('Real-part upload stopped. Reconcile encrypted ledger and Studio before retry; secrets not shown.')
        raise SystemExit(1) from None
    finally:
        if controls is not None:
            try:controls.set_access(False)
            except Exception:
                print('STOP control write unconfirmed. No rerun; operator action required.')
                raise SystemExit(2) from None
if __name__=='__main__':main()
