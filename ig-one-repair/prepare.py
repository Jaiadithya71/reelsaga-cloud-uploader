import os,json,time,hashlib,pathlib,datetime,urllib.request,urllib.error,base64
import cloudinary,cloudinary.uploader,cloudinary.api,cloudinary.utils
from github_state import GitHubState
from transport import Transport
from durable_state import DurableLedger
SIZE=85133950;SHA='35f6af5adeed92f6f5376bb489f690797baf96038b4eb082be9b8157d646b5fc';ID='repair-pups-e1p1-fullheight-20261028-v1';CH='6adb4d02778b240e2f9c6d48';ORG='6adb4a329ef1e740831f7879'
pathlib.Path('receipt.json').write_text(json.dumps({'status':'started_no_public_write','item':ID}))
secret=os.environ.pop('REELSAGA_CLOUDINARY_API_SECRET');buf=os.environ.pop('REELSAGA_BUFFER_API_KEY');gh=os.environ.pop('GH_TOKEN');lk=os.environ.pop('REELSAGA_LEDGER_KEY')
cloudinary.config(cloud_name='btob02ll',api_key='323756243716765',api_secret=secret,secure=True)
class State(GitHubState):
 def url(self,k):return self.base+'/contents/state-v2/'+k+'.enc'
b=State(Transport(lambda:gh,{'api.github.com'}),lk);assert b.request('GET',b.base+'/git/ref/heads/'+b.branch).status==200;ledger=DurableLedger(b)
caption=pathlib.Path('ig-one-repair/caption.txt').read_text();item={'id':ID,'bytes':SIZE,'sha256':SHA,'caption':caption,'width':1080,'height':1922,'cover_ms':2000,'ai_label':True}
def checkpoint(state,**kw):ledger.checkpoint(ID,'instagram',state,**kw)
def gql(q,v):
 req=urllib.request.Request('https://api.buffer.com',data=json.dumps({'query':q,'variables':v}).encode(),headers={'Authorization':'Bearer '+buf,'Content-Type':'application/json'})
 try:
  with urllib.request.urlopen(req,timeout=60)as r:d=json.load(r)
 except Exception:raise RuntimeError('Buffer result uncertain; reconcile, never retry')from None
 if d.get('errors'):raise RuntimeError('Buffer GraphQL rejected; inspect schema without response dump')
 return d['data']
ch=gql('query($input:ChannelInput!){channel(input:$input){id name service organizationId isDisconnected isLocked isQueuePaused}}',{'input':{'id':CH}})['channel']
assert ch['name'].lstrip('@')=='reelsaga3000'and ch['organizationId']==ORG and not ch['isDisconnected']and not ch['isLocked']and not ch['isQueuePaused']
recent=gql('query($input:PostsInput!){posts(input:$input,first:100){edges{node{id text status sentAt dueAt}}}}',{'input':{'organizationId':ORG,'filter':{'channelIds':[CH],'status':['draft','scheduled','sending','sent']}}})['posts']['edges']
assert not any(e['node'].get('text','').strip()==caption.strip()for e in recent),'Duplicate exact caption exists; reconcile'
now=datetime.datetime.now(datetime.timezone.utc)
for e in recent:
 ts=e['node'].get('sentAt')or e['node'].get('dueAt')
 if ts:assert abs((now-datetime.datetime.fromisoformat(ts.replace('Z','+00:00'))).total_seconds())>=1800,'Spacing gate'
