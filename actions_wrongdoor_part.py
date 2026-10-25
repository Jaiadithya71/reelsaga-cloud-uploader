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
COUNTS={'1':4,'2':5,'3':4,'4':4,'5':3,'6':4,'7':5}
if EP not in COUNTS or not PART.isdigit() or not 1<=int(PART)<=COUNTS[EP]:raise RuntimeError('Unprepared Wrong Door Right Girl part')
MANIFEST=f'dramacps-wrongdoor-prepared/ep{EP}-part{PART}.json'

def validate(item,path):
    title=f"Wrong Door Right Girl - Episode {EP} Part {PART}/{COUNTS[EP]} | ReelShort"
    if item.get('id')!=f'dramacps-wrongdoor-ep{EP}-part{PART}-v1' or item.get('title')!=title:raise RuntimeError('Unexpected Wrong Door Right Girl item')
    if Path(path).stat().st_size!=item['bytes'] or hashlib.sha256(Path(path).read_bytes()).hexdigest()!=item['sha256']:raise RuntimeError('Media integrity mismatch')
    expected="Paige knocks on the wrong door and meets Talia, the cheerleading captain. A fake-girlfriend deal could help fund Paige's music dream, but campus gossip and real feelings complicate the plan.\n\nThis is only one piece of the story. The rest is waiting on the channel.\n\nWatch on ReelShort: https://r.reelsgo.tv/gJ9-dTiPfJ5E\nGet the ReelShort app: https://r.reelsgo.tv/RE4VVx_RfW7Q\n\n"+f"Full episode part {PART} of {COUNTS[EP]}.\nAffiliate links: I may earn a commission if you use them."
    if item.get('description')!=expected:raise RuntimeError('Approved description mismatch')
    if not item['description'].endswith(f'Full episode part {PART} of {COUNTS[EP]}.\nAffiliate links: I may earn a commission if you use them.'):raise RuntimeError('Disclosure mismatch')
    for link in ('https://r.reelsgo.tv/gJ9-dTiPfJ5E','https://r.reelsgo.tv/RE4VVx_RfW7Q'):
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
    stage="manifest"
    try:
        item=json.loads(Path(MANIFEST).read_text());path=f'dramacps-wrongdoor-prepared/ep{EP}-part{PART}.mp4';validate(item,path)
        stage="credentials_config"
        record=validated_record(os.environ.pop('REELSAGA_GOOGLE_CREDENTIALS',''));gh=os.environ.pop('GH_TOKEN','')
        stage="state_initialize"
        backend=GitHubState(Transport(lambda:gh,{'api.github.com'}),record['refresh_token']);backend.initialize()
        stage="state_probe"
        controls=Controls(backend,lambda:None);probe(backend,os.environ['GITHUB_RUN_ID'])
        stage="google_refresh"
        credential=GoogleCredentials(Store(record),GoogleTokenForms(),SCOPES);token=credential.access_token()
        api=Transport(lambda:token,{'www.googleapis.com'})
        stage="channel_identity"
        identity=checked(api('GET','https://www.googleapis.com/youtube/v3/channels',params={'part':'id','mine':'true'})).data
        if {x.get('id') for x in identity.get('items',[])}!={CHANNEL}:raise RuntimeError('Identity mismatch')
        stage="item_claim_read"
        if DurableLedger(backend).resume(item['id'],'youtube')!='unclaimed':raise RuntimeError('Item already claimed')
        stage="enable_control"
        controls.set_access(True,verified=True)
        stage="private_upload"
        result=run(backend,api,item,path)
        stage="stop_verify"
        controls.set_access(False)
        try:controls.require_enabled()
        except ControlError:pass
        else:raise RuntimeError('Stop did not block access')
        stage="checkpoint_readback"
        saved,_=backend.get(DurableLedger.key(item['id'],'youtube'))
        if saved.get('external_id')!=result['video_id']:raise RuntimeError('Checkpoint mismatch')
        result.update(checkpoint_video_id_verified=True,stop_control_readback_verified=True,access_enabled=False)
        print(json.dumps(result,sort_keys=True))
    except Exception:
        print('Safe failure stage: '+stage)
        print('Real-part upload stopped. Reconcile encrypted ledger and Studio before retry; secrets not shown.')
        raise SystemExit(1) from None
    finally:
        if controls is not None:
            try:controls.set_access(False)
            except Exception:
                print('STOP control write unconfirmed. No rerun; operator action required.')
                raise SystemExit(2) from None
if __name__=='__main__':main()
