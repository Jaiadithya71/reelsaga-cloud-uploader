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
B='reelsaga-relay-stage-71';OLD='reelsaga-private-staging-71';CH='6adb4d02778b240e2f9c6d48';ORG='6adb4a329ef1e740831f7879';BATCH='ig-recovery-batch-20261028'
def receipt(**kw):pathlib.Path('recovery-receipt.json').write_text(json.dumps(kw,indent=2))
secret=os.environ.pop('REELSAGA_CLOUDINARY_API_SECRET');key=hashlib.sha256(b'reelsaga-ig-recovery-catalog-v1\0'+secret.encode()).digest();raw=pathlib.Path('ig-recovery/catalog.enc').read_bytes();m=json.loads(AESGCM(key).decrypt(raw[:12],raw[12:],None));del secret
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
batch,bv=st.get(BATCH)
if not batch:
 batch={'state':'active','started':time.time(),'deadline':time.time()+6*86400,'class_a_reserved':0,'class_b_reserved':0,'objects':[],'baseline_a':1029,'baseline_b':2377,'baseline_asof':'2026-10-28T05:20:00Z','bucket_names':[OLD,B]};require(st.compare_and_swap(BATCH,bv,batch),'Batch CAS failed');batch,bv=st.get(BATCH)

item=next(i for i in m['items']if i['id']=='ig-fullheight-repair-pups-e2p2-20261028-v1')
rec,_=st.get(ledger.key(item['id'],'instagram'));host,hv=st.get('host-'+item['id'])
require(rec['state']=='uncertain'and rec['external_id']=='6ae1b243074a2fccd9885a13'and rec['session']=='buffer_release_existing_draft','Exact released identity differs')
ledger.verify_item(item,'instagram')
post=buf.post(rec['external_id']);require(post['status']=='sent'and post['channelId']==CH and post['text']==item['caption'],'Saved post not confirmed sent')
require(post['metadata']=={'type':'reel','shouldShareToFeed':True,'isAiGenerated':True},'Metadata differs')
print('::add-mask::'+host['url'],flush=True)
with urllib.request.urlopen(host['url'],timeout=90)as rr:pathlib.Path('p1.mp4').write_bytes(rr.read(item['bytes']+1))
p=pathlib.Path('p1.mp4');require(p.stat().st_size==item['bytes']and hashlib.sha256(p.read_bytes()).hexdigest()==item['sha256'],'Hosted original differs')
qa=verify(post['externalLink'],p,item['caption'],item['cover_ms'],'public-qa')
ledger.checkpoint(item['id'],'instagram','published',external_id=post['id'],session='public_pixels_verified_batch_host_retained')
host.update(state='published_qa_verified',post_id=post['id'],external_link=post['externalLink']);require(st.compare_and_swap('host-'+item['id'],hv,host),'Host checkpoint failed')
receipt(status='published_public_qa_verified_batch_retained',item=item['id'],post_id=post['id'],external_link=post['externalLink'],sent_at=post['sentAt'],qa=qa)
