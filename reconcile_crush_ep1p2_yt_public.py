"""Reconcile Crush EP1P2 YT ledger record to published after the verified Studio public flip."""
import os,json
from actions_canary import Store
from desktop_setup import CHANNEL,SCOPES
from provision_actions import validated_record
from credentials import GoogleCredentials
from transport import Transport,GoogleTokenForms
from quarantine_state import QuarantineState
from durable_state import DurableLedger
from adapters import checked
from actions_state_probe import probe
ITEM='dramabox-crush42000028219-ep1-part2-v1';VID='akhmLTBtkiM'
record=validated_record(os.environ.pop('REELSAGA_GOOGLE_CREDENTIALS',''))
gh=os.environ.pop('GH_TOKEN','')
stable=os.environ.pop('REELSAGA_LEDGER_KEY','')
if len(stable)<48:raise RuntimeError('Stable key missing')
backend=QuarantineState(Transport(lambda:gh,{'api.github.com'}),stable);backend.initialize()
probe(backend,os.environ['GITHUB_RUN_ID']+'-reconcile')
credential=GoogleCredentials(Store(record),GoogleTokenForms(),SCOPES);token=credential.access_token()
api=Transport(lambda:token,{'www.googleapis.com'})
r=checked(api('GET','https://www.googleapis.com/youtube/v3/videos',params={'part':'snippet,status','id':VID})).data
rows=r.get('items',[])
if len(rows)!=1:raise RuntimeError('Video readback missing')
row=rows[0]
if row['snippet']['channelId']!=CHANNEL or row['status']['privacyStatus']!='public':raise RuntimeError('Public state not verified; no reconcile')
saved,_=backend.get(DurableLedger.key(ITEM,'youtube'))
if not saved or saved.get('external_id')!=VID or saved.get('state') not in ('private_locked','ready_for_review'):raise RuntimeError('Unexpected ledger state: '+json.dumps(saved))
DurableLedger(backend).checkpoint(ITEM,'youtube','published',external_id=VID)
saved,_=backend.get(DurableLedger.key(ITEM,'youtube'))
if saved.get('state')!='published' or saved.get('external_id')!=VID:raise RuntimeError('Reconcile readback failed')
print(json.dumps({'reconciled':ITEM,'platform':'youtube','state':'published','video_id':VID},sort_keys=True))
