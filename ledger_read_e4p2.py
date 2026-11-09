"""Read-only: print the Soldier EP4P2 YT ledger record (state, external_id; no secrets)."""
import os,json
from actions_canary import Store
from provision_actions import validated_record
from transport import Transport
from quarantine_state import QuarantineState
from durable_state import DurableLedger
from actions_state_probe import probe
ITEM='dramabox-soldier42000030015-ep4-part2-v1'
gh=os.environ.pop('GH_TOKEN','')
stable=os.environ.pop('REELSAGA_LEDGER_KEY','')
if len(stable)<48:raise RuntimeError('Stable key missing')
backend=QuarantineState(Transport(lambda:gh,{'api.github.com'}),stable);backend.initialize()
probe(backend,os.environ['GITHUB_RUN_ID']+'-ledgerread')
saved,_=backend.get(DurableLedger.key(ITEM,'youtube'))
print('LEDGER_RECORD '+json.dumps(saved,sort_keys=True))
print('resume='+str(DurableLedger(backend).resume(ITEM,'youtube')))
