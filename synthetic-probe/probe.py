"""One-shot synthetic-only Buffer draft probe. Never schedule or publish.
Input: mode0600 manifest JSON at PROBE_MANIFEST with asset_url, sha256, bytes,
width,height,duration_ms,marker,created_at. Secret from REELSAGA_BUFFER_API_KEY.
Never print API responses, exceptions, URLs or credentials. Receipt has no URLs.
Caller must persist receipt before any retry and reconcile existing marker.
"""
import os,json,urllib.request,urllib.error,hashlib,datetime,pathlib,sys,time
ENDPOINT='https://api.buffer.com'
CHANNEL='6adb4d02778b240e2f9c6d48';ORG='6adb4a329ef1e740831f7879'
receipt={'version':1,'status':'not_started','fetch_proven':False}
out=pathlib.Path('probe-receipt.json')
def save():out.write_text(json.dumps(receipt,indent=2));os.chmod(out,0o600)
def fail(code):receipt['status']=code;save();print('PROBE_RESULT',code);sys.exit(1)
def gql(query,variables):
 req=urllib.request.Request(ENDPOINT,data=json.dumps({'query':query,'variables':variables}).encode(),headers={'Authorization':'Bearer '+token,'Content-Type':'application/json'})
 try:
  with urllib.request.urlopen(req,timeout=60)as r: d=json.load(r)
 except Exception:fail('buffer_request_failed_reconcile_before_retry')
 if d.get('errors'):fail('buffer_graphql_error_reconcile_before_retry')
 return d.get('data')or{}
def download(url):
 try:
  with urllib.request.urlopen(urllib.request.Request(url,headers={'User-Agent':'ReelSagaSyntheticProbe/1'}),timeout=60)as r:
   b=r.read(10000001)
   if len(b)>10000000:fail('synthetic_too_large')
   return b,r.headers.get('Content-Type','')
 except Exception:fail('asset_fetch_failed')
try:
 m=json.loads(pathlib.Path(os.environ['PROBE_MANIFEST']).read_text());token=os.environ.pop('REELSAGA_BUFFER_API_KEY');url=m['asset_url']
 assert token and url.startswith('https://') and m['marker'].startswith('REELSAGA_SYNTHETIC_DRAFT_')
 assert all(k in m for k in ['sha256','bytes','width','height','duration_ms','created_at'])
 assert 0<m['bytes']<10000000 and m['width']>0 and m['height']>0
 age=(datetime.datetime.now(datetime.timezone.utc)-datetime.datetime.fromisoformat(m['created_at'].replace('Z','+00:00'))).total_seconds();assert 0<=age<=3600
except Exception:fail('invalid_or_stale_manifest')
# Runner mask command is consumed by GitHub, not retained as an unmasked log line.
print('::add-mask::'+url,flush=True)
b,mime=download(url)
if len(b)!=m['bytes']or hashlib.sha256(b).hexdigest()!=m['sha256']:fail('fixture_hash_mismatch')
receipt.update({'marker':m['marker'],'fixture_sha256':m['sha256'],'fixture_bytes':len(b),'fixture_width':m['width'],'fixture_height':m['height']});save()
recent=gql('query($input:PostsInput!){posts(input:$input,first:100){edges{node{id text status}}}}',{'input':{'organizationId':ORG,'filter':{'channelIds':[CHANNEL],'status':['draft','scheduled','sending','sent']}}})
for e in recent.get('posts',{}).get('edges',[]):
 if e['node'].get('text')==m['marker']:
  receipt['post_id']=e['node']['id'];fail('existing_marker_reconcile_no_create')
# No dimensions/size supplied: server media readback must be independently derived.
input_={'text':m['marker'],'channelId':CHANNEL,'schedulingType':'automatic','mode':'addToQueue','saveToDraft':True,'metadata':{'instagram':{'type':'reel','shouldShareToFeed':False}},'assets':[{'video':{'url':url,'metadata':{'thumbnailOffset':1000}}}]}
assert input_['saveToDraft']is True and input_['mode']=='addToQueue' and 'dueAt'not in input_
receipt['status']='create_in_flight';save()
r=gql('mutation($input:CreatePostInput!){createPost(input:$input){__typename ... on PostActionSuccess{post{id status}} ... on MutationError{message}}}',{'input':input_}).get('createPost',{})
if not r.get('post'):fail('draft_rejected_no_receipt')
pid=r['post']['id'];receipt.update({'post_id':pid,'status':'draft_created_readback_pending'});save()
for i in range(3):
 if i:time.sleep(20)
 p=gql('query($input:PostInput!){post(input:$input){id status sentAt dueAt externalLink assets{type source mimeType thumbnail ... on VideoAsset{video{width height durationMs fileSize videoCodec audioCodec containerFormat isVideoProcessing isTranscodingRequired}}}}}',{'input':{'id':pid}}).get('post',{})
 if p.get('status')!='draft'or p.get('sentAt')or p.get('dueAt')or p.get('externalLink'):fail('unexpected_non_draft_state_stop')
 assets=p.get('assets')or[]
 receipt['draft_status']='draft';receipt['server_video_metadata']=[a.get('video')for a in assets if a.get('video')];save()
 if len(assets)!=1:continue
 a=assets[0];v=a.get('video')or{}
 metadata_matches=v.get('width')==m['width']and v.get('height')==m['height']and abs(v.get('durationMs',0)-m['duration_ms'])<=1000
 receipt['server_metadata_matches']=metadata_matches
 source=a.get('source')or''
 receipt['source_rewritten']=bool(source and source!=url)
 # Strong byte proof only if Buffer exposes a different hosted source and bytes match.
 if metadata_matches and source and source!=url and source.startswith('https://'):
  print('::add-mask::'+source,flush=True)
  got,_=download(source);receipt['buffer_media_bytes']=len(got);receipt['buffer_media_sha256']=hashlib.sha256(got).hexdigest();receipt['fetch_proven']=receipt['buffer_media_sha256']==m['sha256'];save()
 if not v.get('isVideoProcessing'):break
receipt['status']='draft_verified_fetch_proven'if receipt['fetch_proven']else'draft_verified_fetch_not_proven';save();print('PROBE_RESULT',receipt['status'])
# Assigned test cleanup only, ID created in this run and verified draft.
delr=gql('mutation($input:DeletePostInput!){deletePost(input:$input){__typename ... on DeletePostSuccess{id} ... on VoidMutationError{message}}}',{'input':{'id':pid}}).get('deletePost',{})
receipt['cleanup_deleted_id']=delr.get('id');receipt['cleanup_success']=delr.get('id')==pid;save();print('CLEANUP',receipt['cleanup_success'])
