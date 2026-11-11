"""One privately prepared promo, PRIVATE only, then stop for Studio review.

Manual dispatch only. Reruns never recreate a claimed upload.
"""
import hashlib,json,os,pathlib
from pathlib import Path
from actions_canary import Store
from desktop_setup import CHANNEL,SCOPES
from provision_actions import validated_record
from credentials import GoogleCredentials
from transport import Transport,GoogleTokenForms
from quarantine_state import QuarantineState
from durable_state import DurableLedger
from controls import Controls,ControlError
from adapters import YouTube,checked
from actions_state_probe import probe

import requests,subprocess
assert os.environ['SOLDIER_EP']=='athena2p2'
u='https://outin-c6b1636ee48611f0bf9400163e01d238.oss-us-west-1.aliyuncs.com/original/workflow/151a6b30-1a1aad52062-0005-9573-534-c9280.mp4'
r=requests.get(u,timeout=60);r.raise_for_status();Path('source.mp4').write_bytes(r.content)
assert hashlib.sha256(r.content).hexdigest()=='d3db1bd44833ffd2fa2e66c8b134e0ee896c2079c88f8c49a5cbb38c992ad3f9'
meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json','source.mp4']));v=next(x for x in meta['streams'] if x['codec_type']=='video');assert (v['width'],v['height'])==(1080,1920);assert abs(float(meta['format']['duration'])-121.344)<.1
subprocess.run(['ffmpeg','-v','error','-i','source.mp4','-f','null','-'],check=True)
subprocess.run(['ffmpeg','-v','error','-filter_threads','1','-ss','35','-i','source.mp4','-t','48','-vf','fade=t=in:st=0:d=0.5,fade=t=out:st=47.5:d=0.5','-af','afade=t=in:st=0:d=0.5,afade=t=out:st=47.5:d=0.5','-c:v','libx264','-threads:v','2','-preset','ultrafast','-crf','18','-c:a','aac','-b:a','192k','-movflags','+faststart','-y','p2.mp4'],check=True)
subprocess.run(['ffmpeg','-v','error','-i','p2.mp4','-f','null','-'],check=True)
assert hashlib.sha256(Path('p2.mp4').read_bytes()).hexdigest()=='37702bc93afdfd833aff333c76aafd85f2d526da5d3d50c8cf3c20cdc37d4aea'
gate=json.loads(Path('athena-subtitle-quality-gates.json').read_text())['parts']['yourchannel-athena829263-ep2-part2-v1']
assert gate['whole_part_release_ready'] and gate['approved_render_sha256']=='37702bc93afdfd833aff333c76aafd85f2d526da5d3d50c8cf3c20cdc37d4aea'
from scripts.part_cap import compute_parts,gate_measured
assert len(compute_parts(121.344))==3
render_meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_format','-of','json','p2.mp4']))
gate_measured(float(render_meta['format']['duration']),48)
data=Path('p2.mp4').read_bytes()
item={'id': 'yourchannel-athena829263-ep2-part2-v1', 'episode': 2, 'part': 2, 'title': 'The Outcast Who Called Down Athena - Episode 2 Part 2/3 | YourChannel', 'description': "Ad\n\nAthena's signal has reached the Federation. Nova's bullies still think she's powerless, but her public rating could change everything.\n\nThe Outcast Who Called Down Athena | Episode 2 Part 2/3\nThis is only one piece of the story. The rest is waiting on the channel.\n\nWatch the original on YourChannel: https://r.reelsgo.tv/SyqGbe__100g\n#TheOutcastWhoCalledDownAthena #AIDrama #YourChannel #ReelSaga", 'file': 'athena-e2p2.mp4', 'source_start': 35, 'source_end': 83, 'privacy': 'private', 'approval_required': True, 'bytes': 82067705, 'sha256': '37702bc93afdfd833aff333c76aafd85f2d526da5d3d50c8cf3c20cdc37d4aea'}
if len(data)!=item['bytes'] or hashlib.sha256(data).hexdigest()!=item['sha256']:raise RuntimeError('Render differs from catalog pinned part; fail closed')
Path('athena.json').write_text(json.dumps(item));MANIFEST='athena.json'

