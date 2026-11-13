import os,json
from actions_canary import Store
from desktop_setup import CHANNEL,SCOPES
from provision_actions import validated_record
from credentials import GoogleCredentials
from transport import Transport,GoogleTokenForms
from quarantine_state import QuarantineState
from durable_state import DurableLedger
from adapters import checked
record=validated_record(os.environ.pop('REELSAGA_GOOGLE_CREDENTIALS',''));gh=os.environ.pop('GH_TOKEN','');stable=os.environ.pop('REELSAGA_LEDGER_KEY','')
b=QuarantineState(Transport(lambda:gh,{'api.github.com'}),stable);b.initialize()
saved,_=b.get(DurableLedger.key('yourchannel-family829268-ep6-part1-v1','youtube'));c,_=b.get('account-control')
print(json.dumps({'ledger':{k:saved.get(k) for k in ['id','state','external_id']} if saved else None,'has_session':bool(saved and saved.get('session')),'control':c}))
api=Transport(lambda:GoogleCredentials(Store(record),GoogleTokenForms(),SCOPES).access_token(),{'www.googleapis.com'})
x=checked(api('GET','https://www.googleapis.com/youtube/v3/channels',params={'part':'contentDetails','mine':'true'})).data['items'];assert {v['id'] for v in x}=={CHANNEL};pl=x[0]['contentDetails']['relatedPlaylists']['uploads'];p=None;ids=[]
while True:
 q={'part':'contentDetails','playlistId':pl,'maxResults':'50'}
 if p:q['pageToken']=p
 d=checked(api('GET','https://www.googleapis.com/youtube/v3/playlistItems',params=q)).data;ids +=[v['contentDetails']['videoId'] for v in d['items']];p=d.get('nextPageToken')
 if not p:break
matches=[]
for n in range(0,len(ids),50):
 d=checked(api('GET','https://www.googleapis.com/youtube/v3/videos',params={'part':'snippet,status','id':','.join(ids[n:n+50])})).data
 for v in d['items']:
  if v['snippet']['title']=='His Unexpected Little Family - Episode 6 Part 1/4 | YourChannel':matches.append({'id':v['id'],'title':v['snippet']['title'],'privacy':v['status']['privacyStatus']})
print(json.dumps({'inventory_count':len(ids),'exact_matches':matches}))

if saved and saved.get("session"):
 session=saved["session"];print("::add-mask::"+session,flush=True)
 r=api("PUT",session,body=b"",headers={"Content-Length":"0","Content-Range":"bytes */22296481"});print(json.dumps({"saved_session_status":r.status,"range":r.headers.get("Range") or r.headers.get("range"),"video_id":r.data.get("id"),"error_reasons":[e.get("reason") for e in r.data.get("error",{}).get("errors",[])]}))
