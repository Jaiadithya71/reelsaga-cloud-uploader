"""Strict control self-test only, with allowlisted diagnostic error labels. No video operations."""
import os,json
from transport import Transport
from quarantine_state import QuarantineState
from controls import Controls
from actions_state_probe import probe
key=os.environ.pop('REELSAGA_LEDGER_KEY','');gh=os.environ.pop('GH_TOKEN','');assert len(key)>=48
backend=QuarantineState(Transport(lambda:gh,{'api.github.com'}),key);backend.initialize();controls=Controls(backend,lambda:None)
try:print(json.dumps(probe(backend,os.environ['GITHUB_RUN_ID']+'-cake-strict'),sort_keys=True))
except Exception as e:
 msg=str(e)
 labels=['Stop control did not block access','Disabled control allowed access','Control readback did not settle; no external operations','Probe update failed','Probe readback mismatch','Control update failed; stop writes','State update uncertain; stop writes','Account access disabled']
 print('Strict probe failure: '+(msg if msg in labels else type(e).__name__),flush=True)
 raise SystemExit(1)from None
finally:controls.set_access(False)
