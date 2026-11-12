"""Read-only uncertain P6 upload diagnosis. No uploads or state writes."""
import os,json
from actions_canary import Store
from desktop_setup import CHANNEL,SCOPES
from provision_actions import validated_record
from credentials import GoogleCredentials
from transport import Transport,GoogleTokenForms
from quarantine_state import QuarantineState
from durable_state import DurableLedger
from adapters import checked
record=validated_record(os.environ.pop('REELSAGA_GOOGLE_CREDENTIALS',''));gh=os.environ.pop('GH_TOKEN','');stable=os.environ.pop('REELSAGA_LEDGER_KEY','');assert len(stable)>=48
backend=QuarantineState(Transport(lambda:gh,{'api.github.com'}),stable);backend.initialize()
item=json.load(open('cake-ep1-part6.json'));saved,_=backend.get(DurableLedger.key(item['id'],'youtube'));control,_=backend.get('account-control')
print(json.dumps({'ledger':None if saved is None else {k:saved.get(k) for k in ['id','state','external_id','metadata_hash']},'saved_session_exists':bool(saved and saved.get('session')),'expected_metadata_hash':DurableLedger.metadata_hash(item),'control':{k:(control or {}).get(k)for k in ['enabled','verified']}}),flush=True)
credential=GoogleCredentials(Store(record),GoogleTokenForms(),SCOPES);token=credential.access_token();api=Transport(lambda:token,{'www.googleapis.com'})
c=checked(api('GET','https://www.googleapis.com/youtube/v3/channels',params={'part':'contentDetails','mine':'true'})).data
assert len(c['items'])==1 and c['items'][0]['id']==CHANNEL
playlist=c['items'][0]['contentDetails']['relatedPlaylists']['uploads'];page=None;seen=set();ids=[];total=None
while True:
 q={'part':'contentDetails','playlistId':playlist,'maxResults':'50'}
 if page:q['pageToken']=page
 d=checked(api('GET','https://www.googleapis.com/youtube/v3/playlistItems',params=q)).data
 if total is None:total=d['pageInfo']['totalResults']
 else:assert total==d['pageInfo']['totalResults']
 ids.extend(x['contentDetails']['videoId']for x in d.get('items',[]));page=d.get('nextPageToken')
 if not page:break
 assert page not in seen;seen.add(page)
ids=list(dict.fromkeys(ids));matches=[]
for n in range(0,len(ids),50):
 d=checked(api('GET','https://www.googleapis.com/youtube/v3/videos',params={'part':'snippet,status','id':','.join(ids[n:n+50])})).data
 assert {v['id']for v in d.get('items',[])}==set(ids[n:n+50])
 for v in d['items']:
  assert v['snippet']['channelId']==CHANNEL
  if v['snippet']['title']==item['title']:matches.append({'id':v['id'],'privacy':v['status']['privacyStatus'],'title':v['snippet']['title'],'description_match':v['snippet']['description']==item['description']})
print(json.dumps({'complete_inventory':True,'count':len(ids),'exact_matches':matches}),flush=True)
