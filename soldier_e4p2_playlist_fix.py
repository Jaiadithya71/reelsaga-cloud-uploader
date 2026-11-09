"""Diagnose+recover Soldier EP4P2 YT playlist add: print sanitized API error reasons, retry with backoff, verify membership. Ledger untouched."""
import os,json,time
from actions_canary import Store
from desktop_setup import CHANNEL,SCOPES
from provision_actions import validated_record
from credentials import GoogleCredentials
from transport import Transport,GoogleTokenForms
from quarantine_state import QuarantineState
from durable_state import DurableLedger
from controls import Controls,ControlError
from adapters import checked
from actions_state_probe import probe
ITEM='dramabox-soldier42000030015-ep4-part2-v1';VID='45e9Iihtigs';PL='PLD5vEa-35ZMU'
record=validated_record(os.environ.pop('REELSAGA_GOOGLE_CREDENTIALS',''))
gh=os.environ.pop('GH_TOKEN','')
stable=os.environ.pop('REELSAGA_LEDGER_KEY','')
if len(stable)<48:raise RuntimeError('Stable key missing')
backend=QuarantineState(Transport(lambda:gh,{'api.github.com'}),stable);backend.initialize()
probe(backend,os.environ['GITHUB_RUN_ID']+'-playlistfix')
saved,_=backend.get(DurableLedger.key(ITEM,'youtube'))
if not saved or saved.get('external_id')!=VID or saved.get('state')!='private_locked':raise RuntimeError('Unexpected ledger state')
controls=Controls(backend,lambda:None)
credential=GoogleCredentials(Store(record),GoogleTokenForms(),SCOPES);token=credential.access_token()
api=Transport(lambda:token,{'www.googleapis.com'})
r=checked(api('GET','https://www.googleapis.com/youtube/v3/videos',params={'part':'snippet,status,processingDetails','id':VID})).data
row=r['items'][0]
if row['snippet']['channelId']!=CHANNEL:raise RuntimeError('Channel mismatch')
print(json.dumps({'privacy':row['status'].get('privacyStatus'),'processing':row.get('processingDetails',{}).get('processingStatus'),'uploadStatus':row['status'].get('uploadStatus')}))
m=checked(api('GET','https://www.googleapis.com/youtube/v3/playlistItems',params={'part':'snippet','playlistId':PL,'videoId':VID})).data
if m.get('items'):
    print(json.dumps({'playlist_add':'already_member'}));raise SystemExit(0)
controls.set_access(True,verified=True)
try:
    last=None
    for attempt in range(5):
        resp=api('POST','https://www.googleapis.com/youtube/v3/playlistItems',params={'part':'snippet'},json={'snippet':{'playlistId':PL,'resourceId':{'kind':'youtube#video','videoId':VID}}})
        if resp.status in (200,201):
            last=None;break
        e=resp.data.get('error',{}) if isinstance(resp.data,dict) else {}
        reasons=[x.get('reason') for x in e.get('errors',[])][:3]
        print(json.dumps({'attempt':attempt+1,'http':resp.status,'reasons':reasons}))
        last=(resp.status,reasons)
        if attempt<4:time.sleep(60)
    if last:
        print(json.dumps({'playlist_add':'failed','last_http':last[0],'last_reasons':last[1]}));raise SystemExit(1)
finally:
    controls.set_access(False)
m=checked(api('GET','https://www.googleapis.com/youtube/v3/playlistItems',params={'part':'snippet','playlistId':PL,'videoId':VID})).data
ok=bool(m.get('items'))
print(json.dumps({'playlist_add':'ok' if ok else 'unverified','member_verified':ok}))
raise SystemExit(0 if ok else 1)
