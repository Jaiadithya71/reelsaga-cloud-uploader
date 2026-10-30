import os,json,pathlib,hashlib,time,datetime,subprocess,uuid,urllib.request,urllib.error,traceback
import boto3,numpy as np
from botocore.config import Config
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from github_state import GitHubState
from transport import Transport
from durable_state import DurableLedger
from buffer_client import Buffer,Inventory
from queue_guard import require,preflight,media
from public_verify import verify
from verified_upload import put_once_verified
B='reelsaga-relay-stage-71';OLD='reelsaga-private-staging-71';CH='6adb4d02778b240e2f9c6d48';ORG='6adb4a329ef1e740831f7879';BATCH='ig-null-batch-20261029'
def receipt(**kw):pathlib.Path('recovery-receipt.json').write_text(json.dumps(kw,indent=2))
m=json.loads(pathlib.Path('null-public-catalog.json').read_text())
require(not m.get('instagram_publishing_paused',m.get('publishing_paused',False)),'Instagram publication paused; no new upload or post')
require(1<=len(m['items'])<=33 and m['full_planned_parts']==33,'Unexpected qualified catalog')
review=json.loads(pathlib.Path('null-ig-release-gates.json').read_text())
require(m['approval_message']=='wamid.HBgMOTE3MzU4MjU4MjE2FQIAEhggQUM2RTE4MzhGMzY2OUM3NjExMzdDMDMxNjBERTRGMzUA','Approval mismatch')

class State(GitHubState):
 def url(self,k):return self.base+'/contents/state-v2/'+k+'.enc'
st=State(Transport(lambda:os.environ['GH_TOKEN'],{'api.github.com'}),os.environ.pop('REELSAGA_LEDGER_KEY'));ledger=DurableLedger(st);buf=Buffer(os.environ.pop('REELSAGA_BUFFER_API_KEY'))
s3=boto3.client('s3',endpoint_url='https://t3.storage.dev',region_name='auto',aws_access_key_id=os.environ.pop('AWS_ACCESS_KEY_ID'),aws_secret_access_key=os.environ.pop('AWS_SECRET_ACCESS_KEY'),config=Config(signature_version='s3v4',retries={'total_max_attempts':1},s3={'addressing_style':'path'}))
def inv(bucket):
 a=[]
 for page in s3.get_paginator('list_objects_v2').paginate(Bucket=bucket):a.extend(page.get('Contents',[]))
 return a
def code(link):
 import re
 z=re.search(r'/(?:reel|reels|p)/([A-Za-z0-9_-]+)',link or'');return z.group(1)if z else None
def is_present(c):
 try:
  with urllib.request.urlopen('https://www.instagram.com/reel/'+c+'/embed/',timeout=45)as r:s=r.read(5000000).decode()
 except Exception:raise RuntimeError('Old-post presence unverifiable')from None
 return 'EmbeddedMediaImage'in s
prior,_=st.get('ig-recovery-batch-20261028')
require(prior and prior.get('state')=='active' and time.time()<prior['deadline'],'Existing free transfer batch evidence missing/expired')
batch,bv=st.get(BATCH)
if not batch:
 batch={'state':'active','started':time.time(),'deadline':time.time()+6*86400,'class_a_reserved':0,'class_b_reserved':0,'objects':[],'baseline_a':prior['baseline_a']+prior['class_a_reserved'],'baseline_b':prior['baseline_b']+prior['class_b_reserved'],'baseline_asof':'2026-10-28T05:20:00Z','bucket_names':[OLD,B]};require(st.compare_and_swap(BATCH,bv,batch),'Batch CAS failed');batch,bv=st.get(BATCH)
