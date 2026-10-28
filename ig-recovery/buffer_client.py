"""No implicit retries. Mutation uncertainty is durable reconciliation work."""
import json,urllib.request,urllib.error
class Uncertain(RuntimeError):pass
class Rejected(RuntimeError):pass
class Inventory(list):
 complete=True
class Buffer:
 def __init__(self,key):self.key=key
 def gql(self,query,variables):
  req=urllib.request.Request('https://api.buffer.com',data=json.dumps({'query':query,'variables':variables}).encode(),headers={'Authorization':'Bearer '+self.key,'Content-Type':'application/json'})
  try:
   with urllib.request.urlopen(req,timeout=90)as r:d=json.load(r)
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
