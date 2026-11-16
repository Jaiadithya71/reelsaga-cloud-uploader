"""Read-only current ReelSaga video/playlist membership audit. No platform mutation."""
import os,json
from actions_canary import Store
from desktop_setup import CHANNEL,SCOPES
from provision_actions import validated_record
from credentials import GoogleCredentials
from transport import Transport,GoogleTokenForms
from adapters import checked
record=validated_record(os.environ.pop('REELSAGA_GOOGLE_CREDENTIALS',''))
credential=GoogleCredentials(Store(record),GoogleTokenForms(),SCOPES)
api=Transport(lambda:credential.access_token(),{'www.googleapis.com'})
def get(path,**q):return checked(api('GET','https://www.googleapis.com/youtube/v3/'+path,params=q)).data
def pages(path,**q):
 out=[]
 for _ in range(100):
  data=get(path,maxResults=50,**q);out+=data.get('items',[])
  if not data.get('nextPageToken'):return out
  q['pageToken']=data['nextPageToken']
 raise RuntimeError('pagination bound')
c=get('channels',part='snippet,contentDetails',id=CHANNEL)['items'][0]
assert c['id']==CHANNEL
uploads=c['contentDetails']['relatedPlaylists']['uploads']
u=pages('playlistItems',part='contentDetails',playlistId=uploads)
ids=[x['contentDetails']['videoId'] for x in u]
vs=[]
for n in range(0,len(ids),50):
 vs+=get('videos',part='snippet,status',id=','.join(ids[n:n+50])).get('items',[])
for v in vs:
 assert v['snippet']['channelId']==CHANNEL
 print('AUDIT_VIDEO '+json.dumps({'id':v['id'],'title':v['snippet']['title'],'description':v['snippet'].get('description',''),'privacy':v['status']['privacyStatus'],'upload':v['status'].get('uploadStatus'),'published':v['snippet']['publishedAt']},ensure_ascii=True))
ps=pages('playlists',part='snippet,status,contentDetails',channelId=CHANNEL)
for p in ps:
 assert p['snippet']['channelId']==CHANNEL
 items=pages('playlistItems',part='snippet,contentDetails,status',playlistId=p['id'])
 print('AUDIT_PLAYLIST '+json.dumps({'id':p['id'],'title':p['snippet']['title'],'privacy':p['status']['privacyStatus'],'count':p['contentDetails']['itemCount'],'items':[{'item':i['id'],'id':i['contentDetails'].get('videoId'),'title':i['snippet']['title'],'position':i['snippet']['position'],'privacy':i.get('status',{}).get('privacyStatus')}for i in items]},ensure_ascii=True))
print('AUDIT_COMPLETE '+json.dumps({'channel':CHANNEL,'videos':len(vs),'playlists':len(ps)}))
