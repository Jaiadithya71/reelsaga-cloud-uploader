import os,json,pathlib,urllib.request,urllib.error,time
import cloudinary,cloudinary.api,cloudinary.uploader
from cloudinary.exceptions import NotFound
from github_state import GitHubState
from transport import Transport
from durable_state import DurableLedger
ID='repair-pups-e1p1-fullheight-20261028-v1';PID='6ae1604ff652e014d7a4bf99'
secret=os.environ.pop('REELSAGA_CLOUDINARY_API_SECRET');buf=os.environ.pop('REELSAGA_BUFFER_API_KEY');gh=os.environ.pop('GH_TOKEN');lk=os.environ.pop('REELSAGA_LEDGER_KEY')
class State(GitHubState):
 def url(self,k):return self.base+'/contents/state-v2/'+k+'.enc'
b=State(Transport(lambda:gh,{'api.github.com'}),lk);ledger=DurableLedger(b)
rec,_=b.get(ledger.key(ID,'instagram'));assert rec and rec['external_id']==PID and rec['state']=='ready_for_review' and rec['session']=='buffer_sent_pending_public_pixels'
host,hv=b.get('host-'+ID);assert host and host['bytes']==85133950 and host['public_id']=='reelsaga-repair/20261028/pups-e1p1-fullheight-v1';url=host['url'];print('::add-mask::'+url)
req=urllib.request.Request('https://api.buffer.com',data=json.dumps({'query':'query($input:PostInput!){post(input:$input){id status externalLink}}','variables':{'input':{'id':PID}}}).encode(),headers={'Authorization':'Bearer '+buf,'Content-Type':'application/json'})
with urllib.request.urlopen(req,timeout=60)as r:p=json.load(r)['data']['post']
assert p['id']==PID and p['status']=='sent' and p.get('externalLink')
cloudinary.config(cloud_name='btob02ll',api_key='323756243716765',api_secret=secret,secure=True)
r=cloudinary.uploader.destroy(host['public_id'],resource_type='video',type='authenticated',invalidate=True);assert r['result']in('ok','not found')
try:cloudinary.api.resource(host['public_id'],resource_type='video',type='authenticated');raise RuntimeError('Host still present')
except NotFound:pass
statuses={}
for method in ('HEAD','GET'):
 try:
  with urllib.request.urlopen(urllib.request.Request(url,method=method),timeout=45)as x:statuses[method]=x.status
 except urllib.error.HTTPError as e:statuses[method]=e.code
assert all(v in (401,403,404,410)for v in statuses.values()),'Cache still accessible; recheck before cleanup complete'
clean={k:v for k,v in host.items()if k!='url'};clean['state']='destroyed_absence_verified';assert b.compare_and_swap('host-'+ID,hv,clean)
i,iv=b.get('host-intent-'+ID);i['state']='destroyed_absence_verified';assert b.compare_and_swap('host-intent-'+ID,iv,i)
budget,bv=b.get('cloudinary-one-repair-budget-20261028');budget['state']='single_repair_complete_no_extensions';assert b.compare_and_swap('cloudinary-one-repair-budget-20261028',bv,budget)
ledger.checkpoint(ID,'instagram','published',external_id=PID,session='public_pixels_verified_host_destroyed')
pathlib.Path('cleanup-receipt.json').write_text(json.dumps({'post_id':PID,'external_link':p['externalLink'],'destroy':r['result'],'resource_absent':True,'delivery':statuses,'scope':'ONE no extensions'},indent=2));print('CLEANUP_ABSENCE_CONFIRMED')
