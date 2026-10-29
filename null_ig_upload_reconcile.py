"""Read-only reconciliation of exact E3P1 upload precondition failure."""
import os,json,pathlib,hashlib,urllib.request,urllib.error
import boto3
from botocore.config import Config
from github_state import GitHubState
from transport import Transport
from durable_state import DurableLedger
from buffer_client import Buffer
class State(GitHubState):
 def url(self,k):return self.base+'/contents/state-v2/'+k+'.enc'
st=State(Transport(lambda:os.environ['GH_TOKEN'],{'api.github.com'}),os.environ.pop('REELSAGA_LEDGER_KEY'))
i='dramabox-null42000029033-ep3-part2-v1';item=next(x for x in json.loads(pathlib.Path('null-public-catalog.json').read_text())['items']if x['id']==i)
rec,rv=st.get(DurableLedger.key(i,'instagram'));host,hv=st.get('host-'+i)
assert rec and host and rec['state']=='uploading' and not rec.get('external_id') and host['state']=='upload_intent'
assert rec['session']=='tigris:'+host['key'] and host['bytes']==item['bytes']
buf=Buffer(os.environ.pop('REELSAGA_BUFFER_API_KEY'));rows=buf.inventory('6adb4a329ef1e740831f7879','6adb4d02778b240e2f9c6d48');assert not[x for x in rows if x.get('text')==item['caption']]
s3=boto3.client('s3',endpoint_url='https://t3.storage.dev',region_name='auto',aws_access_key_id=os.environ.pop('AWS_ACCESS_KEY_ID'),aws_secret_access_key=os.environ.pop('AWS_SECRET_ACCESS_KEY'),config=Config(signature_version='s3v4',retries={'total_max_attempts':1},s3={'addressing_style':'path'}))
objects=[]
for bucket in ('reelsaga-private-staging-71','reelsaga-relay-stage-71'):
 a=[]
 for page in s3.get_paginator('list_objects_v2').paginate(Bucket=bucket):a.extend(page.get('Contents',[]))
 objects.append({'bucket':bucket,'count':len(a),'bytes':sum(x['Size']for x in a),'exact_key_present':any(x['Key']==host['key']for x in a)})
try:
 h=s3.head_object(Bucket=host['bucket'],Key=host['key']);head={'exists':True,'bytes':h['ContentLength']};data=s3.get_object(Bucket=host['bucket'],Key=host['key'])['Body'].read(item['bytes']+1);head['sha256']=hashlib.sha256(data).hexdigest();head['matches_original']=len(data)==item['bytes']and head['sha256']==item['sha256']
except s3.exceptions.ClientError as e:head={'http_status':e.response['ResponseMetadata']['HTTPStatusCode'],'exists':False}
public={}
for method in ('HEAD','GET'):
 try:
  with urllib.request.urlopen(urllib.request.Request(host['url'],method=method),timeout=45)as r:public[method]=r.status
 except urllib.error.HTTPError as e:public[method]=e.code
out={'item':i,'ledger_state':rec['state'],'no_buffer_post':True,'inventory_complete':True,'host_state':host['state'],'objects':objects,'head':head,'public':public,'no_mutations':True}
pathlib.Path('ig-upload-reconcile.json').write_text(json.dumps(out,indent=2));print(json.dumps(out))
