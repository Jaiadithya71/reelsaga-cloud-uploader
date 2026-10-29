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

import requests,io,zipfile,subprocess
e=int(os.environ['NULL_EP']);assert e==1,'First episode only until Studio qualification'
durations={1:140.459002};cuts={1:50.32};parts={1:3}
u='https://cps-distr.ikyuedu.com/distribution/11/DramaBox资源包-42000029033-19b48bade6b3906f40a7fafe28d1b268.zip'
s=requests.Session();response=s.head(u,timeout=30);response.raise_for_status();size=int(response.headers['Content-Length'])
class Remote(io.RawIOBase):
 def __init__(self):self.pos=0
 def seekable(self):return True
 def readable(self):return True
 def tell(self):return self.pos
 def seek(self,o,w=0):self.pos=o if w==0 else self.pos+o if w==1 else size+o;return self.pos
 def read(self,n=-1):
  if n<0:n=size-self.pos
  if not n:return b''
  r=s.get(u,headers={'Range':f'bytes={self.pos}-{min(size-1,self.pos+n-1)}'},timeout=40);r.raise_for_status();assert r.status_code==206;self.pos+=len(r.content);return r.content
z=zipfile.ZipFile(Remote());member=f'Episode{e}.mp4';assert member in z.namelist();Path('source.mp4').write_bytes(z.read(member))
meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json','source.mp4']));v=next(x for x in meta['streams'] if x['codec_type']=='video');assert (v['width'],v['height'])==(1080,1920);assert abs(float(meta['format']['duration'])-durations[e])<.1
subprocess.run(['ffmpeg','-v','error','-i','source.mp4','-f','null','-'],check=True)
subprocess.run(['ffmpeg','-v','error','-filter_threads','1','-i','source.mp4','-t',str(cuts[e]),'-vf',f'fade=t=in:st=0:d=0.5,fade=t=out:st={cuts[e]-.5}:d=0.5','-af',f'afade=t=in:st=0:d=0.5,afade=t=out:st={cuts[e]-.5}:d=0.5','-c:v','libx264','-threads:v','3','-preset','ultrafast','-crf','18','-c:a','aac','-b:a','192k','-movflags','+faststart','-y','ev.mp4'],check=True)
subprocess.run(['ffmpeg','-v','error','-i','ev.mp4','-f','null','-'],check=True)
data=Path('ev.mp4').read_bytes();item={'id':f'dramabox-null42000029033-ep{e}-part1-private-probe','episode':e,'part':1,'title':f'The Weakest Null Commands the Devil King! - Episode {e} Part 1/{parts[e]} | DramaBox','description':'Private claims qualification. Not approved for public release.','file':'ev.mp4','source_start':0.0,'source_end':cuts[e],'privacy':'private','approval_required':True,'bytes':len(data),'sha256':hashlib.sha256(data).hexdigest()};Path('ev.json').write_text(json.dumps(item));MANIFEST='ev.json'

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
    return {'item_id':item['id'],'video_id':result['video_id'],'privacy':'private','channel_id':CHANNEL,'processing_status':row.get('processingDetails',{}).get('processingStatus','unknown'),'claims_verified':False,'studio_review_required':True,'public_publishing_enabled':False}

def main():
    controls=None
    stage="manifest"
    try:
        item=json.loads(Path(MANIFEST).read_text());path='ev.mp4';validate(item,path)
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
                probe(backend,os.environ['GITHUB_RUN_ID']+'-ep'+os.environ['NULL_EP']+'-a'+str(_pa))
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
        while True:
            _da+=1
            try:
                _count=_dupread()
                break
            except Exception as _e:
                _m=str(_e)
                if 'Existing episode part' in _m or 'Channel mismatch' in _m:raise
                if _da<3:
                    print('RETRY duplicate_read attempt '+str(_da)+' transient: '+_m[:120]+'; backoff 75s',flush=True)
                    _pt.sleep(75)
                    continue
                raise
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
        open(os.environ["GITHUB_STEP_SUMMARY"],"a").write("## Private Weakest Null episode probe verified\n\n```json\n"+json.dumps(result,indent=2)+"\n```\n")
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