assert ledger.resume(ID,'instagram')=='unclaimed','Existing claim; reconcile'
u=cloudinary.api.usage();credits=u.get('credits')or{};used=float(credits['usage']);limit=float(credits['limit']);assert str(u.get('plan','')).lower()=='free' and limit==25
# API lag protected by task-local reserve on this ONE attempt, including prior synthetic use.
reserve=SIZE/(1024**3)*5+0.004+0.10;assert used+reserve+1.0<limit,'Capacity gate'
k='cloudinary-one-repair-budget-20261028';old,ver=b.get(k);assert not old,'Existing reserve; reconcile'
assert ledger.claim(item,'instagram')
assert b.compare_and_swap(k,ver,{'attempts':1,'item':ID,'api_usage':used,'limit':limit,'reserve':reserve,'floor':1.0,'last_updated':u.get('last_updated'),'state':'reserved'})
p=pathlib.Path('p1.mp4');assert p.stat().st_size==SIZE and hashlib.sha256(p.read_bytes()).hexdigest()==SHA
pid='reelsaga-repair/20261028/pups-e1p1-fullheight-v1'
# A deterministic host public_id and overwrite false prevent duplicate upload on retry.
assert b.compare_and_swap('host-intent-'+ID,None,{'public_id':pid,'resource_type':'video','type':'authenticated','state':'upload_intent','bytes':SIZE})
checkpoint('uploading',session='cloudinary:'+pid)
up=cloudinary.uploader.upload(str(p),resource_type='video',type='authenticated',public_id=pid,overwrite=False,unique_filename=False,use_filename=False)
assert up['bytes']==SIZE and up['width']==1080 and up['height']==1922 and up['resource_type']=='video'and up['type']=='authenticated'
assert not up.get('eager')
url=cloudinary.utils.cloudinary_url(pid+'.mp4',resource_type='video',type='authenticated',version=up['version'],secure=True,sign_url=True)[0]
print('::add-mask::'+url,flush=True)
host={'public_id':pid,'url':url,'bytes':SIZE,'sha256':SHA,'resource_type':'video','type':'authenticated','version':up['version'],'credits_before':used,'reserved':reserve}
assert b.compare_and_swap('host-'+ID,None,host)
# One full GET checks delivery did not optimize or crop. Charged within reserve.
try:
 with urllib.request.urlopen(url,timeout=90)as res:
  h=hashlib.sha256();n=0
  while True:
   x=res.read(1048576)
   if not x:break
   h.update(x);n+=len(x)
 assert n==SIZE and h.hexdigest()==SHA
except Exception:raise RuntimeError('Host delivery verification failed; no Buffer creation')from None
u2=cloudinary.api.usage();assert float(u2['credits']['usage'])+reserve+1.0<25,'Unexpected usage'
checkpoint('uncertain',session='buffer_create_draft')
inp={'text':caption,'channelId':CH,'schedulingType':'automatic','mode':'addToQueue','saveToDraft':True,'metadata':{'instagram':{'type':'reel','shouldShareToFeed':True,'isAiGenerated':True}},'assets':[{'video':{'url':url,'metadata':{'thumbnailOffset':2000}}}]}
r=gql('mutation($input:CreatePostInput!){createPost(input:$input){__typename ... on PostActionSuccess{post{id status}} ... on MutationError{message}}}',{'input':inp})['createPost'];assert r.get('post'),'Draft rejected; no resend'
postid=r['post']['id'];pathlib.Path('receipt.json').write_text(json.dumps({'status':'draft_created_readback_pending','post_id':postid,'item':ID}));checkpoint('ready_for_review',external_id=postid,session='buffer_draft')
p=gql('query($input:PostInput!){post(input:$input){id status text sentAt dueAt externalLink metadata{... on InstagramPostMetadata{type shouldShareToFeed isAiGenerated}} assets{type source thumbnail mimeType ... on VideoAsset{video{width height durationMs isVideoProcessing isTranscodingRequired thumbnailOffset}}}}}',{'input':{'id':postid}})['post']
assert p['status']=='draft'and not p.get('sentAt')and not p.get('dueAt')and p['text']==caption
# Store private detailed readback encrypted, no plaintext source/thumbnail in artifact or logs.
from cryptography.hazmat.primitives.ciphers.aead import AESGCM
key=hashlib.sha256(b'reelsaga-repair-receipt-v1\0'+secret.encode()).digest();nonce=os.urandom(12);payload={'host':host,'post':p,'item':item};pathlib.Path('private-readback.enc').write_bytes(nonce+AESGCM(key).encrypt(nonce,json.dumps(payload).encode(),None))
san={'status':'draft_ready_for_review','post_id':postid,'width':up['width'],'height':up['height'],'bytes':SIZE,'sha256':SHA,'credits_before':used,'reserve':reserve,'metadata':p.get('metadata'),'video':[a.get('video')for a in p['assets']]};pathlib.Path('receipt.json').write_text(json.dumps(san,indent=2));print('DRAFT_READY',postid)