def validate(item,path):
    expected=json.loads(Path(MANIFEST).read_text())
    if item!=expected:raise RuntimeError("Unexpected item")
    if Path(path).stat().st_size!=item["bytes"] or hashlib.sha256(Path(path).read_bytes()).hexdigest()!=item["sha256"]:raise RuntimeError("Media integrity mismatch")
    if item.get("privacy")!="private":raise RuntimeError("Private gate missing")

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
    checkpoint('ready_for_review', external_id=result['video_id'])
    # Playlist membership is set at the Studio flip closeout: playlistItems.insert
    # requires auth/youtube scope this grant does not have (403 insufficientPermissions,
    # diagnosed run 42615266141). Never retry the API add here.
    return {'item_id':item['id'],'upload':'success','video_id':result['video_id'],'privacy':'private','channel_id':CHANNEL,'processing_status':row.get('processingDetails',{}).get('processingStatus','unknown'),'playlist_pending':'PLOa3xTBfOOsk','playlist_via':'studio_flip_closeout_oauth_scope_gap','claims_verified':False,'studio_review_required':True,'public_publishing_enabled':False}

def main():
    controls=None
    stage="manifest"
    try:
        item=json.loads(Path(MANIFEST).read_text());path='p2.mp4';validate(item,path)
        stage="credentials_config"
        record=validated_record(os.environ.pop('REELSAGA_GOOGLE_CREDENTIALS',''));gh=os.environ.pop('GH_TOKEN','')
        stage="state_initialize"
        stable=os.environ.pop('REELSAGA_LEDGER_KEY','')
        if len(stable)<48:raise RuntimeError('Stable key missing')
        backend=QuarantineState(Transport(lambda:gh,{'api.github.com'}),stable);backend.initialize()
        stage="state_probe"
        controls=Controls(backend,lambda:None);import time as _pt
        _ptransient=('readback','unsettled','unconfirmed')
        _pa=0
        while True:
            _pa+=1
            try:
                probe(backend,os.environ['GITHUB_RUN_ID']+'-ep'+os.environ['SOLDIER_EP']+'-a'+str(_pa))
                break
            except Exception as _e:
                _m=str(_e)
                if (_m=='Probe update failed' or any(x in _m for x in _ptransient)) and _pa<3:
                    print('RETRY state_probe attempt '+str(_pa)+' transient: '+_m[:120]+'; backoff 75s',flush=True)
                    _pt.sleep(75)
                    continue
                raise
        stage="google_refresh"
        credential=GoogleCredentials(Store(record),GoogleTokenForms(),SCOPES);token=credential.access_token()
        api=Transport(lambda:token,{'www.googleapis.com'})
        stage="channel_identity"
        identity=checked(api('GET','https://www.googleapis.com/youtube/v3/channels',params={'part':'id','mine':'true'})).data
        if {x.get('id') for x in identity.get('items',[])}!={CHANNEL}:raise RuntimeError('Identity mismatch')
        stage="complete_channel_duplicate_read"
        def _dupread():
            c=checked(api('GET','https://www.googleapis.com/youtube/v3/channels',params={'part':'contentDetails','mine':'true'})).data
            playlist=c['items'][0]['contentDetails']['relatedPlaylists']['uploads']
            page=None;seen=set();ids=[];total=None
            while True:
                q={'part':'contentDetails','playlistId':playlist,'maxResults':'50'}
                if page:q['pageToken']=page
                data=checked(api('GET','https://www.googleapis.com/youtube/v3/playlistItems',params=q)).data
                if total is None:total=data['pageInfo']['totalResults']
                elif data['pageInfo']['totalResults']!=total:raise RuntimeError('Channel inventory changed')
                ids.extend(x['contentDetails']['videoId'] for x in data.get('items',[]))
                page=data.get('nextPageToken')
                if not page:break
                if page in seen:raise RuntimeError('Channel pagination loop')
                seen.add(page)
            ids=list(dict.fromkeys(ids))
            for n in range(0,len(ids),50):
                data=checked(api('GET','https://www.googleapis.com/youtube/v3/videos',params={'part':'snippet,status','id':','.join(ids[n:n+50])})).data
                if {v['id'] for v in data.get('items',[])}!=set(ids[n:n+50]):raise RuntimeError('Incomplete channel metadata')
                for video in data.get('items',[]):
                    snippet=video['snippet']
                    if snippet['channelId']!=CHANNEL:raise RuntimeError('Channel mismatch')
                    if snippet['title']==item['title']:raise RuntimeError('Existing episode part, reconcile only')
            return len(ids)
        _da=0
        _dup=None
        while True:
            _da+=1
            try:
                _count=_dupread()
                break
            except Exception as _e:
                _m=str(_e)
                if 'Existing episode part' in _m:_dup=True;break
                if 'Channel mismatch' in _m:raise
                if _da<3:
                    print('RETRY duplicate_read attempt '+str(_da)+' transient: '+_m[:120]+'; backoff 75s',flush=True)
                    _pt.sleep(75)
                    continue
                raise
        if _dup:
            stage="item_claim_read"
            saved,_=backend.get(DurableLedger.key(item['id'],'youtube'))
            if saved and saved.get('external_id') and saved.get('state') in ('private_locked','ready_for_review','published'):
                print(json.dumps({'already_uploaded':True,'video_id':saved['external_id'],'ledger_state':saved['state'],'playlist_pending':saved['state']=='ready_for_review','duplicate_upload_prevented':True},sort_keys=True))
                open(os.environ["GITHUB_STEP_SUMMARY"],"a").write("## Private Athena EP2P2 episode probe: already uploaded (explicit)\n\n```json\n"+json.dumps({'already_uploaded':True,'video_id':saved['external_id'],'ledger_state':saved['state']},indent=2)+"\n```\n")
                return
            raise RuntimeError('Existing episode part without ledger proof; reconcile only')
        print(json.dumps({'complete_channel_inventory_checked':True,'inventory_video_count':_count,'duplicate_part_found':False}))
        stage="item_claim_read"
        if DurableLedger(backend).resume(item['id'],'youtube')!='unclaimed':raise RuntimeError('Item already claimed')
        stage="enable_control"
        controls.set_access(True,verified=True)
        stage="private_upload"
        import time
        for attempt in range(5):
            c,_=backend.get("account-control")
            if c and c.get("enabled") is True:break
            if attempt<4:time.sleep(3)
        else:raise RuntimeError("Control readback unsettled")
        result=run(backend,api,item,path)
        stage="stop_verify"
        controls.set_access(False)
        import time
        for _ in range(5):
            control,_=backend.get('account-control')
            if control and control.get('enabled') is False:break
            time.sleep(3)
        else:raise RuntimeError('Stop readback did not settle')
        try:controls.require_enabled()
        except ControlError:pass
        else:raise RuntimeError('Stop did not block access')
        stage="checkpoint_readback"
        saved,_=backend.get(DurableLedger.key(item['id'],'youtube'))
        if saved.get('external_id')!=result['video_id']:raise RuntimeError('Checkpoint mismatch')
        result.update(checkpoint_video_id_verified=True,stop_control_readback_verified=True,access_enabled=False)
        print(json.dumps(result,sort_keys=True))
        open(os.environ["GITHUB_STEP_SUMMARY"],"a").write("## Private Athena EP2P2 episode probe verified\n\n```json\n"+json.dumps(result,indent=2)+"\n```\n")
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