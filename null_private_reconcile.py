"""Read-only failed-probe reconciliation. No upload or control writes."""
import os,json,pathlib,textwrap
from actions_canary import Store
from desktop_setup import CHANNEL,SCOPES
from provision_actions import validated_record
from credentials import GoogleCredentials
from transport import Transport,GoogleTokenForms
from github_state import GitHubState
from durable_state import DurableLedger
from adapters import checked
class State(GitHubState):
 def url(self,key):return self.base+'/contents/state-v2/'+key+'.enc'
b=State(Transport(lambda:os.environ['GH_TOKEN'],{'api.github.com'}),os.environ.pop('REELSAGA_LEDGER_KEY'))
items=[(f'dramabox-null42000029033-ep9-part{p}-private-probe',f'The Weakest Null Commands the Devil King! - Episode 9 Part {p}/3 | DramaBox')for p in (1,2,3)]
control,_=b.get('account-control');assert control=={'enabled':False}
c=GoogleCredentials(Store(validated_record(os.environ.pop('REELSAGA_GOOGLE_CREDENTIALS'))),GoogleTokenForms(),SCOPES);token=c.access_token();api=Transport(lambda:token,{'www.googleapis.com'})
identity=checked(api('GET','https://www.googleapis.com/youtube/v3/channels',params={'part':'id','mine':'true'})).data;assert {x['id']for x in identity['items']}=={CHANNEL}
s=pathlib.Path('null_part_private_probe.py').read_text();block=s[s.index('        def _dupread():'):s.index('        _da=0')]
for iid,title in items:
 record,_=b.get(DurableLedger.key(iid,'youtube'))
 matches=[]
 page=None;ids=[]
 c=checked(api('GET','https://www.googleapis.com/youtube/v3/channels',params={'part':'contentDetails','mine':'true'})).data
 playlist=c['items'][0]['contentDetails']['relatedPlaylists']['uploads']
 while True:
  q={'part':'contentDetails','playlistId':playlist,'maxResults':'50'}
  if page:q['pageToken']=page
  d=checked(api('GET','https://www.googleapis.com/youtube/v3/playlistItems',params=q)).data
  ids.extend(x['contentDetails']['videoId']for x in d.get('items',[]));page=d.get('nextPageToken')
  if not page:break
 for n in range(0,len(ids),50):
  d=checked(api('GET','https://www.googleapis.com/youtube/v3/videos',params={'part':'snippet,status,processingDetails','id':','.join(ids[n:n+50])})).data
  assert {v['id']for v in d.get('items',[])}==set(ids[n:n+50])
  for v in d['items']:
   if v['snippet']['title']==title:matches.append({'video_id':v['id'],'title':v['snippet']['title'],'description':v['snippet']['description'],'privacy':v['status']['privacyStatus'],'processing':v.get('processingDetails',{}).get('processingStatus')})
 print(json.dumps({'item_id':iid,'ledger_record':record,'control_disabled':True,'complete_channel_inventory_checked':True,'inventory_video_count':len(ids),'matches':matches,'no_mutations':True}))
