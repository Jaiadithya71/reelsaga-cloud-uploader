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
i='dramabox-null42000029033-ep3-part3-private-probe';record,_=b.get(DurableLedger.key(i,'youtube'));control,_=b.get('account-control')
assert record is None,'Existing exact item claim; no retry'
assert control=={'enabled':False},'Disabled control not verified; hold'
c=GoogleCredentials(Store(validated_record(os.environ.pop('REELSAGA_GOOGLE_CREDENTIALS'))),GoogleTokenForms(),SCOPES);token=c.access_token();api=Transport(lambda:token,{'www.googleapis.com'})
identity=checked(api('GET','https://www.googleapis.com/youtube/v3/channels',params={'part':'id','mine':'true'})).data;assert {x['id']for x in identity['items']}=={CHANNEL}
item={'title':'The Weakest Null Commands the Devil King! - Episode 3 Part 3/3 | DramaBox'}
s=pathlib.Path('null_part_private_probe.py').read_text();block=s[s.index('        def _dupread():'):s.index('        _da=0')];exec(textwrap.dedent(block));n=_dupread()
print(json.dumps({'item_id':i,'ledger_unclaimed':True,'control_disabled':True,'complete_channel_inventory_checked':True,'inventory_video_count':n,'exact_title_absent':True,'no_mutations':True}))
