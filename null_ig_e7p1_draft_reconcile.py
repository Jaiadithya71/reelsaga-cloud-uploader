"""Adopt only the already-created E7P1 draft after checkpoint conflict."""
import os,json,pathlib
from github_state import GitHubState
from transport import Transport
from durable_state import DurableLedger
from buffer_client import Buffer
from queue_guard import require
class State(GitHubState):
 def url(self,k):return self.base+'/contents/state-v2/'+k+'.enc'
st=State(Transport(lambda:os.environ['GH_TOKEN'],{'api.github.com'}),os.environ['REELSAGA_LEDGER_KEY']);ledger=DurableLedger(st);buf=Buffer(os.environ['REELSAGA_BUFFER_API_KEY'])
i=next(i for i in json.loads(pathlib.Path('null-public-catalog.json').read_text())['items']if i['id']=='dramabox-null42000029033-ep7-part1-v1');pid='6ae45f38ceb12661efd8c91a';ch='6adb4d02778b240e2f9c6d48'
rows=buf.inventory('6adb4a329ef1e740831f7879',ch);matches=[x for x in rows if x['text'].strip()==i['caption'].strip()];require(len(matches)==1 and matches[0]['id']==pid and matches[0]['status']=='draft','Exact single draft not confirmed')
p=buf.post(pid);require(p['status']=='draft'and p['channelId']==ch and p['text']==i['caption']and not p.get('externalLink'),'Draft identity differs');require(p['metadata']=={'type':'reel','shouldShareToFeed':True,'isAiGenerated':True},'Draft metadata differs')
h,_=st.get('host-'+i['id']);require(h and h['state']=='verified_original'and h['bytes']==i['bytes'],'Verified original host differs')
ledger.verify_item(i,'instagram');k=ledger.key(i['id'],'instagram');r,rv=st.get(k);require(r and r['state']=='uncertain'and r['session']=='buffer_create_draft'and not r.get('external_id'),'Exact unresolved draft checkpoint differs')
r.update(state='ready_for_review',external_id=pid,session='draft_created');require(st.compare_and_swap(k,rv,r),'Reconciliation CAS conflict; no release');rr,_=st.get(k);require(rr==r,'Reconciliation readback differs')
pathlib.Path('draft-reconcile.json').write_text(json.dumps({'item':i['id'],'post_id':pid,'status':'existing_exact_draft_adopted','no_post_created_or_released':True},indent=2));print('Existing exact draft adopted; normal release gates next')