def cleanup_batch(force=False):
 hosts=[]
 for i in m['items']:
  h,hv=st.get('host-'+i['id'])
  if h and h.get('state')!='deleted_absence_verified':hosts.append((i,h,hv))
 if not hosts:return
 require(force or len(hosts)>=2 or all(i.get('status')=='public_verified_cleaned'or ledger.resume(i['id'],'instagram')=='do_not_create'for i in m['items']),'Cleanup batch not due')
 for i,h,hv in hosts:
  require(h.get('state')=='published_qa_verified','Unresolved post requires cancellation/reconciliation before cleanup')
  p=buf.post(h['post_id']);require(p['status']=='sent'and p['externalLink']==h['external_link'],'Published identity changed')
  s3.delete_object(Bucket=B,Key=h['key'])
  try:s3.head_object(Bucket=B,Key=h['key']);raise RuntimeError('Deleted host still exists')
  except s3.exceptions.ClientError as e:require(e.response['ResponseMetadata']['HTTPStatusCode']==404,'Host absence unknown')
  for method in ('HEAD','GET'):
   try:
    with urllib.request.urlopen(urllib.request.Request(h['url'],method=method),timeout=45)as r:raise RuntimeError('Delivery cache still accessible')
   except urllib.error.HTTPError as e:require(e.code in(403,404,410),'Delivery absence unknown')
  h={k:v for k,v in h.items()if k!='url'};h['state']='deleted_absence_verified';require(st.compare_and_swap('host-'+i['id'],hv,h),'Cleanup state conflict')
 receipt(status='batch_cleanup_absence_verified',items=[i['id']for i,h,hv in hosts])
if os.environ.get('RECOVERY_CLEANUP_ONLY')=='1':
 cleanup_batch(force=True);raise SystemExit(0)
require(time.time()<batch['deadline'],'Batch cleanup deadline reached, no more uploads')
new_before=inv(B)
if len(new_before)>=2:cleanup_batch()
item=None
for i in m['items']:
 if i.get('status')=='public_verified_cleaned':continue
 r,_=st.get(ledger.key(i['id'],'instagram'))
 if r and r['state']=='published':continue
 require(not r or (r['state']=='started'and not r.get('external_id')and not r.get('session')) or (os.environ.get('NULL_RESUME_VERIFIED_UPLOAD')=='1'and i['id']=='dramabox-null42000029033-ep3-part2-v1'and r['state']=='uploading'and not r.get('external_id')and r.get('session','').startswith('tigris:')) or (os.environ.get('RECOVERY_RESUME_DRAFT')=='1'and r['state']=='ready_for_review'and r.get('session')=='draft_created'and r.get('external_id')),'In-flight or blocked item, reconcile exact saved ID')
 item=i;break
if item is None:receipt(status='all_30_verified_no_new_post');raise SystemExit(0)
gate=review.get(item['id'])
owner_ig_exception=(item['id']=='dramabox-null42000029033-ep7-part2-v1' and gate and gate.get('status')=='instagram_owner_authorized_known_youtube_block' and gate.get('youtube_current_status')=='globally_blocked_visual_DramaBox' and gate.get('not_rights_clearance') is True and gate.get('instagram_authorization_message')==m.get('instagram_resume',{}).get('message_id')=='wamid.HBgMOTE3MzU4MjU4MjE2FQIAEhggQUM2QkQ1NkUxQjNCNkNDOTdBREY1RjJCNjY3MjJCRTkA' and not m.get('instagram_publishing_paused',True))
require(gate and (gate.get('status')=='private_hd_no_claims' or owner_ig_exception) and gate.get('source_sha256')==item['sha256'],'Own-part review/IG authorization missing or media changed')
require(time.time()-gate['reviewed_at']<86400,'Own-part private review stale')
# All preceding items must have completed served frame/cover verification. No part skipping.
position=m['items'].index(item)
for earlier in m['items'][:position]:
 rr,_=st.get(ledger.key(earlier['id'],'instagram'));require(rr and rr.get('state')=='published' and 'public_pixels_verified' in rr.get('session',''),'Earlier part not verified')
