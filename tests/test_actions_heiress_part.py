import unittest,json,tempfile,hashlib
from pathlib import Path
from actions_heiress_part import validate,run
from tests.test_durable_state import MemoryCAS
from controls import Controls
from adapters import Response
from desktop_setup import CHANNEL
class HeiressTests(unittest.TestCase):
 def setUp(self):
  self.temp=tempfile.TemporaryDirectory();self.path=Path(self.temp.name)/'test.mp4';self.path.write_bytes(b'test-fixture-only')
  self.item={'id':'heiress-ep1-part1-v1','title':'The Divorced Billionaire Heiress - Episode 1 Part 1/2 | ReelShort','description':'https://r.reelsgo.tv/rTaSSpI2PZUP\nhttps://r.reelsgo.tv/2M0nZm8Nvp0A\nFull episode part 1 of 2.\nAffiliate links: I may earn a commission if you use them.','bytes':self.path.stat().st_size,'sha256':hashlib.sha256(self.path.read_bytes()).hexdigest()}
 def tearDown(self):self.temp.cleanup()
 def test_queue_cleared(self):
  self.assertEqual(list(Path('heiress-prepared').glob('ep*')),[])
  validate(self.item,str(self.path))
 def test_daddy_rejected(self):
  with self.assertRaises(RuntimeError):validate(json.loads(Path('hybrid-test/ep4-part1.json').read_text()),'hybrid-test/ep4-part1.mp4')
 def test_bad_disclosure_hash_and_part(self):
  x=dict(self.item);p=str(self.path)
  for y in [dict(x,sha256='0'*64),dict(x,description='missing'),dict(x,id='heiress-ep3-part2-v1')]:
   with self.assertRaises(RuntimeError):validate(y,p)
 def test_private_chunks_stop_and_no_recreate(self):
  x=dict(self.item);p=str(self.path);b=MemoryCAS();Controls(b,lambda:None).set_access(True,verified=True);calls=[]
  def api(method,url,**kw):
   calls.append(method)
   if method=='POST':
    self.assertEqual(kw['json']['status']['privacyStatus'],'private');return Response(200,{}, {'Location':'https://www.googleapis.com/upload/session'})
   if method=='PUT':
    end=int(kw['headers']['Content-Range'].split('-')[1].split('/')[0])
    return Response(308,{}, {'Range':f'bytes=0-{end}'}) if end+1<x['bytes'] else Response(200,{'id':'test-heiress'}, {})
   return Response(200,{'items':[{'snippet':{'channelId':CHANNEL,'title':x['title'],'description':x['description']},'status':{'privacyStatus':'private','selfDeclaredMadeForKids':False}}]}, {})
  r=run(b,api,x,p);self.assertFalse(r['claims_verified']);self.assertFalse(r['public_publishing_enabled']);n=len(calls)
  with self.assertRaises(RuntimeError):run(b,api,x,p)
  self.assertEqual(n,len(calls))
 def test_disabled(self):
  x=dict(self.item)
  with self.assertRaises(Exception):run(MemoryCAS(),lambda *a,**k:None,x,str(self.path))
