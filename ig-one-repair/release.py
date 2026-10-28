import os,json,time,pathlib,hashlib,urllib.request,datetime
import cloudinary,cloudinary.api
from github_state import GitHubState
from transport import Transport
from durable_state import DurableLedger
ID='repair-pups-e1p1-fullheight-20261028-v1';PID='6ae1604ff652e014d7a4bf99';CH='6adb4d02778b240e2f9c6d48';ORG='6adb4a329ef1e740831f7879'
secret=os.environ.pop('REELSAGA_CLOUDINARY_API_SECRET');buf=os.environ.pop('REELSAGA_BUFFER_API_KEY');gh=os.environ.pop('GH_TOKEN');lk=os.environ.pop('REELSAGA_LEDGER_KEY')
class State(GitHubState):
 def url(self,k):return self.base+'/contents/state-v2/'+k+'.enc'
b=State(Transport(lambda:gh,{'api.github.com'}),lk);ledger=DurableLedger(b)
rec,_=b.get(ledger.key(ID,'instagram'));assert rec and rec['state']=='ready_for_review'and rec['external_id']==PID
host,_=b.get('host-'+ID);assert host and host['bytes']==85133950
budget,_=b.get('cloudinary-one-repair-budget-20261028');assert budget and budget['attempts']==1
cloudinary.config(cloud_name='btob02ll',api_key='323756243716765',api_secret=secret,secure=True)
u=cloudinary.api.usage();assert str(u['plan']).lower()=='free'and u['credits']['limit']==25 and float(u['credits']['usage'])+budget['reserve']+1<25
caption=pathlib.Path('ig-one-repair/caption.txt').read_text()
def gql(q,v):
 req=urllib.request.Request('https://api.buffer.com',data=json.dumps({'query':q,'variables':v}).encode(),headers={'Authorization':'Bearer '+buf,'Content-Type':'application/json'})
 try:
  with urllib.request.urlopen(req,timeout=90)as r:d=json.load(r)
 except Exception:raise RuntimeError('Buffer result uncertain; no retry')from None
 if d.get('errors'):raise RuntimeError('GraphQL error; no retry')
 return d['data']
Q='query($input:PostInput!){post(input:$input){id status channelId text sentAt dueAt externalLink metadata{... on InstagramPostMetadata{type shouldShareToFeed isAiGenerated}} assets{type thumbnail ... on VideoAsset{video{width height durationMs thumbnailOffset isVideoProcessing}}}}}'
p=gql(Q,{'input':{'id':PID}})['post'];assert p['status']=='draft'and p['channelId']==CH and p['text']==caption and not p.get('dueAt')and not p.get('sentAt')
assert p['metadata']=={'type':'reel','shouldShareToFeed':True,'isAiGenerated':True};v=p['assets'][0]['video'];assert v['width']==1080 and v['height']==1922 and v['durationMs']==55400 and v['thumbnailOffset']==2000 and not v['isVideoProcessing']
ch=gql('query($input:ChannelInput!){channel(input:$input){name organizationId isDisconnected isLocked isQueuePaused}}',{'input':{'id':CH}})['channel'];assert ch['name'].lstrip('@')=='reelsaga3000'and ch['organizationId']==ORG and not ch['isDisconnected']and not ch['isLocked']and not ch['isQueuePaused']
recent=gql('query($input:PostsInput!){posts(input:$input,first:100){edges{node{id text status sentAt dueAt}}}}',{'input':{'organizationId':ORG,'filter':{'channelIds':[CH],'status':['draft','scheduled','sending','sent']}}})['posts']['edges'];now=datetime.datetime.now(datetime.timezone.utc)
for e in recent:
 n=e['node']
 if n['id']==PID:continue
 assert n.get('text','').strip()!=caption.strip(),'Duplicate caption'
 ts=n.get('sentAt')or n.get('dueAt')
 if ts:assert abs((now-datetime.datetime.fromisoformat(ts.replace('Z','+00:00'))).total_seconds())>=1800,'Spacing'
ledger.checkpoint(ID,'instagram','uncertain',external_id=PID,session='buffer_release_existing_draft')
pathlib.Path('release-receipt.json').write_text(json.dumps({'status':'release_in_flight','post_id':PID}))
r=gql('mutation($input:EditPostInput!){editPost(input:$input){__typename ... on PostActionSuccess{post{id status}} ... on MutationError{message}}}',{'input':{'id':PID,'mode':'shareNow','schedulingType':'automatic','saveToDraft':False}})['editPost'];assert r.get('post',{}).get('id')==PID,'Release response unknown; reconcile'
for i in range(12):
 if i:time.sleep(20)
 p=gql(Q,{'input':{'id':PID}})['post'];status=p['status'];link=p.get('externalLink')
 receipt={'status':status,'post_id':PID,'external_link':link,'sent_at':p.get('sentAt'),'caption_exact':p.get('text')==caption,'metadata':p.get('metadata'),'video':[a.get('video')for a in p['assets']]};pathlib.Path('release-receipt.json').write_text(json.dumps(receipt,indent=2));print('RELEASE_STATUS',status,flush=True)
 if status in ('sent','error'):break
if status!='sent' or not link:raise RuntimeError('Not confirmed sent; no retry')
# Publication acknowledged by Buffer, not final framing check. Keep state reviewable until pixels.
ledger.checkpoint(ID,'instagram','ready_for_review',external_id=PID,session='buffer_sent_pending_public_pixels')
print('BUFFER_SENT',link,flush=True)