receipt(status='preflight',item=item['id'])
resume=os.environ.get('RECOVERY_RESUME_DRAFT')=='1'
recover_upload=os.environ.get('NULL_RESUME_VERIFIED_UPLOAD')=='1'
require(not recover_upload or item['id']=='dramabox-null42000029033-ep3-part2-v1','Recovery exact item mismatch')
if not resume:
 channel=buf.channel(CH);recent=buf.inventory(ORG,CH);caption=item['caption'];dupes=[p for p in recent if p.get('text','').strip()==caption.strip()]
 # Historical Buffer sent rows persist after intentional IG deletion. Only exact mapped old shortcode absent can be excluded.
 exclude=set()
 for p in dupes:
  require(p['status']=='sent'and code(p.get('externalLink'))==item['old_shortcode'],'Caption duplicate is not the mapped deleted original')
  require(not is_present(item['old_shortcode']),'Mapped original still publicly present');exclude.add(p['id'])
 recent=Inventory(p for p in recent if p['id']not in exclude)
 now=datetime.datetime.now(datetime.timezone.utc)
 for row in recent:
  ts=row.get('sentAt')or row.get('dueAt')
  if ts and abs((now-datetime.datetime.fromisoformat(ts.replace('Z','+00:00'))).total_seconds())<2400:
   receipt(status='waiting_minimum_40min_spacing',item=item['id']);raise SystemExit(0)
 preflight(item,channel,recent,datetime.datetime.now(datetime.timezone.utc),caption,min_gap=2400)
 old=inv(OLD);new=inv(B);require(sum(x['Size']for x in old+new)+item['bytes']+512*1024**2<4*1024**3,'Aggregate storage guard');require(len(new)<2,'Stage count guard');require(batch['baseline_a']+batch['class_a_reserved']+30<9000 and batch['baseline_b']+batch['class_b_reserved']+100<90000,'Request planning guard')
 for x in old:
  try:
   with urllib.request.urlopen(urllib.request.Request('https://'+OLD+'.t3.tigrisbucket.io/'+x['Key'],method='HEAD'),timeout=20)as r:raise RuntimeError('Old source public')
  except urllib.error.HTTPError as e:require(e.code==403,'Old privacy uncertain')
 if recover_upload:
  rec,_=st.get(ledger.key(item['id'],'instagram'));saved,_=st.get('host-'+item['id'])
  require(rec['state']=='uploading'and not rec.get('external_id')and saved['state']=='upload_intent'and rec['session']=='tigris:'+saved['key']and saved['bytes']==item['bytes'],'Saved upload mismatch')
  require(len(new)==1 and new[0]['Key']==saved['key']and new[0]['Size']==item['bytes'],'Exact saved object inventory mismatch')
 else:
  # Commit request reserve before any real upload. No card or billing mutation exists in this workflow.
  batch['class_a_reserved']+=30;batch['class_b_reserved']+=100;require(st.compare_and_swap(BATCH,bv,batch),'Reserve CAS failed')
  existing,version=st.get(ledger.key(item['id'],'instagram'))
  if existing:
   require(False,'Existing started item requires exact reconciliation, no automatic re-claim')
  else:require(ledger.claim(item,'instagram'),'Existing item claim')
if os.environ.get('RECOVERY_DIAG_ONLY')=='1':
 rec,_=st.get(ledger.key(item['id'],'instagram'));p=buf.post(rec['external_id']);thumb=p['assets'][0]['thumbnail'];print('::add-mask::'+thumb)
 from urllib.parse import urlsplit
 try:
  with urllib.request.urlopen(thumb,timeout=45)as rr:hc=rr.status;body='image'
 except urllib.error.HTTPError as e:hc=e.code;body=e.read(300).decode(errors='replace')
 receipt(status='draft_diagnostic',post_id=p['id'],post_status=p['status'],thumbnail_host=urlsplit(thumb).hostname,thumbnail_path=urlsplit(thumb).path,http_code=hc,body_preview=body,video=p['assets'][0].get('video'))
 raise SystemExit(0)
if resume:
 rec,_=st.get(ledger.key(item['id'],'instagram'));host,_=st.get('host-'+item['id']);print('::add-mask::'+host['url'],flush=True)
 with urllib.request.urlopen(host['url'],timeout=90)as rr:pathlib.Path('p1.mp4').write_bytes(rr.read(item['bytes']+1))
