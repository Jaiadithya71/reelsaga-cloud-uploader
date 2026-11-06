"""No implicit retries. Mutation uncertainty is durable reconciliation work."""
import json,urllib.request,urllib.error,pathlib,datetime,email.utils
class Uncertain(RuntimeError):pass
class Rejected(RuntimeError):pass
class Inventory(list):
 complete=True
class Buffer:
 def __init__(self,key):self.key=key;self._quota_blocked=False
 def gql(self,query,variables):
  # A fresh process must not silently forget the last known provider cooldown.
  cooldown=pathlib.Path(__file__).resolve().parent.parent/'buffer-api-cooldown.json'
  if cooldown.exists():
   try:
    stop=json.loads(cooldown.read_text());until=datetime.datetime.fromisoformat(stop['not_before'].replace('Z','+00:00'))
    if until.tzinfo is None:raise ValueError('Timezone missing')
   except Exception:raise Rejected('Invalid saved Buffer cooldown; no API request')from None
   if datetime.datetime.now(datetime.timezone.utc)<until:raise Rejected('Saved Buffer Retry-After active; no API request')
  path=pathlib.Path('buffer-rate-limit-receipt.json')
  if path.exists():
   try:
    events=json.loads(path.read_text())
    for event in events:
     if event.get('http_status')!=429:continue
     raw=event.get('headers',{}).get('Retry-After')
     if isinstance(raw,list):raw=raw[0]if raw else None
     at=datetime.datetime.fromisoformat(event['at'].replace('Z','+00:00'))
     if str(raw).isdigit():until=at+datetime.timedelta(seconds=int(raw))
     else:until=email.utils.parsedate_to_datetime(raw)
     if until.tzinfo is None:raise ValueError('Timezone missing')
     if datetime.datetime.now(datetime.timezone.utc)<until:raise Rejected('Saved429 receipt cooldown active; no API request')
   except Rejected:raise
   except Exception:raise Rejected('Saved Buffer quota receipt unverifiable; no API request')from None
  if self._quota_blocked:raise Rejected('Prior429 in this process; no further API requests permitted')
  req=urllib.request.Request('https://api.buffer.com',data=json.dumps({'query':query,'variables':variables}).encode(),headers={'Authorization':'Bearer '+self.key,'Content-Type':'application/json'})
  def evidence(response,body=None):
   # Never persist Authorization, cookies, response text, signed media URLs or keys.
   headers={}
   for k in ('Retry-After','RateLimit','RateLimit-Policy'):
    values=response.headers.get_all(k)if hasattr(response.headers,'get_all')else None
    if values:headers[k]=values if k!='Retry-After'else values[0]
    elif response.headers.get(k)is not None:headers[k]=response.headers.get(k)
   windows=[]
   if isinstance(body,dict):
    for error in body.get('errors',[]):
     ext=error.get('extensions',{})
     windows.append({k:ext[k] for k in ('code','window') if isinstance(ext.get(k),(str,int,float))})
   path=pathlib.Path('buffer-rate-limit-receipt.json')
   event={'at':datetime.datetime.now(datetime.timezone.utc).isoformat(),'http_status':getattr(response,'status',getattr(response,'code',None)),'headers':headers,'errors':windows}
   prior=[]
   if path.exists():
    try:prior=json.loads(path.read_text())
    except Exception:pass
   path.write_text(json.dumps((prior+[event])[-30:],indent=2))
  try:
   with urllib.request.urlopen(req,timeout=90)as r:
    d=json.load(r);evidence(r,d)
  except urllib.error.HTTPError as error:
   try:body=json.loads(error.read(65536))
   except Exception:body=None
   evidence(error,body)
   if error.code==429:
    self._quota_blocked=True
    raise Rejected('Buffer rate limited; honor recorded Retry-After, no automatic retry')from None
   raise Uncertain('Buffer HTTP '+str(error.code)+'; reconcile saved identity, no automatic retry')from None
  except Exception:raise Uncertain('No verified response; reconcile saved identity')from None
  if d.get('errors'):raise Rejected('GraphQL rejected; no retry')
  return d['data']
 def post(self,pid):
  q='query($input:PostInput!){post(input:$input){id status channelId text sentAt dueAt externalLink metadata{... on InstagramPostMetadata{type shouldShareToFeed isAiGenerated}} assets{type thumbnail ... on VideoAsset{video{width height durationMs thumbnailOffset isVideoProcessing}}}}}'
  return self.gql(q,{'input':{'id':pid}})['post']
 def inventory(self,org,ch):
  q='query($input:PostsInput!,$after:String){posts(input:$input,first:100,after:$after){edges{node{id text status sentAt dueAt externalLink}} pageInfo{endCursor hasNextPage}}}'
  rows=[];after=None;seen=set()
  for _ in range(100):
   d=self.gql(q,{'input':{'organizationId':org,'filter':{'channelIds':[ch],'status':['draft','scheduled','sending','sent']}},'after':after})['posts'];rows.extend(e['node']for e in d['edges']);pi=d['pageInfo']
   if not pi['hasNextPage']:return Inventory(rows)
   after=pi.get('endCursor')
   if not after or after in seen:raise Rejected('Pagination stalled; no writes')
   seen.add(after)
  raise Rejected('Inventory bound exhausted; no writes')
 def channel(self,ch):return self.gql('query($input:ChannelInput!){channel(input:$input){id name organizationId isDisconnected isLocked isQueuePaused}}',{'input':{'id':ch}})['channel']
 @staticmethod
 def content(caption,url,offset):return {'text':caption,'schedulingType':'automatic','assets':[{'video':{'url':url,'metadata':{'thumbnailOffset':offset}}}],'metadata':{'instagram':{'type':'reel','shouldShareToFeed':True,'isAiGenerated':True}}}
 def draft(self,ch,caption,url,offset):
  v=self.content(caption,url,offset);v.update(channelId=ch,mode='addToQueue',saveToDraft=True)
  q='mutation($input:CreatePostInput!){createPost(input:$input){__typename ... on PostActionSuccess{post{id status}} ... on MutationError{message}}}'
  return self.gql(q,{'input':v})['createPost']
 def release(self,pid,caption,url,offset):
  # Vendor requires full content despite docs claiming omitted fields preserve it.
  v=self.content(caption,url,offset);v.update(id=pid,mode='shareNow',saveToDraft=False)
  q='mutation($input:EditPostInput!){editPost(input:$input){__typename ... on PostActionSuccess{post{id status}} ... on MutationError{message}}}'
  return self.gql(q,{'input':v})['editPost']
