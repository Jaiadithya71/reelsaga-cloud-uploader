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
items=[('dramabox-null42000029033-ep7-part1-private-probe-cut4496-v2','The Weakest Null Commands the Devil King! - Episode 7 Part 1/3 | DramaBox'),('dramabox-null42000029033-ep7-part2-private-probe','The Weakest Null Commands the Devil King! - Episode 7 Part 2/3 | DramaBox')]
control,_=b.get('account-control');assert control=={'enabled':False}
c=GoogleCredentials(Store(validated_record(os.environ.pop('REELSAGA_GOOGLE_CREDENTIALS'))),GoogleTokenForms(),SCOPES);token=c.access_token();api=Transport(lambda:token,{'www.googleapis.com'})
identity=checked(api('GET','https://www.googleapis.com/youtube/v3/channels',params={'part':'id','mine':'true'})).data;assert {x['id']for x in identity['items']}=={CHANNEL}
s=pathlib.Path('null_part_private_probe.py').read_text();block=s[s.index('        def _dupread():'):s.index('        _da=0')]
for iid,title in items:
 record,_=b.get(DurableLedger.key(iid,'youtube'));assert record is None,'Exact claim exists; hold'
 item={'id':iid,'title':title};exec(textwrap.dedent(block));n=_dupread()
 print(json.dumps({'item_id':iid,'ledger_unclaimed':True,'control_disabled':True,'complete_channel_inventory_checked':True,'inventory_video_count':n,'no_unexpected_exact_title':True,'allowed_retained_private_id':'9zqazaUJ25I'if 'cut4496' in iid else None,'no_mutations':True}))
