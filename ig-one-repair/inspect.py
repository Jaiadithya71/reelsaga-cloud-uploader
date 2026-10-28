import os,json,pathlib,urllib.request
key=os.environ.pop('REELSAGA_BUFFER_API_KEY');q='''query($input:PostInput!){post(input:$input){id status channelId text sentAt dueAt externalLink metadata{... on InstagramPostMetadata{type shouldShareToFeed isAiGenerated}} assets{type thumbnail ... on VideoAsset{video{width height durationMs thumbnailOffset isVideoProcessing}}}}}'''
def g(q,v=None):
 req=urllib.request.Request('https://api.buffer.com',data=json.dumps({'query':q,'variables':v or{}}).encode(),headers={'Authorization':'Bearer '+key,'Content-Type':'application/json'})
 with urllib.request.urlopen(req,timeout=60)as r:return json.load(r)
d=g(q,{'input':{'id':'6ae1604ff652e014d7a4bf99'}});p=d.get('data',{}).get('post')or{};p['caption_exact']=p.get('text')==pathlib.Path('ig-one-repair/caption.txt').read_text();p.pop('text',None)
for a in p.get('assets',[]):a.pop('thumbnail',None)
s=g('query{__schema{mutationType{fields{name args{name type{kind name ofType{kind name}}} type{kind name ofType{kind name}}}}}}')
fields=s.get('data',{}).get('__schema',{}).get('mutationType',{}).get('fields',[]);fields=[f for f in fields if f['name']=='editPost']
pathlib.Path('inspect-receipt.json').write_text(json.dumps({'post':p,'errors':bool(d.get('errors')),'mutation_schema':fields},indent=2))
