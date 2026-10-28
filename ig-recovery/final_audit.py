"""Read-only batch closeout. Never upload, publish or delete."""
import pathlib
source=pathlib.Path('ig-recovery/runner.py').read_text().split('def cleanup_batch(force=False):')[0]
exec(compile(source,'ig-recovery/runner.py','exec'))
old=inv(OLD);new=inv(B)
require(len(old)==9 and sum(x['Size']for x in old)==330741043,'Original nine inventory changed')
require(not new,'Relay staging not empty')
privacy=[]
for x in old:
 statuses={}
 for method in ('HEAD','GET'):
  url='https://'+OLD+'.t3.tigrisbucket.io/'+x['Key']
  try:
   req=urllib.request.Request(url,method=method,headers={'Range':'bytes=0-0'}if method=='GET'else{})
   with urllib.request.urlopen(req,timeout=45)as response:raise RuntimeError('Original source public')
  except urllib.error.HTTPError as error:
   require(error.code==403,'Original source privacy uncertain');statuses[method]=error.code
 privacy.append({'key_sha256':hashlib.sha256(x['Key'].encode()).hexdigest(),'bytes':x['Size'],'anonymous':statuses})
hosts=[];published=[]
for item in m['items']:
 host,_=st.get('host-'+item['id'])
 if host:
  require(host['state']=='deleted_absence_verified','Host cleanup unresolved')
  hosts.append({'id':item['id'],'state':host['state']})
 if item.get('status')=='public_verified_cleaned':published.append(item['id']);continue
 rec,_=st.get(ledger.key(item['id'],'instagram'))
 require(rec and rec['state']=='published','Repair ledger incomplete');published.append(item['id'])
require(len(published)==33,'Repair count differs')
receipt(status='final_read_only_audit_passed',checked_at=datetime.datetime.now(datetime.timezone.utc).isoformat(),repairs_published=len(published),relay_objects=0,original_objects=len(old),original_bytes=sum(x['Size']for x in old),original_privacy=privacy,hosts=hosts)