else:
 import requests,io,zipfile
 u='https://cps-distr.ikyuedu.com/distribution/11/DramaBox资源包-42000029033-19b48bade6b3906f40a7fafe28d1b268.zip'
 sess=requests.Session();rr=sess.head(u,timeout=30);rr.raise_for_status();size=int(rr.headers['Content-Length'])
 class Remote(io.RawIOBase):
  def __init__(self):self.pos=0
  def seekable(self):return True
  def readable(self):return True
  def tell(self):return self.pos
  def seek(self,o,w=0):self.pos=o if w==0 else self.pos+o if w==1 else size+o;return self.pos
  def read(self,n=-1):
   if n<0:n=size-self.pos
   n=min(n,size-self.pos)
   if n<=0:return b''
   rr=sess.get(u,headers={'Range':f'bytes={self.pos}-{min(size-1,self.pos+n-1)}'},timeout=45);rr.raise_for_status();require(rr.status_code==206,'Source range unsupported');self.pos+=len(rr.content);return rr.content
 z=zipfile.ZipFile(Remote());pathlib.Path('source.mp4').write_bytes(z.read(f"Episode{item['episode']}.mp4"))
 length=item['source_end']-item['source_start']
 subprocess.run(['ffmpeg','-v','error','-filter_threads','1','-ss',str(item['source_start']),'-i','source.mp4','-t',str(length),'-vf',f'fade=t=in:st=0:d=0.5,fade=t=out:st={length-.5}:d=0.5','-af',f'afade=t=in:st=0:d=0.5,afade=t=out:st={length-.5}:d=0.5','-c:v','libx264','-threads:v','3','-preset','ultrafast','-crf','18','-c:a','aac','-b:a','192k','-movflags','+faststart','-y','p1.mp4'],check=True)
