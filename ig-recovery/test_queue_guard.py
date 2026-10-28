import unittest,datetime,hashlib,copy
from queue_guard import *
from buffer_client import Inventory
class Tests(unittest.TestCase):
 def setUp(self):
  self.i={'id':'a','status':'pending','caption_sha256':hashlib.sha256(b'caption').hexdigest(),'bytes':85,'sha256':'s','cover_ms':2000};self.m={'items':[dict(self.i,id=str(n),status='public_verified_cleaned'if n==0 else 'pending')for n in range(33)]};self.c={'id':'6adb4d02778b240e2f9c6d48','organizationId':'6adb4a329ef1e740831f7879','name':'reelsaga3000'};self.now=datetime.datetime.now(datetime.timezone.utc)
 def test_order(self):self.assertEqual(next_item(self.m,{})['id'],'1')
 def test_inflight_no_skip(self):
  for s in ['started','uploading','processing','uncertain','ready_for_review','blocked']:
   with self.assertRaises(GateError):next_item(self.m,{'1':{'state':s}})
 def test_completed_advance(self):self.assertEqual(next_item(self.m,{'1':{'state':'published'}})['id'],'2')
 def test_no_blind_duplicate(self):
  with self.assertRaises(GateError):preflight(self.i,self.c,Inventory([{'text':'caption'}]),self.now,'caption')
 def test_wrong_account(self):
  with self.assertRaises(GateError):preflight(self.i,dict(self.c,name='other'),[],self.now,'caption')
 def test_recent(self):
  with self.assertRaises(GateError):preflight(self.i,self.c,Inventory([{'sentAt':self.now.isoformat(),'text':'other','status':'sent'}]),self.now,'caption')
 def test_cap(self):
  a=[{'sentAt':(self.now-datetime.timedelta(hours=2)).isoformat(),'text':'other','status':'sent'}]*40
  with self.assertRaises(GateError):preflight(self.i,self.c,Inventory(a),self.now,'caption')
 def test_saturated_inventory(self):
  with self.assertRaises(GateError):preflight(self.i,self.c,[{'text':'other'}]*100,self.now,'caption')
 def test_caption(self):
  with self.assertRaises(GateError):preflight(self.i,self.c,Inventory(),self.now,'changed')
 def test_vertical(self):
  p={'video':{'width':1080,'height':1922,'sar':'1:1','durationMs':55400},'bytes':85,'sha256':'s','audio_present':True,'decode_ok':True,'cover_nonblack':True,'pixels_reviewed':True};self.assertTrue(media(self.i,p));p['video']['height']=1080
  with self.assertRaises(GateError):media(self.i,p)
 def test_budget(self):
  u={'verified_free':True,'card_present':False,'bucket_is_separate':True,'old_bucket_acl_off':True,'class_a':1028,'class_b':2377,'inventory_bytes':330740000,'staged_count':0};self.assertTrue(budget(u,0,91088246));u['old_bucket_acl_off']=False
  with self.assertRaises(GateError):budget(u,0,91088246)
if __name__=='__main__':unittest.main()

class BufferContractTests(unittest.TestCase):
 def test_full_release_input(self):
  from buffer_client import Buffer
  class Fake(Buffer):
   def gql(self,q,v):self.q=q;self.v=v;return {'editPost':{'__typename':'PostActionSuccess','post':{'id':'existing'}}}
  b=Fake('not-a-real-key');b.release('existing','caption','https://fixture.invalid/video',2000);i=b.v['input'];self.assertEqual(i['id'],'existing');self.assertEqual(i['mode'],'shareNow');self.assertFalse(i['saveToDraft']);self.assertEqual(i['text'],'caption');self.assertTrue(i['metadata']['instagram']['isAiGenerated']);self.assertEqual(i['assets'][0]['video']['metadata']['thumbnailOffset'],2000)

class PaginationTests(unittest.TestCase):
 def test_pages(self):
  from buffer_client import Buffer,Inventory
  class Fake(Buffer):
   def gql(self,q,v):
    return {'posts':{'edges':[{'node':{'id':'1'if v['after']is None else '2'}}],'pageInfo':{'endCursor':'c','hasNextPage':v['after']is None}}}
  x=Fake('x').inventory('org','ch');self.assertTrue(x.complete);self.assertEqual([i['id']for i in x],['1','2'])
 def test_cursor_loop(self):
  from buffer_client import Buffer,Rejected
  class Fake(Buffer):
   def gql(self,q,v):return {'posts':{'edges':[],'pageInfo':{'endCursor':'c','hasNextPage':True}}}
  with self.assertRaises(Rejected):Fake('x').inventory('org','ch')
