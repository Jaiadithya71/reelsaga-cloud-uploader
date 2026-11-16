"""Read-only E5 duplicate inventory reconciliation, no upload or state mutation."""
import os,json,hashlib
from actions_canary import Store
from desktop_setup import CHANNEL,SCOPES
from provision_actions import validated_record
from credentials import GoogleCredentials
from transport import Transport,GoogleTokenForms
from adapters import checked
record=validated_record(os.environ.pop('REELSAGA_GOOGLE_CREDENTIALS',''));c=GoogleCredentials(Store(record),GoogleTokenForms(),SCOPES);api=Transport(lambda:c.access_token(),{'www.googleapis.com'})
def get(path,**q):return checked(api('GET','https://www.googleapis.com/youtube/v3/'+path,params=q)).data
ch=get('channels',part='contentDetails',mine='true')['items'];assert len(ch)==1 and ch[0]['id']==CHANNEL
pl=ch[0]['contentDetails']['relatedPlaylists']['uploads'];ids=[];page=None
while True:
 q={'part':'contentDetails','playlistId':pl,'maxResults':50}
 if page:q['pageToken']=page
 d=get('playlistItems',**q);ids.extend(x['contentDetails']['videoId']for x in d.get('items',[]));page=d.get('nextPageToken')
 if not page:break
ids=list(dict.fromkeys(ids));seen=set();matches=[]
for n in range(0,len(ids),50):
 for v in get('videos',part='snippet,status',id=','.join(ids[n:n+50])).get('items',[]):
  seen.add(v['id']);assert v['snippet']['channelId']==CHANNEL
  if 'episode 5' in v['snippet']['title'].lower() and 'mafia charge' in v['snippet']['title'].lower():matches.append(v)
missing=sorted(set(ids)-seen)
print('INVENTORY_DIAG '+json.dumps({'count':len(ids),'returned':len(seen),'missing':missing,'e5_matches':matches}))
for vid in missing:print('MISSING_SINGLE '+json.dumps({'id':vid,'response':get('videos',part='snippet,status',id=vid)}))