p=pathlib.Path('p1.mp4');require(p.stat().st_size==item['bytes']and hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'],'Original differs')
meta=json.loads(subprocess.check_output(['ffprobe','-v','error','-show_streams','-show_format','-of','json',str(p)]));v=next(x for x in meta['streams']if x['codec_type']=='video');subprocess.run(['ffmpeg','-v','error','-i',str(p),'-f','null','-'],check=True,capture_output=True)
subprocess.run(['ffmpeg','-v','error','-ss',str(item['cover_ms']/1000),'-i',str(p),'-frames:v','1','-vf','scale=360:640','-y','original-cover.png'],check=True,capture_output=True)
from PIL import Image
require(np.asarray(Image.open('original-cover.png')).mean()>12,'Black original cover');require(v['height']/v['width']>1.7 and v['sample_aspect_ratio']=='1:1'and any(x['codec_type']=='audio'for x in meta['streams']),'Original video shape/audio')
if not resume:
 if recover_upload:
  hk='host-'+item['id'];host,_=st.get(hk);k=host['key'];url=host['url'];print('::add-mask::'+url,flush=True)
  require(s3.head_object(Bucket=B,Key=k)['ContentLength']==item['bytes'],'Saved object size mismatch')
 else:
  k='xfer/'+item['id']+'-'+uuid.uuid4().hex+'.mp4';url='https://'+B+'.t3.tigrisbucket.io/'+k;print('::add-mask::'+url,flush=True);hk='host-'+item['id'];host={'key':k,'bucket':B,'url':url,'bytes':item['bytes'],'uploaded':time.time(),'deadline':batch['deadline'],'state':'upload_intent'};require(st.compare_and_swap(hk,None,host),'Host locator exists');ledger.checkpoint(item['id'],'instagram','uploading',session='tigris:'+k)
  upload_proof=put_once_verified(s3,B,k,p,item['bytes'],item['sha256'])
  pathlib.Path('upload-readback-receipt.json').write_text(json.dumps(upload_proof,indent=2))
 acl=s3.get_object_acl(Bucket=B,Key=k);require(any(g['Grantee'].get('URI','').endswith('/AllUsers')and g['Permission']=='READ'for g in acl['Grants']),'Public ACL absent')
 with urllib.request.urlopen(url,timeout=90)as r:data=r.read(item['bytes']+1)
 require(len(data)==item['bytes']and hashlib.sha256(data).hexdigest()==item['sha256'],'Delivery original differs');del data
 host,hv=st.get(hk);host['state']='verified_original';require(st.compare_and_swap(hk,hv,host),'Host checkpoint conflict')
 # Recheck exact saved identity and live channel inventory immediately before
 # external creation. A reconciled acknowledgement never skips release gates.
 rec,_=st.get(ledger.key(item['id'],'instagram'));saved,_=st.get(hk)
 require(rec['state']=='uploading'and not rec.get('external_id')and rec['session']=='tigris:'+k and saved['key']==k and saved['bytes']==item['bytes']and saved['state']=='verified_original','Upload identity changed')
 current=inv(B);require(len(current)==1 and current[0]['Key']==k and current[0]['Size']==item['bytes'],'Unexpected relay object after upload')
 require(sum(x['Size']for x in inv(OLD)+current)+512*1024**2<4*1024**3,'Post-upload storage guard')
 fresh=buf.inventory(ORG,CH);fresh=Inventory(x for x in fresh if x['id']not in exclude)
 preflight(item,buf.channel(CH),fresh,datetime.datetime.now(datetime.timezone.utc),caption,min_gap=2400)
 ledger.checkpoint(item['id'],'instagram','uncertain',session='buffer_create_draft')
 r=buf.draft(CH,caption,url,item['cover_ms']);require(r.get('post',{}).get('id'),'Draft rejected; reconcile');pid=r['post']['id'];ledger.checkpoint(item['id'],'instagram','ready_for_review',external_id=pid,session='draft_created')
else:
 rec,_=st.get(ledger.key(item['id'],'instagram'));pid=rec['external_id'];host,_=st.get('host-'+item['id']);url=host['url'];hk='host-'+item['id'];caption=item['caption'];channel=buf.channel(CH);require(channel['name']=='reelsaga3000','Wrong channel')
if resume:
 rows=buf.inventory(ORG,CH);rows=Inventory(x for x in rows if x['id']!=pid and not(x['status']=='sent'and code(x.get('externalLink'))==item['old_shortcode']and not is_present(item['old_shortcode'])))
 preflight(item,channel,rows,datetime.datetime.now(datetime.timezone.utc),caption,min_gap=2400)
draft=buf.post(pid);dv=draft['assets'][0]['video'];require(draft['status']=='draft'and draft['text']==caption and dv['width']==v['width']and dv['height']==v['height']and abs(dv['durationMs']/1000-float(v['duration']))<.1 and dv['thumbnailOffset']==item['cover_ms']and not dv['isVideoProcessing'],'Draft verification differs')
require(draft['metadata']=={'type':'reel','shouldShareToFeed':True,'isAiGenerated':True},'Draft metadata differs')
# The CDN image URL blocks raw API clients with 403/1010. Do not impersonate browsers.
# Pre-release original frame is decoded/nonblack and exact hash; Buffer derived offset/dimensions match.
# Public served cover/frame comparison is mandatory before queue may advance.
receipt(status='draft_source_and_offset_verified',item=item['id'],post_id=pid,width=dv['width'],height=dv['height'])
ledger.checkpoint(item['id'],'instagram','uncertain',external_id=pid,session='buffer_release_existing_draft');r=buf.release(pid,caption,url,item['cover_ms']);require(r.get('post',{}).get('id')==pid,'Release unacknowledged; reconcile')
for n in range(15):
 post=buf.post(pid);receipt(status=post['status'],item=item['id'],post_id=pid,external_link=post.get('externalLink'))
 if post['status']=='sent':break
 require(post['status']not in('error','failed'),'Publish rejected; hold');time.sleep(20)
require(post['status']=='sent'and post.get('externalLink'),'Not confirmed public')
qa=verify(post['externalLink'],p,caption,item['cover_ms'],'public-qa');require(post['metadata']=={'type':'reel','shouldShareToFeed':True,'isAiGenerated':True},'Public metadata differs');ledger.checkpoint(item['id'],'instagram','published',external_id=pid,session='public_pixels_verified_batch_host_retained')
host,hv=st.get(hk);host.update(state='published_qa_verified',post_id=pid,external_link=post['externalLink']);require(st.compare_and_swap(hk,hv,host),'Host checkpoint failed')
receipt(status='published_public_qa_verified_batch_retained',item=item['id'],post_id=pid,external_link=post['externalLink'],qa=qa,batch_deadline=batch['deadline'])

cleanup_batch(force=True)
